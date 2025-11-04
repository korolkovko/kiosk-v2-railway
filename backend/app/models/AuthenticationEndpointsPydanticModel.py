# AuthenticationEndpointsPydanticModel.py
# Pydantic schemas for authentication endpoints

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=1, max_length=100, description="Password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "Password123"
            }
        }
    )


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "user_id": 1,
                    "username": "superadmin",
                    "email": "super@admin.com",
                    "role_name": "superadmin",
                    "is_active": True
                }
            }
        }
    )


class TokenData(BaseModel):
    """Schema for JWT token data"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role_name: Optional[str] = None
    exp: Optional[datetime] = None


class LogoutResponse(BaseModel):
    """Schema for logout response"""
    message: str = Field(default="Successfully logged out", description="Logout confirmation message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Successfully logged out"
            }
        }
    )