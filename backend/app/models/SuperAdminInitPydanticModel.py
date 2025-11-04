# SuperAdminInitPydanticModel.py
# Pydantic schemas for SuperAdmin initialization endpoints

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class SuperAdminSetupRequest(BaseModel):
    """Schema for first-time SuperAdmin setup"""
    username: str = Field(..., min_length=3, max_length=100, description="SuperAdmin username")
    password: str = Field(..., min_length=8, max_length=100, description="SuperAdmin password")
    email: Optional[str] = Field(None, description="SuperAdmin email")
    phone: Optional[str] = Field(None, description="SuperAdmin phone")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "superadmin",
                "password": "SuperSecurePassword123!",
                "email": "super@admin.com",
                "phone": "+1234567890"
            }
        }
    )


class SetupStatusResponse(BaseModel):
    """Schema for setup status response"""
    setup_required: bool = Field(..., description="Whether setup is required")
    has_superadmin: bool = Field(..., description="Whether SuperAdmin exists")
    message: str = Field(..., description="Status message")
    endpoint: str = Field(..., description="Endpoint to use next")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "setup_required": True,
                "has_superadmin": False,
                "message": "System ready for first-time setup",
                "endpoint": "/api/v1/setup/superadmin"
            }
        }
    )