# ItemUpdatePropertiesPydanticModel.py
# Pydantic models for updating LiveItem properties (description, price, vat, categories, etc.)
# Updated to use integer kopecks for consistency

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime

class ItemUpdatePropertiesRequest(BaseModel):
    """Request model for updating LiveItem properties"""
    item_id: int = Field(..., description="ID of the LiveItem to update")
    name_ru: Optional[str] = Field(None, min_length=1, max_length=200, description="Russian name")
    name_eng: Optional[str] = Field(None, max_length=200, description="English name")
    description_ru: Optional[str] = Field(None, min_length=1, description="Russian description")
    description_eng: Optional[str] = Field(None, description="English description")
    unit_measure_name_eng: Optional[str] = Field(None, description="Unit of measure name (English)")
    food_category_name: Optional[str] = Field(None, description="Food category name")
    price_net_kopecks: Optional[int] = Field(None, gt=0, description="Net price in kopecks without VAT")
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="VAT rate as percentage")
    vat_amount_kopecks: Optional[int] = Field(None, ge=0, description="Calculated VAT amount in kopecks")
    price_gross_kopecks: Optional[int] = Field(None, gt=0, description="Total price in kopecks including VAT")

    model_config = ConfigDict(
        json_encoders={Decimal: lambda v: str(v)},
        json_schema_extra={
            "example": {
                "item_id": 123,
                "name_ru": "Новый кофе",
                "name_eng": "New coffee",
                "description_ru": "Обновленное описание",
                "description_eng": "Updated description",
                "unit_measure_name_eng": "piece",
                "food_category_name": "Drinks",
                "price_net_kopecks": 300,
                "vat_rate": "20.0",
                "vat_amount_kopecks": 60,
                "price_gross_kopecks": 360
            }
        }
    )

class ItemUpdatePropertiesResponse(BaseModel):
    """Response model for updated LiveItem properties"""
    item_id: int
    name_ru: str
    name_eng: Optional[str]
    description_ru: str
    description_eng: Optional[str]
    unit_measure_name_eng: str
    food_category_name: str
    price_net_kopecks: int
    vat_rate: Optional[Decimal]
    vat_amount_kopecks: int
    price_gross_kopecks: int
    is_active: bool
    created_at: datetime
    created_by: int

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: str(v), datetime: lambda v: v.isoformat()}
    )