"""
API dependencies and utilities.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import verify_supabase_jwt
from ..db.session import get_session
from ..db.models import User, Tenant
from ..core.logging import get_logger

logger = get_logger(__name__)


async def get_current_user(
    authorization: Annotated[str, Header()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header (Bearer token)
        session: Database session
    
    Returns:
        Authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise credentials_exception
        
        token = authorization.split(" ")[1]
        
        # Verify JWT
        payload = verify_supabase_jwt(token)
        auth_provider_id: str = payload.get("sub")
        
        if not auth_provider_id:
            raise credentials_exception
        
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise credentials_exception
    
    # Get user from database
    stmt = select(User).where(User.auth_provider_id == auth_provider_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise credentials_exception
    
    return user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Tenant:
    """
    Get tenant for current user.
    
    Args:
        current_user: Authenticated user
        session: Database session
    
    Returns:
        User's tenant
    
    Raises:
        HTTPException: If tenant not found
    """
    stmt = select(Tenant).where(Tenant.id == current_user.tenant_id)
    result = await session.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    if tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is {tenant.status}",
        )
    
    return tenant


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
