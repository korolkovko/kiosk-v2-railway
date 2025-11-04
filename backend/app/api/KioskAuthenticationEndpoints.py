# KioskAuthenticationEndpoints.py
# FastAPI endpoints for kiosk authentication with extended JWT tokens
# Provides dedicated API routes for self-service kiosk authentication

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database.connection import get_db
from ..database.models import User
from ..models.kiosk_auth_models import (
    KioskLoginRequest,
    KioskLoginResponse,
    KioskRefreshRequest,
    KioskRefreshResponse,
    KioskLogoutResponse,
    KioskSessionValidationResponse
)
from ..logic.kiosk_auth_logic import kiosk_auth_logic
from ..auth.kiosk_dependencies import (
    get_current_kiosk_user,
    get_current_kiosk_token_data,
    get_current_kiosk_username,
    get_current_kiosk_device_id,
    get_kiosk_context_for_payments,
    verify_kiosk_refresh_token
)


router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Authentication"]
)


@router.post("/login", response_model=KioskLoginResponse, status_code=status.HTTP_200_OK)
async def kiosk_login(
    login_request: KioskLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate kiosk user and return long-lived JWT tokens
    
    This endpoint provides extended JWT tokens (30 days access, 90 days refresh)
    specifically designed for self-service kiosks that need to stay logged in
    for extended periods without user intervention.
    
    Args:
        login_request: Kiosk credentials and optional device identifier
        db: Database session
        
    Returns:
        KioskLoginResponse with access token, refresh token, and user info
        
    Raises:
        HTTPException: If credentials are invalid or user is not a kiosk
    """
    return await kiosk_auth_logic.kiosk_login(db, login_request)


@router.post("/refresh", response_model=KioskRefreshResponse, status_code=status.HTTP_200_OK)
async def kiosk_refresh_token(
    refresh_request: KioskRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh kiosk access token using refresh token
    
    Generates new access and refresh token pair for continued kiosk operation.
    Updates device telemetry if device_id is provided.
    
    Args:
        refresh_request: Refresh token and optional device identifier
        db: Database session
        
    Returns:
        KioskRefreshResponse with new token pair and user info
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    return await kiosk_auth_logic.kiosk_refresh_token(db, refresh_request)


@router.post("/logout", response_model=KioskLogoutResponse, status_code=status.HTTP_200_OK)
async def kiosk_logout(
    current_user: User = Depends(get_current_kiosk_user),
    device_id: str = Depends(get_current_kiosk_device_id)
):
    """
    Logout kiosk user (stateless confirmation)
    
    In the stateless JWT approach, logout is primarily a client-side operation.
    This endpoint provides confirmation and could be extended to add tokens
    to a deny-list in the future.
    
    Args:
        current_user: Current authenticated kiosk user
        device_id: Device identifier from token
        
    Returns:
        KioskLogoutResponse with logout confirmation
    """
    return await kiosk_auth_logic.kiosk_logout(current_user, device_id)


@router.get("/session/validate", response_model=KioskSessionValidationResponse, status_code=status.HTTP_200_OK)
async def validate_kiosk_session(
    current_user: User = Depends(get_current_kiosk_user),
    token_data = Depends(get_current_kiosk_token_data),
    device_id: str = Depends(get_current_kiosk_device_id)
):
    """
    Validate current kiosk session and return session information
    
    Useful for checking session validity and getting kiosk context information
    for payment processing and POS terminal routing.
    
    Args:
        current_user: Current authenticated kiosk user
        token_data: Decoded token data
        device_id: Device identifier from token
        
    Returns:
        KioskSessionValidationResponse with session validation info
    """
    return await kiosk_auth_logic.validate_kiosk_session(current_user, token_data, device_id)


@router.get("/context/payment", status_code=status.HTTP_200_OK)
async def get_kiosk_payment_context(
    payment_context: Dict[str, Any] = Depends(get_kiosk_context_for_payments)
):
    """
    Get kiosk context for payment processing and POS terminal routing
    
    Provides all necessary kiosk identification information for payment
    integration, including username for POS terminal routing.
    
    Args:
        payment_context: Kiosk context from dependency injection
        
    Returns:
        Dictionary with kiosk context for payment processing
    """
    return {
        "success": True,
        "kiosk_context": payment_context,
        "message": "Kiosk payment context retrieved successfully"
    }


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_kiosk_status(
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username),
    device_id: str = Depends(get_current_kiosk_device_id)
):
    """
    Get current kiosk status and basic information
    
    Provides basic kiosk status information for monitoring and debugging.
    
    Args:
        current_user: Current authenticated kiosk user
        kiosk_username: Kiosk username from token
        device_id: Device identifier from token
        
    Returns:
        Dictionary with kiosk status information
    """
    return {
        "kiosk_username": kiosk_username,
        "user_id": current_user.user_id,
        "device_id": device_id,
        "is_active": current_user.is_active,
        "role": current_user.role_name,
        "last_login_at": current_user.last_login_at,
        "status": "authenticated",
        "token_type": "stateless_jwt"
    }


# Health check endpoint for kiosk authentication service
@router.get("/health", status_code=status.HTTP_200_OK)
async def kiosk_auth_health_check():
    """
    Health check endpoint for kiosk authentication service
    
    Returns:
        Dictionary with service health status
    """
    return {
        "service": "kiosk_authentication",
        "status": "healthy",
        "version": "1.0.0",
        "token_type": "stateless_jwt",
        "features": {
            "extended_tokens": True,
            "device_tracking": True,
            "payment_context": True,
            "deny_list_ready": False
        }
    }


# Future extensibility endpoints

@router.get("/analytics/basic", status_code=status.HTTP_200_OK)
async def get_kiosk_basic_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user)
):
    """
    Get basic analytics for current kiosk (future extensibility)
    
    Args:
        db: Database session
        current_user: Current authenticated kiosk user
        
    Returns:
        Dictionary with basic kiosk analytics
    """
    analytics = await kiosk_auth_logic.get_kiosk_session_analytics(
        db, current_user.username
    )
    
    return {
        "success": True,
        "analytics": analytics,
        "message": "Basic kiosk analytics retrieved"
    }


@router.post("/token/prepare-deny-list", status_code=status.HTTP_200_OK)
async def prepare_token_for_deny_list(
    token_data = Depends(get_current_kiosk_token_data)
):
    """
    Prepare token for future deny-list functionality (placeholder)
    
    Args:
        token_data: Current token data
        
    Returns:
        Dictionary with deny-list preparation status
    """
    jti = getattr(token_data, 'jti', None)
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain JTI for deny-list functionality"
        )
    
    result = await kiosk_auth_logic.prepare_for_token_deny_list_support(jti)
    
    return {
        "success": True,
        "deny_list_preparation": result,
        "message": "Token prepared for future deny-list functionality"
    }