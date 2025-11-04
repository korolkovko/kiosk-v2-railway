# kiosk_auth_models.py
# Pydantic schemas for kiosk authentication and device tracking
# Provides data validation and serialization for kiosk-specific authentication flows

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class KioskLoginRequest(BaseModel):
    """Schema for kiosk login request"""
    username: str = Field(..., min_length=3, max_length=100, description="Kiosk username")
    password: str = Field(..., min_length=1, max_length=100, description="Kiosk password")
    device_id: Optional[str] = Field(None, max_length=100, description="Optional device identifier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "kiosk_store_01",
                "password": "KioskSecurePassword123!",
                "device_id": "terminal_001"
            }
        }
    )


class KioskLoginResponse(BaseModel):
    """Schema for kiosk login response with extended token information"""
    access_token: str = Field(..., description="Long-lived JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")
    user: dict = Field(..., description="Kiosk user information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 2592000,  # 30 days in seconds
                "refresh_expires_in": 7776000,  # 90 days in seconds
                "user": {
                    "user_id": 5,
                    "username": "kiosk_store_01",
                    "role_name": "kiosk",
                    "is_active": True,
                    "device_id": "terminal_001"
                }
            }
        }
    )


class KioskRefreshRequest(BaseModel):
    """Schema for kiosk token refresh request"""
    refresh_token: str = Field(..., description="JWT refresh token")
    device_id: Optional[str] = Field(None, max_length=100, description="Optional device identifier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "device_id": "terminal_001"
            }
        }
    )


class KioskRefreshResponse(BaseModel):
    """Schema for kiosk token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")
    user: dict = Field(..., description="Kiosk user information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 2592000,
                "refresh_expires_in": 7776000,
                "user": {
                    "user_id": 5,
                    "username": "kiosk_store_01",
                    "role_name": "kiosk",
                    "is_active": True,
                    "device_id": "terminal_001"
                }
            }
        }
    )


class KioskLogoutResponse(BaseModel):
    """Schema for kiosk logout response"""
    message: str = Field(default="Kiosk successfully logged out", description="Logout confirmation message")
    kiosk_username: str = Field(..., description="Username of logged out kiosk")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Kiosk successfully logged out",
                "kiosk_username": "kiosk_store_01"
            }
        }
    )


class KioskSessionValidationResponse(BaseModel):
    """Schema for kiosk session validation response"""
    valid: bool = Field(..., description="Whether the session is valid")
    kiosk_username: str = Field(..., description="Kiosk username")
    user_id: int = Field(..., description="Kiosk user ID")
    device_id: Optional[str] = Field(None, description="Device identifier if present")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "valid": True,
                "kiosk_username": "kiosk_store_01",
                "user_id": 5,
                "device_id": "terminal_001",
                "expires_at": "2025-04-22T14:30:00Z"
            }
        }
    )


class KioskTokenData(BaseModel):
    """Extended token data schema for kiosk JWT tokens"""
    user_id: int = Field(..., description="Kiosk user ID")
    username: str = Field(..., description="Kiosk username")
    role_name: str = Field(..., description="User role (should be 'kiosk')")
    jti: Optional[str] = Field(None, description="JWT token ID")
    device_id: Optional[str] = Field(None, description="Device identifier")
    exp: Optional[datetime] = Field(None, description="Token expiration timestamp")
    iat: Optional[datetime] = Field(None, description="Token issued at timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 5,
                "username": "kiosk_store_01",
                "role_name": "kiosk",
                "jti": "550e8400-e29b-41d4-a716-446655440000",
                "device_id": "terminal_001",
                "exp": "2025-04-22T14:30:00Z",
                "iat": "2025-03-22T14:30:00Z"
            }
        }
    )


# Future extensibility models for device registry and telemetry

class KioskDeviceRegistryBase(BaseModel):
    """Base schema for kiosk device registry (future use)"""
    device_id: str = Field(..., max_length=100, description="Unique device identifier")
    device_name: str = Field(..., max_length=200, description="Human-readable device name")
    location: Optional[str] = Field(None, max_length=200, description="Device location")
    is_active: bool = Field(True, description="Whether device is active")


class KioskDeviceRegistryCreate(KioskDeviceRegistryBase):
    """Schema for creating device registry entry"""
    kiosk_username: str = Field(..., description="Associated kiosk username")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "terminal_001",
                "device_name": "Store Front Kiosk #1",
                "location": "Main Store Entrance",
                "kiosk_username": "kiosk_store_01",
                "is_active": True
            }
        }
    )


class KioskDeviceRegistryResponse(KioskDeviceRegistryBase):
    """Schema for device registry response"""
    registry_id: int = Field(..., description="Registry entry ID")
    kiosk_username: str = Field(..., description="Associated kiosk username")
    last_seen_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    created_at: datetime = Field(..., description="Registry creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "registry_id": 1,
                "device_id": "terminal_001",
                "device_name": "Store Front Kiosk #1",
                "location": "Main Store Entrance",
                "kiosk_username": "kiosk_store_01",
                "is_active": True,
                "last_seen_at": "2025-03-22T14:30:00Z",
                "created_at": "2025-03-01T10:00:00Z"
            }
        }
    )


class KioskTelemetryUpdate(BaseModel):
    """Schema for updating kiosk telemetry data"""
    device_id: str = Field(..., description="Device identifier")
    last_seen_at: datetime = Field(..., description="Last activity timestamp")
    status: Optional[str] = Field(None, description="Device status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "terminal_001",
                "last_seen_at": "2025-03-22T14:30:00Z",
                "status": "active"
            }
        }
    )