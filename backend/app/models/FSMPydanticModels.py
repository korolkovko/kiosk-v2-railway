# FSMPydanticModels.py
# Pydantic models for FSM operations including state responses and transition requests

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from ..orchestrator.fsm_spec import State, Event
from ..database.models import ActorType


class FSMStateResponse(BaseModel):
    """Response model for FSM state information"""
    order_fsm_kiosk_runtime_id: UUID = Field(..., description="FSM runtime unique identifier")
    order_id: int = Field(..., description="Associated order ID")
    fsm_kiosk_state: State = Field(..., description="Current FSM state")
    
    # Payment context
    payment_session_id: Optional[str] = Field(None, description="Payment session ID")
    pos_terminal_id: Optional[int] = Field(None, description="POS terminal device ID")
    payment_attempt_started_at: Optional[datetime] = Field(None, description="Payment attempt start time")
    payment_attempt_response_at: Optional[datetime] = Field(None, description="Payment attempt response time")
    payment_attempt_result_code: Optional[str] = Field(None, description="Payment result code")
    payment_attempt_result_description: Optional[Dict[str, Any]] = Field(None, description="Payment result details")
    payment_id_transaction: Optional[str] = Field(None, description="Payment transaction ID")
    payment_slip_number_id: Optional[str] = Field(None, description="Payment slip number")
    
    # Fiscal context
    fiscal_session_id: Optional[str] = Field(None, description="Fiscal session ID")
    fiscal_device_id: Optional[int] = Field(None, description="Fiscal device ID")
    fiscal_attempt_started_at: Optional[datetime] = Field(None, description="Fiscal attempt start time")
    fiscal_attempt_response_at: Optional[datetime] = Field(None, description="Fiscal attempt response time")
    fiscal_attempt_result_code: Optional[str] = Field(None, description="Fiscal result code")
    fiscal_attempt_result_description: Optional[Dict[str, Any]] = Field(None, description="Fiscal result details")
    fiscal_id_transaction: Optional[str] = Field(None, description="Fiscal transaction ID")
    fiscalisation_number_id: Optional[str] = Field(None, description="Fiscalisation number ID")
    
    # Printing context
    printing_session_id: Optional[str] = Field(None, description="Printing session ID")
    printing_device_id: Optional[int] = Field(None, description="Printing device ID")
    printing_attempt_started_at: Optional[datetime] = Field(None, description="Printing attempt start time")
    printing_attempt_response_at: Optional[datetime] = Field(None, description="Printing attempt response time")
    printing_attempt_result_code: Optional[str] = Field(None, description="Printing result code")
    printing_attempt_result_description: Optional[Dict[str, Any]] = Field(None, description="Printing result details")
    
    # Pickup information
    pickup_code: Optional[str] = Field(None, description="Pickup code")
    pin_code: Optional[str] = Field(None, description="PIN code")
    qr_code: Optional[str] = Field(None, description="QR code for pickup")
    
    # Audit fields
    created_at: datetime = Field(..., description="FSM runtime creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class FSMTransitionRequest(BaseModel):
    """Request model for FSM state transitions"""
    order_id: int = Field(..., description="Order ID to transition")
    trigger_event: Event = Field(..., description="Event that triggers the transition")
    actor_type: Optional[ActorType] = Field(None, description="Type of actor triggering the transition")
    actor_id: Optional[str] = Field(None, description="ID of the actor")
    comment: Optional[str] = Field(None, description="Optional context comment")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")

    class Config:
        json_encoders = {
            UUID: str
        }


class FSMEventRequest(BaseModel):
    """Request model for FSM events"""
    event_type: Event = Field(..., description="Type of event")
    order_id: int = Field(..., description="Order ID associated with the event")
    actor_type: Optional[ActorType] = Field(None, description="Actor type")
    actor_id: Optional[str] = Field(None, description="Actor ID")
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event-specific data")
    comment: Optional[str] = Field(None, description="Optional comment")

    class Config:
        json_encoders = {
            UUID: str
        }


class FSMTransitionResponse(BaseModel):
    """Response model for FSM transition results"""
    success: bool = Field(..., description="Whether transition was successful")
    from_state: Optional[State] = Field(None, description="Previous state")
    to_state: State = Field(..., description="New state after transition")
    trigger_event: Event = Field(..., description="Event that triggered the transition")
    message: Optional[str] = Field(None, description="Response message")
    log_id: UUID = Field(..., description="Lifecycle log entry ID")

    class Config:
        json_encoders = {
            UUID: str
        }


class FSMValidEventsResponse(BaseModel):
    """Response model for valid events from current state"""
    current_state: State = Field(..., description="Current FSM state")
    valid_events: List[Event] = Field(..., description="List of valid events from current state")
    is_terminal: bool = Field(..., description="Whether current state is terminal")
    timeout_seconds: Optional[int] = Field(None, description="State timeout in seconds")
    retry_allowed: bool = Field(..., description="Whether retry is allowed in current state")

    class Config:
        json_encoders = {
            UUID: str
        }