# MediaUpdatePydanticModel.py
# Pydantic models for Media Update API
#
# Purpose:
# Admin endpoint to trigger silent media updates on all connected kiosks.
# When media (images/videos) are updated in storage (S3/local), admin calls this API
# to notify kiosks to re-download and refresh the specific media in their IndexedDB cache.
#
# Validation Rules:
# - media_type: "item" → identifier must be valid item_id from items_live (not archived)
# - media_type: "category_open" → identifier must be valid category name from food_categories table
# - media_type: "category_sorry" → identifier must be valid category name from food_categories table
# - media_type: "category_promoted" → identifier must be exactly "promoted"
# - media_type: "screensaver" → identifier must be exactly "screensaver"
# - media_type: "order_handling" → identifier must be exactly "order_handling"
# - media_type: "service_mode" → identifier must be one of: "menu", "maintenance", "dayoff"
#
# Examples:
#
# 1. Update item poster (item ID 5):
# POST /api/v1/media/update
# {
#   "media_type": "item",
#   "identifier": "5"
# }
#
# 2. Update category open poster (beverages category):
# POST /api/v1/media/update
# {
#   "media_type": "category_open",
#   "identifier": "beverages"
# }
#
# 3. Update category sorry poster (food category):
# POST /api/v1/media/update
# {
#   "media_type": "category_sorry",
#   "identifier": "food"
# }
#
# 4. Update promoted poster (NEW category):
# POST /api/v1/media/update
# {
#   "media_type": "category_promoted",
#   "identifier": "promoted"
# }
#
# 5. Update screensaver:
# POST /api/v1/media/update
# {
#   "media_type": "screensaver",
#   "identifier": "screensaver"
# }
#
# 6. Update order handling media:
# POST /api/v1/media/update
# {
#   "media_type": "order_handling",
#   "identifier": "order_handling"
# }
#
# 7. Update service mode picture (maintenance):
# POST /api/v1/media/update
# {
#   "media_type": "service_mode",
#   "identifier": "maintenance"
# }
#
# 8. Update service mode picture (dayoff):
# POST /api/v1/media/update
# {
#   "media_type": "service_mode",
#   "identifier": "dayoff"
# }
#
# 9. Update service mode picture (menu):
# POST /api/v1/media/update
# {
#   "media_type": "service_mode",
#   "identifier": "menu"
# }

from pydantic import BaseModel, Field, field_validator
from typing import Literal

class MediaUpdateRequest(BaseModel):
    """
    Request model for media update notification

    Triggers silent background media refresh on all connected kiosks.
    Kiosks will re-download the specified media from storage and update their IndexedDB cache.
    """
    media_type: Literal[
        "item",                  # Item poster (items table)
        "category_open",         # Category open poster (food_categories table)
        "category_sorry",        # Category sorry poster (food_categories table)
        "category_promoted",     # Promoted poster (NEW category, only "promoted" allowed)
        "screensaver",           # Screensaver media (only "screensaver" allowed)
        "order_handling",        # Order handling media (only "order_handling" allowed)
        "service_mode"           # Service mode picture (only "menu", "maintenance", "dayoff" allowed)
    ] = Field(
        ...,
        description="Type of media to update"
    )

    identifier: str = Field(
        ...,
        description="Item ID, category name, or specific media name (depends on media_type)",
        examples=["5", "beverages", "promoted", "screensaver", "maintenance"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "media_type": "item",
                    "identifier": "5"
                },
                {
                    "media_type": "category_promoted",
                    "identifier": "promoted"
                },
                {
                    "media_type": "category_open",
                    "identifier": "beverages"
                },
                {
                    "media_type": "category_sorry",
                    "identifier": "beverages"
                },
                {
                    "media_type": "screensaver",
                    "identifier": "screensaver"
                },
                {
                    "media_type": "service_mode",
                    "identifier": "maintenance"
                }
            ]
        }
    }

class MediaUpdateResponse(BaseModel):
    """Response model for media update notification"""
    success: bool = Field(..., description="Whether the media update was triggered successfully")
    message: str = Field(..., description="Human-readable message")
    media_type: str = Field(..., description="Type of media updated")
    identifier: str = Field(..., description="Identifier of the media updated")
    kiosks_notified: int = Field(..., description="Number of kiosks notified via SSE")

class MediaUpdateErrorResponse(BaseModel):
    """Error response model for media update"""
    success: bool = False
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    media_type: str | None = Field(None, description="Type of media that failed")
    identifier: str | None = Field(None, description="Identifier that failed validation")
