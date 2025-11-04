# AuthenticationEndpoints.py
# Authentication endpoints for login, logout, and token refresh

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.AuthenticationEndpointsPydanticModel import LoginRequest, LoginResponse, LogoutResponse
from ..models.UserManagementPydanticModel import UserResponse
from ..auth import get_current_user
from ..logic.AuthenticationEndpointLogic import authentication_endpoint_logic
from ..database.models import User

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Standard login endpoint for existing users.
    
    Args:
        login_request: Login credentials (username and password)
        db: Database session
        
    Returns:
        Login response with access token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    return await authentication_endpoint_logic.login(db, login_request)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint for authenticated users.
    Since we're using stateless JWT tokens, this endpoint primarily serves
    as a confirmation that the user wants to logout. The actual logout
    happens on the client side by discarding the token.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Logout confirmation message
    """
    return await authentication_endpoint_logic.logout(current_user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserResponse.model_validate(await authentication_endpoint_logic.get_current_user_info(current_user))
    

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str = Cookie(None)
):
    """
    Refresh access token using HttpOnly refresh token cookie
    """
    return await authentication_endpoint_logic.refresh_token(response, db, refresh_token)