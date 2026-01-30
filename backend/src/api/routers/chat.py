"""
AI Chat API router.
Provides conversational AI interface for financial queries.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.ai import get_openai_client
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI assistant and get a response.
    
    This endpoint uses GPT-4 to provide intelligent responses about
    financial data, analysis, and general financial advice.
    """
    try:
        client = get_openai_client()
        
        # Create a chat completion with context about Aurix
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful AI financial assistant for Aurix, a financial intelligence platform.
                    You help users understand their finances, analyze data, and provide insights.
                    Be concise, helpful, and professional. When users ask about their data, 
                    acknowledge that you'll need access to their specific financial data to provide accurate analysis.
                    Provide general financial advice and guidance when appropriate."""
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(response=ai_response)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat message. Please try again."
        )
