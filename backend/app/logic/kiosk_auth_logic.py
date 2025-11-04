# kiosk_auth_logic.py
# Business logic for kiosk authentication endpoints
# Manages full transaction flow: validation → operation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.kiosk_auth_models import (
    KioskLoginRequest, 
    KioskLoginResponse, 
    KioskRefreshRequest,
    KioskRefreshResponse,
    KioskLogoutResponse,
    KioskSessionValidationResponse
)
from ..services.kiosk_device_registry_crud import kiosk_device_registry_crud
from ..auth.kiosk_auth_service import kiosk_auth_service
from ..database.models import User


class KioskAuthLogic:
    """Business logic for kiosk authentication operations"""
    
    async def kiosk_login(self, db: Session, login_request: KioskLoginRequest) -> Dict[str, Any]:
        """
        Kiosk login logic with extended JWT token generation
        
        Args:
            db: Database session
            login_request: Kiosk login credentials and device info
            
        Returns:
            Login response with long-lived access and refresh tokens
            
        Raises:
            HTTPException: If credentials are invalid or user is not kiosk
        """
        try:
            # Authenticate kiosk user
            user = kiosk_auth_service.authenticate_kiosk_user(
                db=db,
                username=login_request.username,
                password=login_request.password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid kiosk credentials or user is not a kiosk",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last login timestamp
            user.last_login_at = datetime.utcnow()
            db.add(user)
            
            # Update device registry telemetry if device_id provided
            if login_request.device_id:
                await kiosk_device_registry_crud.update_device_last_seen(
                    db=db,
                    device_id=login_request.device_id,
                    kiosk_username=user.username
                )
            
            # Commit database changes
            db.commit()
            
            # Generate kiosk token response with extended expiration
            token_response = kiosk_auth_service.create_kiosk_token_response(
                user=user,
                device_id=login_request.device_id
            )
            
            return token_response
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Kiosk login failed: {str(e)}"
            )
    
    async def kiosk_logout(self, current_user: User, device_id: Optional[str] = None) -> KioskLogoutResponse:
        """
        Kiosk logout logic (stateless - just returns confirmation)
        
        Args:
            current_user: Current authenticated kiosk user
            device_id: Optional device identifier
            
        Returns:
            Logout confirmation message
        """
        # In stateless JWT approach, logout is just a client-side token removal
        # Future: Could add token to deny-list here if needed
        
        return KioskLogoutResponse(
            message=f"Kiosk {current_user.username} successfully logged out",
            kiosk_username=current_user.username
        )
    
    async def kiosk_refresh_token(
        self, 
        db: Session, 
        refresh_request: KioskRefreshRequest
    ) -> Dict[str, Any]:
        """
        Refresh kiosk access token using refresh token
        
        Args:
            db: Database session
            refresh_request: Refresh token and optional device info
            
        Returns:
            New access and refresh tokens
            
        Raises:
            HTTPException: If refresh token is invalid or user not found
        """
        try:
            # Verify refresh token
            token_data = kiosk_auth_service.verify_kiosk_refresh_token(refresh_request.refresh_token)
            
            # Get current user
            user = kiosk_auth_service.get_kiosk_user_by_id(db, token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Kiosk user not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Kiosk user account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update device registry telemetry if device_id provided
            device_id = refresh_request.device_id or getattr(token_data, 'device_id', None)
            if device_id:
                await kiosk_device_registry_crud.update_device_last_seen(
                    db=db,
                    device_id=device_id,
                    kiosk_username=user.username
                )
            
            # Generate new token pair
            token_response = kiosk_auth_service.create_kiosk_token_response(
                user=user,
                device_id=device_id
            )
            
            return token_response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token refresh failed: {str(e)}"
            )
    
    async def validate_kiosk_session(
        self, 
        current_user: User, 
        token_data: Any,
        device_id: Optional[str] = None
    ) -> KioskSessionValidationResponse:
        """
        Validate current kiosk session and return session information
        
        Args:
            current_user: Current authenticated kiosk user
            token_data: Decoded token data
            device_id: Optional device identifier
            
        Returns:
            Session validation response with kiosk information
        """
        # Extract expiration from token data
        expires_at = getattr(token_data, 'exp', None)
        if expires_at is None:
            # Fallback: calculate approximate expiration
            expires_at = datetime.utcnow().replace(
                day=datetime.utcnow().day + kiosk_auth_service.access_token_expire_days
            )
        
        return KioskSessionValidationResponse(
            valid=True,
            kiosk_username=current_user.username,
            user_id=current_user.user_id,
            device_id=device_id or getattr(token_data, 'device_id', None),
            expires_at=expires_at
        )
    
    async def get_kiosk_context_for_payment_processing(
        self,
        current_user: User,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get kiosk context information for payment processing and POS routing
        
        Args:
            current_user: Current authenticated kiosk user
            device_id: Optional device identifier
            
        Returns:
            Dictionary with kiosk context for payment integration
        """
        return {
            "kiosk_username": current_user.username,
            "kiosk_user_id": current_user.user_id,
            "device_id": device_id,
            "is_active": current_user.is_active,
            "role": current_user.role_name,
            "last_login_at": current_user.last_login_at,
            "payment_routing_key": current_user.username  # For POS terminal routing
        }
    
    # Future extensibility methods
    
    async def prepare_for_token_deny_list_support(self, token_jti: str) -> Dict[str, Any]:
        """
        Prepare foundation for future token deny-list functionality
        
        Args:
            token_jti: JWT token ID to potentially deny-list
            
        Returns:
            Dictionary with deny-list preparation info
        """
        # Placeholder for future deny-list implementation
        return {
            "jti": token_jti,
            "deny_list_ready": False,
            "message": "Token deny-list functionality not yet implemented"
        }
    
    async def get_kiosk_session_analytics(
        self,
        db: Session,
        kiosk_username: str
    ) -> Dict[str, Any]:
        """
        Get basic analytics for kiosk session (for future admin monitoring)
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to analyze
            
        Returns:
            Dictionary with basic session analytics
        """
        user = db.query(User).filter(
            User.username == kiosk_username,
            User.role_name == "kiosk"
        ).first()
        
        if not user:
            return {"error": "Kiosk user not found"}
        
        return {
            "kiosk_username": kiosk_username,
            "user_id": user.user_id,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "session_type": "stateless_jwt"
        }


# Global kiosk auth logic instance
kiosk_auth_logic = KioskAuthLogic()