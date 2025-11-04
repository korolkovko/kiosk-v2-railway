# ItemStopListPydanticModel.py
# Pydantic models for updating LiveItem stop list status

from pydantic import BaseModel, Field, ConfigDict

class ItemStopListRequest(BaseModel):
    """Request model for updating LiveItem stop list status"""
    item_id: int = Field(..., description="ID of the LiveItem")
    is_active: bool = Field(..., description="Desired active status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": 123,
                "is_active": False
            }
        }
    )

class ItemStopListResponse(BaseModel):
    """Response model for updated LiveItem stop list status"""
    item_id: int
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "item_id": 123,
                "is_active": False
            }
        }
    )