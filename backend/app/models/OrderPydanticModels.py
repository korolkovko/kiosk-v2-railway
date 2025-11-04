# OrderPydanticModels.py
# Pydantic models for Order operations including requests and responses
# All money fields now use integer kopecks for backend consistency

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from uuid import UUID

from ..database.models import OrderStatus


class OrderItemRequest(BaseModel):
    """Request model for creating an order item"""
    item_id: int = Field(..., description="ID of the item from ItemLive")
    quantity: int = Field(..., gt=0, description="Quantity of items to order")
    wishes: Optional[str] = Field(None, max_length=500, description="Customer-specific wishes or options")

    class Config:
        json_encoders = {
            Decimal: str
        }


class OrderItemResponse(BaseModel):
    """Response model for order item details - all amounts in kopecks"""
    item_in_order_id: UUID = Field(..., description="Unique identifier for this order item")
    order_id: int = Field(..., description="Order ID this item belongs to")
    item_id: int = Field(..., description="Original item ID from ItemLive")
    name_ru: str = Field(..., description="Item name in Russian")
    name_eng: Optional[str] = Field(None, description="Item name in English")
    description_ru: str = Field(..., description="Item description in Russian")
    description_eng: Optional[str] = Field(None, description="Item description in English")
    unit_of_measure_ru: str = Field(..., description="Unit of measure in Russian")
    unit_of_measure_eng: Optional[str] = Field(None, description="Unit of measure in English")
    item_price_net_kopecks: int = Field(..., description="Item net price in kopecks (snapshot)")
    item_vat_rate: Decimal = Field(..., description="Item VAT rate as percentage (snapshot)")
    item_vat_amount_kopecks: int = Field(..., description="Item VAT amount in kopecks (snapshot)")
    item_price_gross_kopecks: int = Field(..., description="Item gross price in kopecks (snapshot)")
    quantity: int = Field(..., description="Quantity ordered")
    total_price_net_kopecks: int = Field(..., description="Total net price in kopecks for this line")
    applied_vat_rate: Decimal = Field(..., description="Applied VAT rate as percentage")
    total_vat_amount_kopecks: int = Field(..., description="Total VAT amount in kopecks for this line")
    total_price_gross_kopecks: int = Field(..., description="Total gross price in kopecks for this line")
    wishes: Optional[str] = Field(None, description="Customer wishes")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            UUID: str
        }


class OrderCreateRequest(BaseModel):
    """Request model for creating a new order"""
    items: List[OrderItemRequest] = Field(..., min_items=1, description="List of items to order")
    currency: str = Field(default="643", description="Currency code (ISO 4217 numeric)")
    customer_id: Optional[int] = Field(None, description="Known customer ID if applicable")
    session_id: Optional[UUID] = Field(None, description="Session ID if applicable")

    @validator('currency')
    def validate_currency(cls, v):
        # For now, only support RUB (643)
        if v not in ["643", "RUB"]:
            raise ValueError("Only RUB currency (643) is currently supported")
        return "643"  # Normalize to numeric code

    class Config:
        json_encoders = {
            UUID: str
        }


class OrderResponse(BaseModel):
    """Response model for order details - all amounts in kopecks"""
    order_id: int = Field(..., description="Unique order identifier")
    order_date: date = Field(..., description="Order date")
    status: OrderStatus = Field(..., description="Current order status")
    order_time: datetime = Field(..., description="Order timestamp")
    currency: str = Field(..., description="Order currency")
    total_amount_net_kopecks: int = Field(..., description="Total net amount in kopecks")
    total_amount_vat_kopecks: int = Field(..., description="Total VAT amount in kopecks")
    total_amount_gross_kopecks: int = Field(..., description="Total gross amount in kopecks")
    customer_id: Optional[int] = Field(None, description="Customer ID if known")
    session_id: Optional[UUID] = Field(None, description="Session ID")
    pickup_number: str = Field(..., description="Pickup number for customer")
    pin_code: str = Field(..., description="PIN code for pickup")
    
    # Device snapshots
    kiosk_id: Optional[int] = Field(None, description="Kiosk device ID")
    kiosk_ip: Optional[str] = Field(None, description="Kiosk IP address")
    kiosk_port: Optional[str] = Field(None, description="Kiosk port")
    pos_terminal_id: Optional[int] = Field(None, description="POS terminal ID")
    pos_terminal_ip: Optional[str] = Field(None, description="POS terminal IP")
    pos_terminal_port: Optional[str] = Field(None, description="POS terminal port")
    fiscal_machine_id: Optional[int] = Field(None, description="Fiscal machine ID")
    fiscal_machine_ip: Optional[str] = Field(None, description="Fiscal machine IP")
    fiscal_machine_port: Optional[str] = Field(None, description="Fiscal machine port")
    fiscal_printer_id: Optional[int] = Field(None, description="Fiscal printer ID")
    fiscal_printer_ip: Optional[str] = Field(None, description="Fiscal printer IP")
    fiscal_printer_port: Optional[str] = Field(None, description="Fiscal printer port")
    
    # Related data
    order_items: List[OrderItemResponse] = Field(default_factory=list, description="Order items")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class OrderCommandRequest(BaseModel):
    """Request model for order commands (e.g., retry payment, cancel)"""
    action: str = Field(..., description="Action to perform")
    operation_id: Optional[str] = Field(None, description="Operation ID for idempotency")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            "RETRY_PAYMENT",
            "CHANGE_CARD", 
            "CANCEL_ORDER",
            "RETRY_FISCALIZATION",
            "RETRY_PRINTING",
            "ACCEPT_ALTERNATIVE_RECEIPT",
            "DECLINE_ALTERNATIVE_RECEIPT"
        ]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v

    class Config:
        json_encoders = {
            UUID: str
        }


class OrderCommandResponse(BaseModel):
    """Response model for order command execution"""
    ack: bool = Field(..., description="Command acknowledgment")
    state: Optional[str] = Field(None, description="Current order state after command")
    message: Optional[str] = Field(None, description="Response message")
    operation_id: Optional[str] = Field(None, description="Operation ID")

    class Config:
        json_encoders = {
            UUID: str
        }


class OrderListResponse(BaseModel):
    """Response model for order list queries"""
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., description="Total number of orders")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Page size")

    class Config:
        json_encoders = {
            Decimal: str,
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }