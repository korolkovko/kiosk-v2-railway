# KioskCategoriesResponseModel.py
# Pydantic models for kiosk categories API response
# Provides data transfer objects for food categories endpoint

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class KioskCategoryResponse(BaseModel):
    """
    Response model for a single food category in kiosk API

    Includes synthetic promoted category (display_order=0) merged with regular categories.
    All categories have optional ru_label/en_label for i18n support.

    Attributes:
        name: Category name (primary key)
        display_order: Display position in menu (0=synthetic promoted, 1+=regular)
        ru_label: Russian label for display (optional, falls back to name)
        en_label: English label for display (optional, falls back to name)
        created_at: Category creation timestamp
    """
    name: str
    display_order: int
    ru_label: Optional[str] = None
    en_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PromotedLabelResponse(BaseModel):
    """
    Response model for promoted label configuration.

    Provides localized labels for the promoted items category.
    Frontend uses this to display promoted category name instead of hardcoded values.

    Attributes:
        name: Internal name (e.g., "promoted")
        ru_label: Russian label (e.g., "Новинки!")
        en_label: English label (e.g., "New!")
    """
    name: str
    ru_label: Optional[str] = None
    en_label: Optional[str] = None

    class Config:
        from_attributes = True


class KioskCategoriesListResponse(BaseModel):
    """
    Response model for list of food categories in kiosk API

    Returns unified category structure with synthetic promoted category at index 0.
    Backend merges promoted_label table with menu_categories and shifts display_order by +1.

    Attributes:
        categories: List of all categories (synthetic promoted at [0], regular at [1+])
        total_count: Total number of categories (including synthetic promoted)
    """
    categories: List[KioskCategoryResponse]
    total_count: int