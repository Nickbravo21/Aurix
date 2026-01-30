"""
Background task for data ingestion from connected sources.
"""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select

from ..celery_app import celery_app
from ...db.session import get_session_context
from ...db.models import DataSource, OAuthToken, Transaction
from ...integrations import GoogleSheetsClient
from ...etl.normalize import enrich_transaction, detect_duplicates
from ...core.security import token_encryption
from ...core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="aurix.ingest_datasource")
async def ingest_datasource(datasource_id: str, days_back: int = 30) -> dict:
    """
    Ingest data from a datasource.
    
    Args:
        datasource_id: UUID of datasource
        days_back: How many days of data to fetch
    
    Returns:
        Dict with ingestion results
    """
    datasource_uuid = UUID(datasource_id)
    
    async with get_session_context() as session:
        # Get datasource
        stmt = select(DataSource).where(DataSource.id == datasource_uuid)
        result = await session.execute(stmt)
        datasource = result.scalar_one_or_none()
        
        if not datasource:
            raise ValueError(f"DataSource {datasource_id} not found")
        
        # Get OAuth token
        token_stmt = select(OAuthToken).where(OAuthToken.data_source_id == datasource_uuid)
        token_result = await session.execute(token_stmt)
        oauth_token = token_result.scalar_one_or_none()
        
        if not oauth_token:
            raise ValueError(f"OAuth token not found for datasource {datasource_id}")
        
        # Decrypt tokens
        access_token = token_encryption.decrypt(oauth_token.access_token)
        refresh_token = token_encryption.decrypt(oauth_token.refresh_token) if oauth_token.refresh_token else None
        
        # Fetch transactions based on source type
        start_date = date.today() - timedelta(days=days_back)
        end_date = date.today()
        
        try:
            if datasource.kind == "google_sheets":
                client = GoogleSheetsClient(access_token, refresh_token)
                spreadsheet_id = datasource.config.get("spreadsheet_id")
                raw_transactions = await client.extract_transactions(spreadsheet_id)
            else:
                raise ValueError(f"Unsupported datasource kind: {datasource.kind}. Only google_sheets is supported.")
            
            # Deduplicate
            unique_transactions = detect_duplicates(raw_transactions)
            
            # Enrich and save
            saved_count = 0
            for txn in unique_transactions:
                try:
                    enriched = enrich_transaction(
                        txn,
                        datasource.tenant_id,
                        datasource.id,
                    )
                    
                    # Check if transaction already exists
                    check_stmt = select(Transaction).where(
                        Transaction.tenant_id == datasource.tenant_id,
                        Transaction.external_id == enriched["external_id"],
                    )
                    check_result = await session.execute(check_stmt)
                    existing = check_result.scalar_one_or_none()
                    
                    if not existing:
                        transaction = Transaction(**enriched)
                        session.add(transaction)
                        saved_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to save transaction: {e}")
                    continue
            
            await session.commit()
            
            # Update datasource sync status
            datasource.last_sync_at = date.today()
            datasource.last_sync_status = "success"
            datasource.sync_count += 1
            session.add(datasource)
            await session.commit()
            
            logger.info(
                f"Ingested {saved_count} new transactions from {datasource.kind} "
                f"datasource {datasource_id}"
            )
            
            return {
                "datasource_id": datasource_id,
                "status": "success",
                "transactions_fetched": len(raw_transactions),
                "transactions_saved": saved_count,
            }
            
        except Exception as e:
            # Update error status
            datasource.last_sync_status = "error"
            datasource.last_sync_error = str(e)
            session.add(datasource)
            await session.commit()
            
            logger.error(f"Ingestion failed for {datasource_id}: {e}")
            raise


@celery_app.task(name="aurix.ingest_all_tenant_sources")
async def ingest_all_tenant_sources(tenant_id: str) -> dict:
    """
    Ingest data from all active datasources for a tenant.
    
    Args:
        tenant_id: UUID of tenant
    
    Returns:
        Dict with results for each datasource
    """
    tenant_uuid = UUID(tenant_id)
    
    async with get_session_context() as session:
        # Get all active datasources
        stmt = (
            select(DataSource)
            .where(DataSource.tenant_id == tenant_uuid)
            .where(DataSource.status == "active")
        )
        result = await session.execute(stmt)
        datasources = result.scalars().all()
        
        results = {}
        for ds in datasources:
            try:
                result = await ingest_datasource(str(ds.id))
                results[str(ds.id)] = result
            except Exception as e:
                results[str(ds.id)] = {"status": "error", "error": str(e)}
        
        return {
            "tenant_id": tenant_id,
            "datasources_processed": len(results),
            "results": results,
        }
