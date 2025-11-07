"""
Slack integration for alert notifications.
"""
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class SlackClient:
    """Client for Slack API operations."""
    
    def __init__(self, bot_token: str | None = None) -> None:
        """
        Initialize Slack client.
        
        Args:
            bot_token: Slack bot token (defaults to settings)
        """
        token = bot_token or settings.slack_bot_token
        if not token:
            raise ValueError("Slack bot token not configured")
        
        self.client = AsyncWebClient(token=token)
    
    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """
        Post a message to a Slack channel.
        
        Args:
            channel: Channel ID or name
            text: Plain text message (fallback)
            blocks: Rich message blocks
            thread_ts: Thread timestamp for replies
        
        Returns:
            Message response
        """
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
            )
            return response.data
        except SlackApiError as e:
            logger.error(f"Failed to post Slack message: {e.response['error']}")
            raise ValueError(f"Slack API error: {e.response['error']}")
    
    async def send_alert(
        self,
        channel: str,
        alert_title: str,
        alert_message: str,
        severity: str = "warning",
        fields: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Send a formatted alert message.
        
        Args:
            channel: Channel ID or name
            alert_title: Alert title
            alert_message: Alert description
            severity: Alert severity (info|warning|error)
            fields: Additional fields to display
        
        Returns:
            Message response
        """
        # Color coding
        color_map = {
            "info": "#36a64f",      # Green
            "warning": "#ff9900",   # Orange
            "error": "#ff0000",     # Red
        }
        color = color_map.get(severity, "#808080")
        
        # Build attachment fields
        attachment_fields = []
        if fields:
            for key, value in fields.items():
                attachment_fields.append({
                    "title": key,
                    "value": value,
                    "short": True,
                })
        
        # Build blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {alert_title}",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert_message,
                }
            },
        ]
        
        # Add fields if present
        if attachment_fields:
            fields_text = "\n".join([
                f"*{field['title']}:* {field['value']}"
                for field in attachment_fields
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": fields_text,
                }
            })
        
        # Add context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Severity: *{severity.upper()}* | Aurix Financial Intelligence",
                }
            ]
        })
        
        return await self.post_message(
            channel=channel,
            text=f"{alert_title}: {alert_message}",  # Fallback text
            blocks=blocks,
        )


async def send_alert_notification(
    channel: str,
    alert_name: str,
    metric: str,
    current_value: float | str,
    threshold: float | str,
    message: str | None = None,
) -> bool:
    """
    Convenience function to send alert notifications.
    
    Args:
        channel: Slack channel ID
        alert_name: Name of the alert
        metric: Metric that triggered alert
        current_value: Current value of the metric
        threshold: Threshold that was crossed
        message: Optional additional message
    
    Returns:
        True if sent successfully
    """
    try:
        client = SlackClient()
        
        alert_message = message or f"Alert `{alert_name}` has been triggered."
        
        await client.send_alert(
            channel=channel,
            alert_title=alert_name,
            alert_message=alert_message,
            severity="warning",
            fields={
                "Metric": metric,
                "Current Value": str(current_value),
                "Threshold": str(threshold),
            },
        )
        
        logger.info(f"Sent Slack alert to {channel}: {alert_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False
