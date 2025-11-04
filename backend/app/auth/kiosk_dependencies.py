# kiosk_dependencies.py
# FastAPI dependencies for kiosk authentication and route protection
# Provides dependency injection for kiosk-specific authentication requirements

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..database.connection import get_db
from ..database.models import User
from ..models.auth import TokenData
from .kiosk_auth_service import kiosk_auth_service


# HTTP Bearer token scheme for kiosk authentication
# auto_error=False to handle missing token manually and return 401 instead of 403
kiosk_security = HTTPBearer(scheme_name="KioskBearer", auto_error=False)


async def get_kiosk_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(kiosk_security)
) -> str:
    """
    Extract kiosk JWT token from Authorization header
    
    Args:
        credentials: HTTP authorization credentials from header
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing kiosk authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def get_current_kiosk_token_data(
    token: str = Depends(get_kiosk_token_from_header)
) -> TokenData:
    """
    Verify kiosk JWT token and extract token data
    
    Args:
        token: JWT token string from authorization header
        
    Returns:
        TokenData object with decoded kiosk token information
        
    Raises:
        HTTPException: If token is invalid, expired, or not for kiosk user
    """
    return kiosk_auth_service.verify_kiosk_token(token)


async def get_current_kiosk_user(
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_kiosk_token_data)
) -> User:
    """
    Get current authenticated kiosk user from database
    
    Args:
        db: Database session
        token_data: Decoded token data from JWT
        
    Returns:
        User object for authenticated kiosk user
        
    Raises:
        HTTPException: If user not found or not active kiosk user
    """
    user = kiosk_auth_service.get_kiosk_user_by_id(db, token_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiosk user not found or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiosk user account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_kiosk_username(
    token_data: TokenData = Depends(get_current_kiosk_token_data)
) -> str:
    """
    Get current kiosk username from token (for POS routing and identification)
    
    Args:
        token_data: Decoded token data from JWT
        
    Returns:
        Kiosk username string (e.g., "kiosk_store_01")
    """
    return token_data.username


async def get_current_kiosk_device_id(
    token_data: TokenData = Depends(get_current_kiosk_token_data)
) -> Optional[str]:
    """
    Get current kiosk device ID from token (for future device tracking)
    
    Args:
        token_data: Decoded token data from JWT
        
    Returns:
        Device ID string if present in token, None otherwise
    """
    return getattr(token_data, 'device_id', None)


async def get_kiosk_context_for_payments(
    username: str = Depends(get_current_kiosk_username),
    device_id: Optional[str] = Depends(get_current_kiosk_device_id),
    user: User = Depends(get_current_kiosk_user)
) -> dict:
    """
    Get complete kiosk context for payment processing and POS terminal routing
    
    Args:
        username: Kiosk username for POS routing
        device_id: Optional device identifier
        user: Full kiosk user object
        
    Returns:
        Dictionary containing kiosk context for payment integration
    """
    return {
        "kiosk_username": username,
        "kiosk_user_id": user.user_id,
        "device_id": device_id,
        "is_active": user.is_active,
        "role": user.role_name
    }


# Dependency for validating kiosk refresh tokens
async def verify_kiosk_refresh_token(
    token: str = Depends(get_kiosk_token_from_header)
) -> TokenData:
    """
    Verify kiosk refresh token specifically
    
    Args:
        token: JWT refresh token string
        
    Returns:
        TokenData object with decoded refresh token information
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    return kiosk_auth_service.verify_kiosk_refresh_token(token)