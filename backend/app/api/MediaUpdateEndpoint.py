# MediaUpdateEndpoint.py
# FastAPI endpoints for Media Update functionality
#
# Purpose:
# Admin endpoint to trigger silent media updates on all connected kiosks.
# When media files are updated in storage, admin calls this API to notify kiosks
# to re-download and refresh the specific media in their IndexedDB cache.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.MediaUpdatePydanticModel import (
    MediaUpdateRequest,
    MediaUpdateResponse,
    MediaUpdateErrorResponse
)
from ..auth.dependencies import get_current_admin
from ..logic.MediaUpdateLogic import media_update_logic
from ..database.models import User

router = APIRouter(
    prefix="/media",
    tags=["Media Management"]
)


@router.post(
    "/update",
    response_model=MediaUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger media update on all kiosks",
    description="""Trigger silent background media refresh on all connected kiosks.

**Purpose:**
When media files (images/videos) are updated in storage (S3/local filesystem), admin calls this API
to notify all connected kiosks to re-download and refresh the specific media in their IndexedDB cache.

**Behavior:**
- Validates the identifier against database (items, categories) or allowed values (static media)
- Broadcasts MEDIA_UPDATE SSE event to all connected kiosks
- Kiosks silently re-download media in background (no UI interruption)
- Works during any kiosk state (browsing, cart, order-handling, service-mode)
- Tolerates missing files (404) gracefully

**Validation Rules:**

1. **media_type: "item"**
   - identifier must be valid item_id from items table
   - Item must not be archived
   - Example: `{"media_type": "item", "identifier": "5"}`

2. **media_type: "category_open"**
   - identifier must be valid category name from food_categories table
   - Example: `{"media_type": "category_open", "identifier": "beverages"}`

3. **media_type: "category_sorry"**
   - identifier must be valid category name from food_categories table
   - Example: `{"media_type": "category_sorry", "identifier": "food"}`

4. **media_type: "category_promoted"**
   - identifier must be exactly "promoted"
   - Example: `{"media_type": "category_promoted", "identifier": "promoted"}`

5. **media_type: "screensaver"**
   - identifier must be exactly "screensaver"
   - Example: `{"media_type": "screensaver", "identifier": "screensaver"}`

6. **media_type: "order_handling"**
   - identifier must be exactly "order_handling"
   - Example: `{"media_type": "order_handling", "identifier": "order_handling"}`

7. **media_type: "service_mode"**
   - identifier must be one of: "menu", "maintenance", "dayoff"
   - Example: `{"media_type": "service_mode", "identifier": "maintenance"}`

**Authentication:**
- Requires Admin or SuperAdmin role
- Uses standard JWT authentication (not kiosk tokens)

**Error Handling:**
- **404 Not Found**: Item/category with specified identifier does not exist
- **400 Bad Request**: Invalid identifier for the media type
- **500 Internal Server Error**: Database or system error occurred

**Use Cases:**
1. Replace item poster image in S3 → Call this API with media_type="item", identifier="5"
2. Update screensaver video → Call this API with media_type="screensaver", identifier="screensaver"
3. Change service mode maintenance picture → Call this API with media_type="service_mode", identifier="maintenance"

**Batch Updates (Multiple Items/Categories):**
This endpoint processes ONE media update at a time. To update multiple items, call the endpoint multiple times.

*Example: Update 3 items and 2 categories*
```bash
# Call 1: Update item 5
POST /api/v1/media/update
{"media_type": "item", "identifier": "5"}

# Call 2: Update item 12
POST /api/v1/media/update
{"media_type": "item", "identifier": "12"}

# Call 3: Update item 18
POST /api/v1/media/update
{"media_type": "item", "identifier": "18"}

# Call 4: Update beverages category (open poster)
POST /api/v1/media/update
{"media_type": "category_open", "identifier": "beverages"}

# Call 5: Update synthetic promoted category poster
POST /api/v1/media/update
{"media_type": "category_promoted", "identifier": "promoted"}
```

**Most Complex Example (Try It Out):**
Update everything after a major media refresh:
```json
[
  {"media_type": "item", "identifier": "1"},
  {"media_type": "item", "identifier": "2"},
  {"media_type": "item", "identifier": "5"},
  {"media_type": "category_open", "identifier": "beverages"},
  {"media_type": "category_open", "identifier": "main"},
  {"media_type": "category_sorry", "identifier": "beverages"},
  {"media_type": "category_promoted", "identifier": "promoted"},
  {"media_type": "screensaver", "identifier": "screensaver"},
  {"media_type": "order_handling", "identifier": "order_handling"},
  {"media_type": "service_mode", "identifier": "maintenance"}
]
```
*(Call the endpoint once for each object in the array)*

**Security:**
Requires Admin or SuperAdmin authentication. Media updates are applied silently on all kiosks.
    """,
    responses={
        200: {
            "description": "Media update triggered successfully",
            "model": MediaUpdateResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Media update triggered for item: 5",
                        "media_type": "item",
                        "identifier": "5",
                        "kiosks_notified": 3
                    }
                }
            }
        },
        404: {
            "description": "Item or category not found",
            "model": MediaUpdateErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "item_not_found": {
                            "summary": "Item not found",
                            "value": {
                                "success": False,
                                "error": "ITEM_NOT_FOUND",
                                "message": "Item with ID 999 not found or is archived",
                                "media_type": "item",
                                "identifier": "999"
                            }
                        },
                        "category_not_found": {
                            "summary": "Category not found",
                            "value": {
                                "success": False,
                                "error": "CATEGORY_NOT_FOUND",
                                "message": "Category 'invalid' not found in food_categories table",
                                "media_type": "category_open",
                                "identifier": "invalid"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid identifier for media type",
            "model": MediaUpdateErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_service_mode": {
                            "summary": "Invalid service mode name",
                            "value": {
                                "success": False,
                                "error": "INVALID_IDENTIFIER",
                                "message": "Invalid identifier for service_mode. Must be one of: menu, maintenance, dayoff",
                                "media_type": "service_mode",
                                "identifier": "invalid"
                            }
                        },
                        "invalid_item_id": {
                            "summary": "Invalid item ID format",
                            "value": {
                                "success": False,
                                "error": "INVALID_IDENTIFIER",
                                "message": "Invalid item ID: 'abc'. Must be a number.",
                                "media_type": "item",
                                "identifier": "abc"
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def trigger_media_update(
    request: MediaUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Trigger media update on all kiosks - Admin only.

    Validates the identifier and broadcasts SSE event to all connected kiosks.
    Kiosks will silently re-download the specified media in background.

    Args:
        request: MediaUpdateRequest containing media_type and identifier
        current_user: Current authenticated admin user (injected by dependency)
        db: Database session (injected by dependency)

    Returns:
        MediaUpdateResponse with operation result

    Raises:
        HTTPException:
            - 404 if item/category not found
            - 400 if identifier validation fails
            - 500 for database/system errors
    """
    try:
        return await media_update_logic.trigger_media_update(
            db=db,
            request=request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger media update: {str(e)}"
        )
