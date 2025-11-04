# ReceiptPydanticModels.py
# Pydantic models for Receipt operations including slip, fiscal, and summary receipts

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class SlipReceiptResponse(BaseModel):
    """Response model for slip receipt details"""
    slip_receipt_id: UUID = Field(..., description="Unique slip receipt identifier")
    order_id: Optional[int] = Field(None, description="Associated order ID")
    receipt_pos_terminal_returned_id: Optional[str] = Field(None, description="POS terminal returned ID")
    receipt_body: Optional[Dict[str, Any]] = Field(None, description="Receipt content as JSON")
    created_at: datetime = Field(..., description="Receipt creation timestamp")
    created_by: Optional[str] = Field(None, description="Who created the receipt")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class FiscalReceiptResponse(BaseModel):
    """Response model for fiscal receipt details"""
    fiscal_receipt_id: UUID = Field(..., description="Unique fiscal receipt identifier")
    order_id: Optional[int] = Field(None, description="Associated order ID")
    receipt_fiscal_machine_returned_id: Optional[str] = Field(None, description="Fiscal machine returned ID")
    receipt_body: Optional[Dict[str, Any]] = Field(None, description="Fiscal receipt content as JSON")
    created_at: datetime = Field(..., description="Receipt creation timestamp")
    created_by: Optional[str] = Field(None, description="Who created the receipt")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SummaryReceiptResponse(BaseModel):
    """Response model for summary receipt details"""
    summary_receipt_id: UUID = Field(..., description="Unique summary receipt identifier")
    order_id: Optional[int] = Field(None, description="Associated order ID")
    slip_receipt_id: Optional[UUID] = Field(None, description="Associated slip receipt ID")
    fiscal_receipt_id: Optional[UUID] = Field(None, description="Associated fiscal receipt ID")
    pickup_code: Optional[str] = Field(None, description="Pickup code")
    pin_code: Optional[str] = Field(None, description="PIN code")
    created_at: datetime = Field(..., description="Receipt creation timestamp")
    created_by: Optional[str] = Field(None, description="Who created the receipt")
    
    # Related receipts
    slip_receipt: Optional[SlipReceiptResponse] = Field(None, description="Slip receipt details")
    fiscal_receipt: Optional[FiscalReceiptResponse] = Field(None, description="Fiscal receipt details")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ReceiptCreateRequest(BaseModel):
    """Request model for creating receipts"""
    order_id: int = Field(..., description="Order ID for the receipt")
    receipt_type: str = Field(..., description="Type of receipt (slip, fiscal, summary)")
    receipt_body: Optional[Dict[str, Any]] = Field(None, description="Receipt content")
    device_returned_id: Optional[str] = Field(None, description="Device returned ID")
    created_by: Optional[str] = Field(None, description="Creator identifier")

    @validator('receipt_type')
    def validate_receipt_type(cls, v):
        allowed_types = ["slip", "fiscal", "summary"]
        if v not in allowed_types:
            raise ValueError(f"Receipt type must be one of: {', '.join(allowed_types)}")
        return v

    class Config:
        json_encoders = {
            UUID: str
        }


class ReceiptListResponse(BaseModel):
    """Response model for receipt list queries"""
    receipts: List[SummaryReceiptResponse] = Field(..., description="List of summary receipts")
    total_count: int = Field(..., description="Total number of receipts")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Page size")

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }