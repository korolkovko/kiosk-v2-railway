# kiosk_auth_service.py
# Kiosk authentication service for extended JWT token management with stateless approach
# Provides long-lived JWT tokens for self-service kiosks with device identification

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from ..config import get_settings
from ..database.models import User, Role
from ..models.auth import TokenData
from .password import password_manager


class KioskAuthService:
    """Service for handling kiosk authentication operations with extended JWT tokens"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.KIOSK_JWT_SECRET_KEY
        self.algorithm = self.settings.KIOSK_JWT_ALGORITHM
        self.access_token_expire_days = self.settings.KIOSK_ACCESS_TOKEN_EXPIRE_DAYS
        self.refresh_token_expire_days = self.settings.KIOSK_REFRESH_TOKEN_EXPIRE_DAYS
        self.key_id = self.settings.KIOSK_JWT_KEY_ID

    def create_kiosk_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a long-lived JWT access token for kiosk authentication
        
        Args:
            data: Dictionary containing token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string with extended expiration
        """
        to_encode = data.copy()
        
        # Set expiration time (days instead of minutes for kiosks)
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.access_token_expire_days)
        
        # Generate unique token ID for future extensibility
        jti = str(uuid.uuid4())
        
        # Add standard JWT claims with kiosk-specific extensions
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,  # JWT ID for token tracking
            "kid": self.key_id,  # Key identifier for key rotation
            "type": "kiosk_access_token",
            "device_id": data.get("device_id"),  # Optional device identifier for future use
        })
        
        # Create and return JWT token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_kiosk_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token for kiosk with extended expiration
        
        Args:
            data: Dictionary containing token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Generate unique token ID
        jti = str(uuid.uuid4())
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "kid": self.key_id,
            "type": "kiosk_refresh_token",
            "device_id": data.get("device_id"),
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_kiosk_token(self, token: str) -> TokenData:
        """
        Verify and decode a kiosk JWT token
        
        Args:
            token: JWT token string to verify
            
        Returns:
            TokenData object with decoded token information
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate kiosk credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            token_type = payload.get("type")
            if not token_type or not token_type.startswith("kiosk_"):
                raise credentials_exception
            
            # Extract user information from token
            user_id: Optional[int] = payload.get("user_id")
            username: Optional[str] = payload.get("username")
            role_name: Optional[str] = payload.get("role_name")
            jti: Optional[str] = payload.get("jti")
            device_id: Optional[str] = payload.get("device_id")
            
            # Validate required fields
            if user_id is None or username is None:
                raise credentials_exception
            
            # Verify this is a kiosk role
            if role_name != "kiosk":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token is not for kiosk user"
                )
            
            # Create and return token data with kiosk-specific fields
            token_data = TokenData(
                user_id=user_id,
                username=username,
                role_name=role_name
            )
            
            # Add kiosk-specific attributes for future use
            token_data.jti = jti
            token_data.device_id = device_id
            
            return token_data
            
        except JWTError:
            raise credentials_exception

    def verify_kiosk_refresh_token(self, token: str) -> TokenData:
        """
        Verify and decode kiosk JWT refresh token
        
        Args:
            token: JWT refresh token string to verify
            
        Returns:
            TokenData object with decoded token information
            
        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate kiosk refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")
            
            if token_type != "kiosk_refresh_token":
                raise credentials_exception
            
            user_id: Optional[int] = payload.get("user_id")
            username: Optional[str] = payload.get("username")
            role_name: Optional[str] = payload.get("role_name")
            jti: Optional[str] = payload.get("jti")
            device_id: Optional[str] = payload.get("device_id")
            
            if user_id is None or username is None or role_name != "kiosk":
                raise credentials_exception
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                role_name=role_name
            )
            
            # Add kiosk-specific attributes
            token_data.jti = jti
            token_data.device_id = device_id
            
            return token_data
            
        except JWTError:
            raise credentials_exception

    def authenticate_kiosk_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate kiosk user with username and password
        
        Args:
            db: Database session
            username: Kiosk username to authenticate
            password: Plain text password
            
        Returns:
            User object if authentication successful and user has kiosk role, None otherwise
        """
        # Find user by username
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        # Verify this is a kiosk user
        if user.role_name != "kiosk":
            return None
        
        # Verify password
        if not password_manager.verify_password(password, user.password_hash):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        return user

    def get_kiosk_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get kiosk user by ID
        
        Args:
            db: Database session
            user_id: User ID to look up
            
        Returns:
            User object if found and is kiosk user, None otherwise
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        # Verify this is a kiosk user
        if user and user.role_name == "kiosk":
            return user
        
        return None

    def create_kiosk_token_response(self, user: User, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create complete token response for kiosk user
        
        Args:
            user: Kiosk user object to create tokens for
            device_id: Optional device identifier
            
        Returns:
            Dictionary containing access token, refresh token, and user information
        """
        # Create token data with kiosk-specific claims
        token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role_name": user.role_name,
            "device_id": device_id
        }
        
        # Generate both access and refresh tokens
        access_token = self.create_kiosk_access_token(data=token_data)
        refresh_token = self.create_kiosk_refresh_token(data=token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_days * 24 * 3600,  # Convert days to seconds
            "refresh_expires_in": self.refresh_token_expire_days * 24 * 3600,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "role_name": user.role_name,
                "is_active": user.is_active,
                "device_id": device_id
            }
        }


# Global kiosk auth service instance
kiosk_auth_service = KioskAuthService()