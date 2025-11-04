# ItemLiveStockReplenishmentPydanticModel.py
# Pydantic models for stock replenishment or removal
# you can go eith >0 (to add) or ,<0 (to remove) quantities

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class ItemLiveStockReplenishmentRequest(BaseModel):
    """Request model for stock replenishment or removal"""
    item_id: int = Field(..., description="ID of the LiveItem")
    quantity: int = Field(..., description="Positive or negative quantity to adjust stock")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": 123,
                "quantity": -10
            }
        }
    )

class ItemLiveStockReplenishmentResponse(BaseModel):
    """Response model for stock replenishment or removal"""
    item_id: int
    unit_name_ru: str
    unit_name_eng: Optional[str]
    stock_quantity: int
    reserved_quantity: int
    operation_id: int
    changed_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "item_id": 123,
                "unit_name_ru": "шт",
                "unit_name_eng": "piece",
                "stock_quantity": 5,
                "reserved_quantity": 2,
                "operation_id": 456,
                "changed_at": "2025-08-02T19:32:00Z"
            }
        }
    )