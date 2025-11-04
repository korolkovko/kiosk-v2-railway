# MenuRemoveEndpoint.py
# FastAPI endpoints for Menu Remove functionality
# Provides dedicated API routes for admin users to delete menus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.MenuRemovePydanticModel import (
    MenuDeleteRequest, 
    MenuDeleteResponse, 
    MenuDeleteErrorResponse
)
from ..auth.dependencies import get_current_admin
from ..logic.MenuRemoveLogic import menu_remove_logic
from ..database.models import User

router = APIRouter(
    prefix="/menu-management",
    tags=["Menu Management"]
)


@router.delete(
    "/delete",
    response_model=MenuDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete menu by ID or name",
    description="""Delete a menu by ID or name. Only accessible by Admin or SuperAdmin users.

**Purpose:**
This endpoint allows admin users to delete menus that are no longer needed.
The menu can be identified by either ID or name (or both for additional validation).

**Business Rules:**
- Only inactive menus can be deleted (is_active = False)
- Active menus must be deactivated first before deletion
- Deletion cascades to all associated MenuCategory and MenuItem records
- Either menu_id or menu_name (or both) must be provided

**Safety Features:**
- Prevents deletion of active menus to avoid disrupting live operations
- Cascade deletion ensures no orphaned records remain
- Full transaction rollback on any error
- Comprehensive logging for audit trails

**Authentication:**
- Requires Admin or SuperAdmin role
- Uses standard JWT authentication (not kiosk tokens)

**Error Handling:**
- **404 Not Found**: Menu with specified ID/name does not exist
- **409 Conflict**: Menu is active and cannot be deleted
- **400 Bad Request**: Neither ID nor name provided
- **500 Internal Server Error**: Database or system error occurred

**Security:** 
Requires Admin or SuperAdmin authentication. Only inactive menus can be deleted.
    """,
    responses={
        200: {
            "description": "Menu deleted successfully",
            "model": MenuDeleteResponse
        },
        404: {
            "description": "Menu not found",
            "model": MenuDeleteErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "by_id": {
                            "summary": "Menu not found by ID",
                            "value": {
                                "success": False,
                                "error": "MENU_NOT_FOUND",
                                "message": "Menu with ID 999 not found",
                                "menu_id": 999
                            }
                        },
                        "by_name": {
                            "summary": "Menu not found by name",
                            "value": {
                                "success": False,
                                "error": "MENU_NOT_FOUND",
                                "message": "Menu with name 'NonExistent Menu' not found",
                                "menu_name": "NonExistent Menu"
                            }
                        }
                    }
                }
            }
        },
        409: {
            "description": "Menu is active and cannot be deleted",
            "model": MenuDeleteErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "MENU_ACTIVE",
                        "message": "Cannot delete active menu 'Breakfast Menu'. Deactivate the menu first.",
                        "menu_name": "Breakfast Menu"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request - missing identifiers"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def delete_menu(
    request: MenuDeleteRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a menu by ID or name - Admin only.
    
    This endpoint allows admin users to delete menus that are no longer needed.
    Only inactive menus can be deleted to prevent disruption of live operations.
    
    **Deletion Process:**
    1. Locate menu by provided ID and/or name
    2. Validate menu exists
    3. Check menu is inactive (is_active = False)
    4. Delete menu with cascade to MenuCategory and MenuItem records
    5. Return deletion statistics
    
    **Business Logic:**
    - Active menus (is_active = True) cannot be deleted
    - Deletion cascades to remove all associated categories and items
    - Either menu_id or menu_name must be provided
    - If both are provided, they must refer to the same menu
    
    **Safety Features:**
    - Transaction-based deletion with automatic rollback on errors
    - Comprehensive validation before deletion
    - Detailed logging for audit purposes
    
    Args:
        request: MenuDeleteRequest containing menu_id and/or menu_name
        current_user: Current authenticated admin user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        MenuDeleteResponse with deletion result and statistics
        
    Raises:
        HTTPException: 
            - 404 if menu not found
            - 409 if menu is active
            - 400 if request validation fails
            - 500 for database/system errors
    """
    try:
        return await menu_remove_logic.delete_menu(
            db=db,
            request=request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete menu: {str(e)}"
        )


@router.get(
    "/list",
    summary="Get all menus summary",
    description="""Get summary of all existing menus with their status.

Returns information about all menus in the system, including their active status,
which helps administrators understand which menus can be deleted.

**Security:** Requires Admin or SuperAdmin authentication.
    """,
    responses={
        200: {
            "description": "Menus summary retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_menus": 5,
                        "active_menus": 2,
                        "inactive_menus": 3,
                        "menus": [
                            {
                                "id": 1,
                                "name": "Breakfast Menu",
                                "description": "Morning items",
                                "is_active": True
                            },
                            {
                                "id": 2,
                                "name": "Lunch Menu",
                                "description": "Afternoon items",
                                "is_active": False
                            }
                        ]
                    }
                }
            }
        },
        403: {
            "description": "Insufficient permissions"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def get_all_menus_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get summary of all menus - Admin only.
    
    Returns comprehensive information about all menus in the system,
    including their active status and basic details.
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Dictionary containing menus summary and statistics
    """
    try:
        return await menu_remove_logic.get_all_menus_summary(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menus summary: {str(e)}"
        )