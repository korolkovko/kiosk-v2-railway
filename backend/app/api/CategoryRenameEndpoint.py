# CategoryRenameEndpoint.py
# FastAPI endpoint for Category Rename operations
# Provides dedicated API route for admin users to rename categories with cascade updates

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database.connection import get_db
from ..models.CategoryRenameEndpointPydanticModel import RenameCategoryRequest, CategoryRenameResponse
from ..auth.dependencies import get_current_admin
from ..logic.CategoryRenameLogic import category_rename_logic
from ..database.models import User

router = APIRouter(
    prefix="/categories",
    tags=["Category Management"]
)


@router.put(
    "/rename",
    response_model=CategoryRenameResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename category with cascade updates (optional ru_label/en_label)",
    description="""PUT /api/v1/categories/rename

Rename a food category and atomically cascade the new primary key to all referencing menu entities. Accessible only to Admin and SuperAdmin users. Optional ru_label and en_label can be updated in the same request; these labels are display-only and do not affect identity. Category identity is the name (primary key).

Authentication:
- Standard JWT via Authorization: Bearer <token>
- Only Admin or SuperAdmin roles are allowed
- Kiosk tokens are not accepted

Headers:
- Content-Type: application/json
- Authorization: Bearer <token>

Request body (JSON) – two modes are supported:

1) Rename with optional labels override
{
  "current_name": "Burgers",
  "new_name": "Smash Burgers",
  "ru_label": "Смэш-бургеры",   // optional: override RU label for the new category
  "en_label": "Smash Burgers"   // optional: override EN label for the new category
}

2) Labels-only update (no rename)
{
  "current_name": "Burgers",
  "ru_label": "Бургеры",        // optional: set/clear RU label
  "en_label": "Burgers"         // optional: set/clear EN label
  // new_name omitted → only labels will be updated
}

Field rules:
- current_name: required string
- new_name: optional string; when provided, must be unique and different from current_name
- ru_label: optional string; if omitted, the existing value remains unchanged; if explicitly set to null, the stored label is cleared
- en_label: optional string; if omitted, the existing value remains unchanged; if explicitly set to null, the stored label is cleared

Validation:
- The current category name must exist
- If provided, new_name must be unique and must differ from current_name
- Only Admin or SuperAdmin users may perform this operation

Atomic cascade behavior:
- All changes occur in a single database transaction; if any step fails, the entire operation is rolled back
- When renaming, updates the primary key in food_categories and updates references in:
  - menu_categories.food_category_name
  - menu_items.food_category_name
  - items_live.food_category_name
- Historical order data is not affected because OrderItem does not store categories

Successful response (200 OK) – actual schema:
{
  "success": true,
  "message": "Food category renamed successfully from 'Burgers' to 'Smash Burgers'",
  "old_name": "Burgers",
  "new_name": "Smash Burgers",
  "category_type": "food",
  "items_updated_count": 12,
  "ru_label": "Смэш-бургеры",
  "en_label": "Smash Burgers"
}

Labels-only success (200 OK):
{
  "success": true,
  "message": "Food category 'Burgers' labels updated successfully",
  "old_name": "Burgers",
  "new_name": "Burgers",
  "category_type": "food",
  "items_updated_count": 0,
  "ru_label": "Бургеры",
  "en_label": "Burgers"
}

Error responses:
- 401 Unauthorized – JWT missing or invalid
- 403 Forbidden – user is not Admin or SuperAdmin
- 404 Not Found – current_name does not exist
- 409 Conflict – new_name already exists
- 422 Unprocessable Entity – invalid input (e.g., new_name equals current_name)
- 500 Internal Server Error – transaction_failed if cascade update fails and rolls back

Example request (rename + labels):
PUT /api/v1/categories/rename
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "current_name": "Burgers",
  "new_name": "Smash Burgers",
  "ru_label": "Смэш-бургеры",
  "en_label": "Smash Burgers"
}

Example request (labels-only):
PUT /api/v1/categories/rename
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "current_name": "Burgers",
  "ru_label": "Бургеры",
  "en_label": "Burgers"
}
"""
)
async def rename_category(
    rename_request: RenameCategoryRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Rename a food category with cascade updates - Admin only.
    
    This endpoint allows admin users to rename a FoodCategory while automatically updating
    all references across the menu system.

    Affected references updated atomically:
    - menu_categories.food_category_name
    - menu_items.food_category_name
    - items_live.food_category_name

    Atomic Operation:
    - All updates happen in a single database transaction
    - If any part fails, everything is rolled back
    - Returns count of ItemLive records that were updated

    Validation Checks:
    - Current category must exist
    - New name must not already exist
    - New name must be different from current name

    Request Example:
    ```json
    {
        "current_name": "Drinks",
        "new_name": "Beverages"
    }
    ```

    Response Example:
    ```json
    {
        "success": true,
        "message": "Food category renamed successfully from 'Drinks' to 'Beverages'",
        "old_name": "Drinks",
        "new_name": "Beverages",
        "category_type": "food",
        "items_updated_count": 12
    }
    ```

    Error Scenarios:

    Category not found (404):
    ```json
    {
        "detail": "Food category 'NonExistent' not found"
    }
    ```

    Name already exists (409):
    ```json
    {
        "detail": "Food category 'Beverages' already exists"
    }
    ```

    Same name provided (400):
    ```json
    {
        "detail": "New name must be different from current name"
    }
    ```
    """
    try:
        return await category_rename_logic.rename_category(
            db=db,
            rename_request=rename_request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename category: {str(e)}"
        )


@router.get(
    "/rename/impact",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get rename impact analysis (shows current/proposed labels)",
    description="""Analyze the impact of renaming a category before performing the operation. Only accessible by Admin or SuperAdmin users.

Query parameters:
- current_name: Current category name
- new_name: Proposed new category name
- ru_label (optional): Proposed Russian display label override (if omitted, current label would be copied)
- en_label (optional): Proposed English display label override (if omitted, current label would be copied)

Response includes:
- current_labels: labels on the current category
- proposed_labels: labels provided in request (or None if not provided)
"""
)
async def get_rename_impact(
    current_name: str,
    new_name: str,
    ru_label: Optional[str] = None,
    en_label: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get impact analysis for food category rename operation - Admin only.
    
    This endpoint allows admin users to preview what would be affected
    by a category rename operation before actually performing it.
    
    Query Parameters:
    - current_name: Current category name
    - new_name: Proposed new category name
    
    Authentication:
    - Requires admin or superadmin role
    - Uses standard JWT authentication (not kiosk tokens)
    
    Returns:
        Dictionary containing impact analysis:
        - is_valid: Whether the rename operation would succeed
        - error_message: Error description if operation would fail
        - items_affected_count: Number of menu items that would be updated
        - impact_description: Human-readable impact description
    """
    try:
        # Create request object including optional proposed labels (display-only)
        rename_request = RenameCategoryRequest(
            current_name=current_name,
            new_name=new_name,
            ru_label=ru_label,
            en_label=en_label
        )
        return await category_rename_logic.get_category_rename_impact_summary(db, rename_request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze rename impact: {str(e)}"
        )