# UserManagementPydanticModel.py
# Pydantic schemas for User management endpoints

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, max_length=50, description="User phone number")
    is_active: bool = Field(True, description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether user account is verified")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    role_name: str = Field(..., description="Role name for the user")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin_user",
                "email": "admin@kiosk.com",
                "phone": "+1234567890",
                "password": "SecurePassword123!",
                "role_name": "admin",
                "is_active": True,
                "is_verified": True
            }
        }
    )


class AdminCreate(BaseModel):
    """Schema for creating admin user (role automatically assigned as 'admin')"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    email: Optional[EmailStr] = Field(None, description="User email address")
    phone: Optional[str] = Field(None, max_length=50, description="User phone number")
    is_active: bool = Field(True, description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether user account is verified")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin_user",
                "password": "SuperPassword123",
                "email": "admin@kiosk.com",
                "phone": "+1234567890",
                "is_active": True,
                "is_verified": True
            }
        }
    )

class KioskCreate(BaseModel):
    """Schema for creating kiosk user (role automatically assigned as 'kiosk')"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    is_active: bool = Field(True, description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether user account is verified")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "kiosk_user",
                "password": "KioskPassword123",
                "is_active": True,
                "is_verified": True
            }
        }
    )

class UserUpdate(BaseModel):
    """Schema for updating existing user"""
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role_name: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response (excludes password)"""
    user_id: int = Field(..., description="Unique user identifier")
    role_name: str = Field(..., description="User role name")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username": "admin_user",
                "email": "admin@kiosk.com",
                "phone": "+1234567890",
                "is_active": True,
                "is_verified": True,
                "user_id": 2,
                "role_name": "admin",
                "created_at": "2025-08-02T18:27:52.177069Z",
                "updated_at": None,
                "last_login_at": None
            }
        }
    )


class UserInDB(UserResponse):
    """Schema for user stored in database (includes password hash)"""
    password_hash: Optional[str] = Field(None, description="Hashed password")