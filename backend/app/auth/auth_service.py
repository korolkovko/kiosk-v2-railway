# auth_service.py
# Authentication service for JWT token management

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..config import get_settings
from ..database.models import User, Role
from ..models.auth import TokenData
from .password import password_manager


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.JWT_SECRET_KEY
        self.algorithm = self.settings.JWT_ALGORITHM
        self.access_token_expire_minutes = self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = self.settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Dictionary containing token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        })
        
        # Create and return JWT token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode a JWT token (excludes kiosk tokens)
        
        Args:
            token: JWT token string to verify
            
        Returns:
            TokenData object with decoded token information
            
        Raises:
            HTTPException: If token is invalid, expired, or belongs to kiosk user
            
        Note:
            Kiosk tokens are excluded from standard authentication and must use dedicated kiosk endpoints
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extract user information from token
            user_id: Optional[int] = payload.get("user_id")
            username: Optional[str] = payload.get("username")
            role_name: Optional[str] = payload.get("role_name")
            
            # Validate required fields
            if user_id is None or username is None:
                raise credentials_exception
            
            # Exclude kiosk tokens from standard authentication
            if role_name == "kiosk":
                raise credentials_exception
            
            # Create and return token data
            token_data = TokenData(
                user_id=user_id,
                username=username,
                role_name=role_name
            )
            return token_data
            
        except JWTError:
            raise credentials_exception

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password (excludes kiosk users)
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
            
        Note:
            Kiosk users are excluded from standard authentication and must use dedicated kiosk endpoints
        """
        # Find user by username
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        # Exclude kiosk users from standard authentication
        if user.role_name == "kiosk":
            return None
        
        # Verify password
        if not password_manager.verify_password(password, user.password_hash):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID to look up
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.user_id == user_id).first()

    def create_token_for_user(self, user: User) -> Dict[str, Any]:
        """
        Create access token for a user
        
        Args:
            user: User object to create token for
            
        Returns:
            Dictionary containing token information
        """
        # Create token data
        token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role_name": user.role_name
        }
        
        # Generate access token
        access_token = self.create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,  # Convert to seconds
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role_name": user.role_name,
                "is_active": user.is_active
            }
        }

    def is_superadmin(self, db: Session, user: User) -> bool:
        """
        Check if user has SuperAdmin role
        
        Args:
            db: Database session
            user: User object to check
            
        Returns:
            True if user is SuperAdmin, False otherwise
        """
        if not user or not user.role:
            return False
        
        # Get user's role
        role = db.query(Role).filter(Role.name == user.role_name).first()
        return role and role.name.lower() == "superadmin"

    def is_admin(self, db: Session, user: User) -> bool:
        """
        Check if user has Admin role (includes SuperAdmin)
        
        Args:
            db: Database session
            user: User object to check
            
        Returns:
            True if user is Admin or SuperAdmin, False otherwise
        """
        if not user or not user.role:
            return False
        
        # Get user's role
        role = db.query(Role).filter(Role.name == user.role_name).first()
        if not role:
            return False
        
        # Check if user is admin or superadmin
        role_name = role.name.lower()
        return role_name in ["admin", "superadmin"]

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh_token"
        })
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_refresh_token(self, token: str) -> TokenData:
        """
        Verify and decode JWT refresh token (excludes kiosk refresh tokens)
        
        Args:
            token: JWT refresh token string to verify
            
        Returns:
            TokenData object with decoded token information
            
        Raises:
            HTTPException: If refresh token is invalid, expired, or belongs to kiosk user
            
        Note:
            Kiosk refresh tokens are excluded from standard authentication and must use dedicated kiosk endpoints
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")
            if token_type != "refresh_token":
                raise credentials_exception
            user_id: Optional[int] = payload.get("user_id")
            username: Optional[str] = payload.get("username")
            role_name: Optional[str] = payload.get("role_name")
            if user_id is None or username is None:
                raise credentials_exception
            
            # Exclude kiosk refresh tokens from standard authentication
            if role_name == "kiosk":
                raise credentials_exception
            
            return TokenData(
                user_id=user_id,
                username=username,
                role_name=role_name
            )
        except JWTError:
            raise credentials_exception


# Global auth service instance
auth_service = AuthService()