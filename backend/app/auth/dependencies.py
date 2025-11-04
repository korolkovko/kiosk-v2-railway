# dependencies.py
# FastAPI dependencies for authentication and authorization

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..database.models import User
from .auth_service import auth_service

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token (excludes kiosk users)
    
    Args:
        credentials: HTTP authorization credentials containing JWT token
        db: Database session
        
    Returns:
        Current authenticated user (non-kiosk users only)
        
    Raises:
        HTTPException: If token is invalid, user not found, or user is kiosk
        
    Note:
        Kiosk users are excluded from standard authentication and must use dedicated kiosk endpoints
    """
    # Verify JWT token (already excludes kiosk tokens)
    token_data = auth_service.verify_token(credentials.credentials)
    
    # Get user from database
    user = auth_service.get_user_by_id(db, user_id=token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Double-check: exclude kiosk users from standard authentication
    if user.role_name == "kiosk":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_superadmin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to ensure current user is a SuperAdmin
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current user if they are SuperAdmin
        
    Raises:
        HTTPException: If user is not SuperAdmin
    """
    if not auth_service.is_superadmin(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin access required"
        )
    
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to ensure current user is an Admin (includes SuperAdmin)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current user if they are Admin or SuperAdmin
        
    Raises:
        HTTPException: If user is not Admin or SuperAdmin
    """
    if not auth_service.is_admin(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get current user (allows anonymous access)
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user if authenticated, None if anonymous
    """
    if not credentials:
        return None
    
    try:
        # Try to verify token and get user
        token_data = auth_service.verify_token(credentials.credentials)
        user = auth_service.get_user_by_id(db, user_id=token_data.user_id)
        
        # Return user only if found and active
        if user and user.is_active:
            return user
        
    except HTTPException:
        # Invalid token, but we allow anonymous access
        pass
    
    return None