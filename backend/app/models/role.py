# role.py
# Pydantic schemas for Role entity

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class RoleBase(BaseModel):
    """Base role schema with common fields"""
    name: str = Field(..., min_length=2, max_length=100, description="Role name")
    permissions: Optional[Dict[str, Any]] = Field(None, description="JSON permissions structure")


class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "admin",
                "permissions": {
                    "can_create_users": True,
                    "can_manage_inventory": True,
                    "can_view_reports": True,
                    "can_manage_devices": True
                }
            }
        }
    )


class RoleUpdate(BaseModel):
    """Schema for updating existing role"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    permissions: Optional[Dict[str, Any]] = None


class RoleResponse(RoleBase):
    """Schema for role response"""
    role_id: int = Field(..., description="Unique role identifier")
    created_at: datetime = Field(..., description="Role creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)