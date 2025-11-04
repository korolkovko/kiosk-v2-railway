# KioskAvailableItemsResponseModel.py
# Pydantic models for Kiosk Available Items API response
# Updated to use integer kopecks for consistency

from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import time


class KioskAvailableItemResponse(BaseModel):
    """Response model for available items in kiosk menu"""
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
    promoted: bool
    stock_quantity: int

    # Menu display fields
    display_order: int
    start_at: Optional[time]
    end_at: Optional[time]

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: str(v)}
    )
