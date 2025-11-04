# ItemPromotionPydanticModel.py
# Pydantic models for item promotion toggle functionality

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ItemPromotionRequest(BaseModel):
    """Request model for toggling item promotion status"""
    item_id: int = Field(..., description="ID of the LiveItem to update promotion status")
    promoted: bool = Field(..., description="Promotion status to set (true/false)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": 123,
                "promoted": True
            }
        }
    )

class ItemPromotionResponse(BaseModel):
    """Response model for item promotion toggle"""
    item_id: int
    name_ru: str
    name_eng: str | None
    promoted: bool
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )