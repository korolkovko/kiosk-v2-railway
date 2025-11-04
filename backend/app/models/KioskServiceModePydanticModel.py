# KioskServiceModePydanticModel.py
# Pydantic models for kiosk service mode operations
# Handles validation and serialization for service mode API endpoints

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ServiceModeRequest(BaseModel):
    """Request model for activating/deactivating service mode on multiple kiosks"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kiosk_usernames": ["kiosk_001", "kiosk_002", "kiosk_003"],
                "is_service_mode": True,
                "service_picture_name": "maintenance"
            }
        }
    )
    
    kiosk_usernames: List[str] = Field(
        ..., 
        description="List of kiosk usernames to update service mode for",
        min_length=1,
        max_length=50
    )
    is_service_mode: bool = Field(
        ..., 
        description="True to activate service mode, False to deactivate"
    )
    service_picture_name: Optional[str] = Field(
        None, 
        description="Name of service picture to display (required when activating service mode)",
        max_length=100
    )


class ServiceModeResponse(BaseModel):
    """Response model for service mode operations"""
    model_config = ConfigDict(from_attributes=True)
    
    kiosk_username: str = Field(..., description="Kiosk username")
    is_service_mode: bool = Field(..., description="Current service mode status")
    service_picture_name: Optional[str] = Field(None, description="Current service picture name")
    status: str = Field(..., description="Operation status: 'updated', 'ignored', 'error'")
    message: str = Field(..., description="Human-readable status message")


class ServiceModeOperationResult(BaseModel):
    """Overall result of service mode operation on multiple kiosks"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_requested": 3,
                "successful_updates": 2,
                "ignored_kiosks": 1,
                "failed_updates": 0,
                "results": [
                    {
                        "kiosk_username": "kiosk_001",
                        "is_service_mode": True,
                        "service_picture_name": "maintenance",
                        "status": "updated",
                        "message": "Service mode activated successfully"
                    },
                    {
                        "kiosk_username": "kiosk_002",
                        "is_service_mode": True,
                        "service_picture_name": "maintenance",
                        "status": "updated",
                        "message": "Service mode activated successfully"
                    },
                    {
                        "kiosk_username": "kiosk_003",
                        "is_service_mode": False,
                        "service_picture_name": None,
                        "status": "ignored",
                        "message": "Kiosk not found or not active"
                    }
                ]
            }
        }
    )
    
    total_requested: int = Field(..., description="Total number of kiosks requested for update")
    successful_updates: int = Field(..., description="Number of kiosks successfully updated")
    ignored_kiosks: int = Field(..., description="Number of kiosks ignored (not found/inactive)")
    failed_updates: int = Field(..., description="Number of kiosks that failed to update")
    results: List[ServiceModeResponse] = Field(..., description="Detailed results for each kiosk")


class KioskServiceModeStatus(BaseModel):
    """Current service mode status for a kiosk"""
    model_config = ConfigDict(from_attributes=True)
    
    kiosk_username: str = Field(..., description="Kiosk username")
    is_service_mode: bool = Field(..., description="Current service mode status")
    service_picture_name: Optional[str] = Field(None, description="Current service picture name")
    is_kiosk_active: bool = Field(..., description="Whether the kiosk user is active")
    has_active_sse_connection: bool = Field(..., description="Whether kiosk has active SSE connection")


class ServiceModeStatusListResponse(BaseModel):
    """Response model for listing all kiosk service mode statuses"""
    kiosks: List[KioskServiceModeStatus] = Field(..., description="List of kiosk service mode statuses")
    total_kiosks: int = Field(..., description="Total number of kiosks")
    active_kiosks: int = Field(..., description="Number of active kiosks")
    kiosks_in_service_mode: int = Field(..., description="Number of kiosks currently in service mode")