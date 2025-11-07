"""
API dependencies and utilities - DEMO MODE (Auth Bypassed)
"""
from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import verify_supabase_jwt
from ..db.session import get_session
from ..db.models import User, Tenant
from ..core.logging import get_logger

logger = get_logger(__name__)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get current authenticated user - DEMO MODE: Returns mock user.
    
    Args:
        authorization: Authorization header (optional for demo)
        session: Database session
    
    Returns:
        Mock demo user
    """
    # DEMO MODE: Return a mock user without authentication
    logger.info("DEMO MODE: Bypassing authentication, returning mock user")
    
    # Create a mock user for demo purposes
    mock_user = User(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        auth_provider_id="demo_user",
        email="demo@aurix.com",
        full_name="Demo User",
        role="admin",
        is_active=True,
    )
    
    return mock_user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Tenant:
    """
    Get tenant for current user - DEMO MODE: Returns mock tenant.
    
    Args:
        current_user: Authenticated user
        session: Database session
    
    Returns:
        Mock demo tenant
    """
    # DEMO MODE: Return a mock tenant
    logger.info("DEMO MODE: Bypassing tenant lookup, returning mock tenant")
    
    mock_tenant = Tenant(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Demo Company",
        slug="demo-company",
        status="active",
        plan="professional",
        max_ai_calls_per_month=10000,
        ai_calls_this_month=0,
    )
    
    return mock_tenant


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.
    
    Args:
        required_role: Required role (admin|member|viewer)
    
    Returns:
        Dependency function
    """
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        role_hierarchy = {"viewer": 0, "member": 1, "admin": 2}
        
        user_level = role_hierarchy.get(current_user.role, -1)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        
        return current_user
    
    return role_checker


async def check_ai_quota(tenant: Annotated[Tenant, Depends(get_current_tenant)]) -> Tenant:
    """
    Check if tenant has remaining AI quota.
    
    Args:
        tenant: Current tenant
    
    Returns:
        Tenant if quota available
    
    Raises:
        HTTPException: If quota exceeded
    """
    if tenant.ai_calls_this_month >= tenant.max_ai_calls_per_month:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI call quota exceeded for this month. Please upgrade your plan.",
        )
    
    return tenant
