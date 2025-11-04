# SSEEventModels.py
# Pydantic models for SSE events sent to kiosk clients
# Updated to send kopeck amounts to frontend

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Union
from datetime import datetime

class ItemStatusChangedEvent(BaseModel):
    """Event for item active status changes (stop list)"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ITEM_STATUS_CHANGED"] = "ITEM_STATUS_CHANGED"
    item_id: int
    is_active: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ItemPromotionChangedEvent(BaseModel):
    """Event for item promotion status changes"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ITEM_PROMOTION_CHANGED"] = "ITEM_PROMOTION_CHANGED"
    item_id: int
    promoted: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ItemStockChangedEvent(BaseModel):
    """Event for item stock quantity changes"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ITEM_STOCK_CHANGED"] = "ITEM_STOCK_CHANGED"
    item_id: int
    stock_quantity: int
    change_quantity: int
    changed_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ItemCreatedEvent(BaseModel):
    """Event for new item creation - sends kopeck amounts to frontend"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ITEM_CREATED"] = "ITEM_CREATED"
    item_id: int
    name_ru: str
    name_eng: str | None
    description_ru: str
    description_eng: str | None
    unit_measure_name_eng: str
    food_category_name: str
    # Price fields now in kopecks
    price_net_kopecks: str
    vat_rate: str | None
    vat_amount_kopecks: str
    price_gross_kopecks: str
    is_active: bool
    promoted: bool
    stock_quantity: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ItemPropertiesChangedEvent(BaseModel):
    """Event for item properties changes - sends kopeck amounts to frontend"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ITEM_PROPERTIES_CHANGED"] = "ITEM_PROPERTIES_CHANGED"
    item_id: int
    name_ru: str
    name_eng: str | None
    description_ru: str
    description_eng: str | None
    unit_measure_name_eng: str
    food_category_name: str
    # Price fields now in kopecks
    price_net_kopecks: str
    vat_rate: str | None
    vat_amount_kopecks: str
    price_gross_kopecks: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OrderStatusChangedEvent(BaseModel):
    """Event for order status changes - filtered by kiosk_username on frontend"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ORDER_STATUS_CHANGED"] = "ORDER_STATUS_CHANGED"
    order_id: int
    kiosk_username: str  # Kiosk that created this order (for frontend filtering)
    status: str  # OrderStatus enum value
    previous_status: str | None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OrderEventTriggeredEvent(BaseModel):
    """Event for FSM events triggered during order processing - filtered by kiosk_username on frontend"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["ORDER_EVENT_TRIGGERED"] = "ORDER_EVENT_TRIGGERED"
    order_id: int
    kiosk_username: str  # Kiosk that created this order (for frontend filtering)
    fsm_event: str  # Event enum value from fsm_spec
    fsm_state: str  # Current FSM state
    previous_state: str | None
    actor_type: str | None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class KioskServiceModeChangedEvent(BaseModel):
    """Event for kiosk service mode activation/deactivation"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["KIOSK_SERVICE_MODE_CHANGED"] = "KIOSK_SERVICE_MODE_CHANGED"
    kiosk_username: str
    is_service_mode: bool
    service_picture_name: str | None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MenuActivatedEvent(BaseModel):
    """Event for menu activation/switching"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["MENU_ACTIVATED"] = "MENU_ACTIVATED"
    menu_id: int
    menu_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MediaUpdateEvent(BaseModel):
    """Event for media update notification (silent background update)"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["MEDIA_UPDATE"] = "MEDIA_UPDATE"
    media_type: str  # "item", "category_open", "category_sorry", "category_promoted", "screensaver", "order_handling", "service_mode"
    identifier: str  # item_id, category name, or specific name
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Union type for all possible SSE events
SSEEvent = Union[
    ItemStatusChangedEvent,
    ItemPromotionChangedEvent,
    ItemStockChangedEvent,
    ItemCreatedEvent,
    ItemPropertiesChangedEvent,
    OrderStatusChangedEvent,
    OrderEventTriggeredEvent,
    KioskServiceModeChangedEvent,
    MenuActivatedEvent,
    MediaUpdateEvent
]