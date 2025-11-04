# CategoryManagementEndpoint.py
# FastAPI endpoints for Category Management (FoodCategory only)
# Provides dedicated API routes for admin users to manage categories

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.CategoryManagementPydanticModel import CreateCategoryRequest, DeleteCategoryRequest, CategoryLabelUpdateRequest, CategoryCreationResponse, CategoryDeletionResponse, FoodCategoryResponse
from ..auth.dependencies import get_current_admin
from ..logic.CategoryManagementLogic import category_management_logic
from ..database.models import User

router = APIRouter(
    prefix="/categories",
    tags=["Category Management"]
)


@router.post(
    "/create",
    response_model=CategoryCreationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new food category (with optional ru_label and en_label)",
    description="""Create a new food category for organizing menu items. Only accessible by Admin or SuperAdmin users.

Required Fields:
- name: Category name (must be unique)

Notes:
- Only food categories are supported. Day categories are no longer supported.
"""
)
async def create_category(
    category_data: CreateCategoryRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new food category - Admin only.
    
    This endpoint allows admin users to create new food categories for organizing menu items.
    
    Validation Rules:
    - Category names must be unique
    - Only admin and superadmin users can create categories
    
    Authentication:
    - Requires admin or superadmin role
    - Uses standard JWT authentication (not kiosk tokens)
    
    Request Example:
    ```json
    {
        "name": "Desserts"
    }
    ```
    """
    try:
        return await category_management_logic.create_category(
            db=db,
            category_data=category_data,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get(
    "/summary",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get categories summary",
    description="Get summary of existing categories for admin reference. Includes additional non-breaking fields: food_categories_details and labels_map. Only accessible by Admin or SuperAdmin users."
)
async def get_categories_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get summary of existing categories - Admin only.
    
    This endpoint provides an overview of existing food categories,
    including counts and sample category names for admin reference.
    
    Authentication:
    - Requires admin or superadmin role
    - Uses standard JWT authentication (not kiosk tokens)
    
    Returns:
        Dictionary containing:
        - food_categories: count and categories (list of names)
    
    Example Response:
    ```json
    {
        "food_categories": {
            "count": 5,
            "categories": ["Beverages", "Desserts", "Meals", "Snacks", "Soups"]
        }
    }
    ```
    """
    try:
        return await category_management_logic.get_category_creation_summary(db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories summary: {str(e)}"
        )


@router.delete(
    "/delete",
    response_model=CategoryDeletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete food category (safe deletion only)",
    description="""Delete a food category. Only accessible by Admin or SuperAdmin users.

IMPORTANT: Safe Deletion Only
- This endpoint will only delete categories that are NOT referenced by any menu items.
- If any ItemLive records reference the category, deletion will be blocked with a 409 Conflict error.

Authentication:
- Requires admin or superadmin role
- Uses standard JWT authentication (not kiosk tokens)
"""
)
async def delete_category(
    delete_request: DeleteCategoryRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a food category - Admin only.
    
    This endpoint allows admin users to safely delete food categories that are not referenced by any menu items.
    
    Safety Rules:
    - Category must exist to be deleted
    - Category must NOT be referenced by any menu items
    - If items reference the category, deletion is blocked with 409 Conflict
    - Only admin and superadmin users can delete categories
    
    Authentication:
    - Requires admin or superadmin role
    - Uses standard JWT authentication (not kiosk tokens)
    
    Request Example:
    ```json
    {
        "name": "Desserts"
    }
    ```
    
    Response Examples:
    
    Success:
    ```json
    {
        "success": true,
        "message": "Food category 'Desserts' deleted successfully"
    }
    ```
    
    Blocked by references:
    ```json
    {
        "detail": "Cannot delete food category 'Drinks': 5 menu items are using this category"
    }
    ```
    
    Category not found:
    ```json
    {
        "detail": "Food category 'NonExistent' not found"
    }
    ```
    """
    try:
        return await category_management_logic.delete_category(
            db=db,
            delete_request=delete_request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )


@router.put(
    "/labels",
    response_model=FoodCategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update category labels (ru_label/en_label only)",
    description="""Update optional display labels (ru_label, en_label) for an existing food category WITHOUT renaming it.

Notes:
- These labels are display-only. They do not affect identity or relations.
- Category identity remains the 'name' (primary key).
- Provide only the fields you want to change; omitted fields remain unchanged.

Authentication:
- Requires admin or superadmin role
- Uses standard JWT authentication (not kiosk tokens)

Request example:
{
  "name": "Desserts",
  "ru_label": "Десерты"
}

Response example:
{
  "name": "Desserts",
  "category_type": "food",
  "ru_label": "Десерты",
  "en_label": "Desserts",
  "created_at": "2025-10-29T00:00:00Z"
}
"""
)
async def update_category_labels(
    label_request: CategoryLabelUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update display-only labels for a category without renaming it.
    Only provided fields (ru_label, en_label) will be updated.
    """
    try:
        return await category_management_logic.update_category_labels(
            db=db,
            label_request=label_request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category labels: {str(e)}"
        )