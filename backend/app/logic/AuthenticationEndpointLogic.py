# AuthenticationEndpointLogic.py
# Business logic for authentication endpoints
# NOTE: This layer manages full transaction: validation → operation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from typing import Dict, Any

from ..models.AuthenticationEndpointsPydanticModel import LoginRequest, LoginResponse, LogoutResponse
from ..services.AuthenticationEndpointsDBCRUD import authentication_endpoints_db_crud
from ..auth.auth_service import auth_service
from ..config import get_settings
from ..database.models import User

settings = get_settings()


class AuthenticationEndpointLogic:
    """Business logic for authentication endpoints"""
    
    async def login(self, db: Session, login_request: LoginRequest) -> Dict[str, Any]:
        """
        Login logic
        
        Args:
            db: Database session
            login_request: Login credentials
            
        Returns:
            Login response with access token and user info
            
        Raises:
            HTTPException: If credentials are invalid
        """
        try:
            # Authenticate user
            user = auth_service.authenticate_user(
                db=db,
                username=login_request.username,
                password=login_request.password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last login timestamp
            authentication_endpoints_db_crud.update_last_login(db, user.user_id)
            
            # Commit transaction
            db.commit()
            
            # Generate access token
            token_data = auth_service.create_token_for_user(user)
            
            return token_data
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
    
    async def logout(self, current_user: User) -> LogoutResponse:
        """
        Logout logic
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Logout confirmation message
        """
        return LogoutResponse(message=f"User {current_user.username} successfully logged out")
    
    async def get_current_user_info(self, current_user: User) -> User:
        """
        Get current user information
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current user information
        """
        return current_user
    
    async def refresh_token(self, response: Response, db: Session, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            response: FastAPI response object
            db: Database session
            refresh_token: Refresh token
            
        Returns:
            New access token and user info
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            token_data = auth_service.verify_refresh_token(refresh_token)
            user = auth_service.get_user_by_id(db, token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Generate new tokens
            access_token = auth_service.create_access_token(
                data={"user_id": user.user_id, "username": user.username, "role_name": user.role_name}
            )
            new_refresh_token = auth_service.create_refresh_token(
                data={"user_id": user.user_id, "username": user.username, "role_name": user.role_name}
            )
            
            # Set HttpOnly cookie for refresh token
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                path="/auth"
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "role_name": user.role_name,
                    "is_active": user.is_active
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token refresh failed: {str(e)}"
            )


# Global logic instance
authentication_endpoint_logic = AuthenticationEndpointLogic()