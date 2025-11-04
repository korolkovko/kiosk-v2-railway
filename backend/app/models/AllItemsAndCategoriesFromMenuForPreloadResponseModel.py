# AllItemsAndCategoriesFromMenuForPreloadResponseModel.py
# Pydantic response model for all items and categories from menu for preload endpoint

from pydantic import BaseModel, Field
from typing import List, Optional

class PromotedLabelForPreloadResponse(BaseModel):
    """
    Promoted label configuration for media preload.

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

class AllItemsAndCategoriesFromMenuForPreloadResponse(BaseModel):
    """
    Response model for GET /kiosk/menu/all-for-preload endpoint.

    Returns ALL item IDs and unified category names (with synthetic promoted)
    for media preloading, regardless of stock or availability.

    category_names array includes synthetic promoted category at index [0],
    followed by regular categories. This matches /kiosk/categories structure.

    Purpose: Used at login to cache media files for items that might
    become available during the session via SSE updates.
    """

    item_ids: List[int] = Field(
        ...,
        description="List of all item IDs in the active menu (regardless of stock)",
        example=[1, 2, 3, 8, 10, 11, 12]
    )

    category_names: List[str] = Field(
        ...,
        description="Unified category names including synthetic promoted at [0], then regular categories",
        example=["promoted", "main", "drinks", "sides"]
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "item_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "category_names": ["promoted", "main", "drinks", "sides"]
            }
        }
