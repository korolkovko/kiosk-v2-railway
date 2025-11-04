# session.py
# Pydantic schemas for Session entity

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class SessionBase(BaseModel):
    """Base session schema with common fields"""
    user_id: Optional[int] = Field(None, description="User ID for authenticated sessions")
    device_id: Optional[int] = Field(None, description="Device ID for device sessions")
    customer_id: Optional[int] = Field(None, description="Customer ID for customer sessions")


class SessionCreate(SessionBase):
    """Schema for creating a new session"""
    session_token: Optional[str] = Field(None, description="Optional session token")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "device_id": None,
                "customer_id": None,
                "session_token": "jwt_token_here"
            }
        }
    )


class SessionUpdate(BaseModel):
    """Schema for updating existing session"""
    last_active_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    expired_at: Optional[datetime] = Field(None, description="Session expiration timestamp")
    session_token: Optional[str] = Field(None, description="Updated session token")


class SessionResponse(SessionBase):
    """Schema for session response"""
    session_id: UUID = Field(..., description="Unique session identifier")
    started_at: datetime = Field(..., description="Session start timestamp")
    last_active_at: datetime = Field(..., description="Last activity timestamp")
    expired_at: Optional[datetime] = Field(None, description="Session expiration timestamp")
    session_token: Optional[str] = Field(None, description="Session token")
    
    model_config = ConfigDict(from_attributes=True)