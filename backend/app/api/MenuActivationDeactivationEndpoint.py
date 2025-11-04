# MenuActivationDeactivationEndpoint.py
# FastAPI endpoints for Menu Activation/Deactivation functionality
# Provides dedicated API routes for admin users to activate/deactivate menus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.MenuActivationDeactivationPydanticModel import (
    MenuActivationRequest, 
    MenuActivationResponse, 
    MenuActivationErrorResponse
)
from ..auth.dependencies import get_current_admin
from ..logic.MenuActivationDeactivationLogic import menu_activation_deactivation_logic
from ..database.models import User

router = APIRouter(
    prefix="/menu-management",
    tags=["Menu Management"]
)


@router.patch(
    "/activation-status",
    response_model=MenuActivationResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate or deactivate menu",
    description="""Activate or deactivate a menu by ID or name. Only accessible by Admin or SuperAdmin users.

**Purpose:**
This endpoint allows admin users to control which menu is currently active in the system.
Only one menu can be active at any given time to ensure consistent customer experience.

**Business Rules:**
1. **Single Active Menu**: Only one menu can be active at a time
2. **Automatic Deactivation**: When activating a menu, any currently active menu is automatically deactivated
3. **No Active Menus Allowed**: System allows having zero active menus
4. **Idempotency**: Cannot activate already active menu or deactivate already inactive menu

**Activation Logic:**
- **Activate Menu**: Deactivates any currently active menu, then activates the target menu
- **Deactivate Menu**: Simply deactivates the target menu (no replacement)

**Menu Identification:**
- Can use `menu_id`, `menu_name`, or both
- If both provided, they must refer to the same menu
- At least one identifier must be provided

**Authentication:**
- Requires Admin or SuperAdmin role
- Uses standard JWT authentication (not kiosk tokens)

**Error Handling:**
- **404 Not Found**: Menu with specified ID/name does not exist
- **409 Conflict**: Menu already in requested state (active/inactive)
- **400 Bad Request**: Neither ID nor name provided
- **500 Internal Server Error**: Database or system error occurred

**Security:** 
Requires Admin or SuperAdmin authentication. Ensures system integrity with single active menu constraint.
    """,
    responses={
        200: {
            "description": "Menu activation status updated successfully",
            "model": MenuActivationResponse
        },
        404: {
            "description": "Menu not found",
            "model": MenuActivationErrorResponse,
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
            "description": "Menu already in requested state",
            "model": MenuActivationErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "already_active": {
                            "summary": "Menu already active",
                            "value": {
                                "success": False,
                                "error": "ALREADY_ACTIVE",
                                "message": "Menu 'Breakfast Menu' is already active",
                                "menu_name": "Breakfast Menu"
                            }
                        },
                        "already_inactive": {
                            "summary": "Menu already inactive",
                            "value": {
                                "success": False,
                                "error": "ALREADY_INACTIVE",
                                "message": "Menu 'Lunch Menu' is already inactive",
                                "menu_name": "Lunch Menu"
                            }
                        }
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
async def toggle_menu_activation(
    request: MenuActivationRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a menu - Admin only.
    
    This endpoint manages menu activation with the constraint that only one menu
    can be active at any time. When activating a menu, any currently active menu
    is automatically deactivated.
    
    **Single Active Menu Logic:**
    - When `is_active=true`: Target menu becomes active, any other active menu becomes inactive
    - When `is_active=false`: Target menu becomes inactive, no replacement menu is activated
    - System can have zero active menus, but never more than one
    
    **Use Cases:**
    - **Switch Active Menu**: Activate a different menu (automatically deactivates current)
    - **Deactivate All**: Deactivate current menu without replacement
    - **Initial Activation**: Activate first menu when none are active
    
    **Request Examples:**
    
    Activate menu by ID:
    ```json
    {
        "menu_id": 15,
        "is_active": true
    }
    ```
    
    Deactivate menu by name:
    ```json
    {
        "menu_name": "Breakfast Menu",
        "is_active": false
    }
    ```
    
    Activate with both identifiers (for validation):
    ```json
    {
        "menu_id": 15,
        "menu_name": "Breakfast Menu",
        "is_active": true
    }
    ```
    
    Args:
        request: MenuActivationRequest containing menu identifiers and desired status
        current_user: Current authenticated admin user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        MenuActivationResponse with operation result and details
        
    Raises:
        HTTPException: 
            - 404 if menu not found
            - 409 if menu already in requested state
            - 400 if request validation fails
            - 500 for database/system errors
    """
    try:
        return await menu_activation_deactivation_logic.toggle_menu_activation(
            db=db,
            request=request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update menu activation status: {str(e)}"
        )


@router.get(
    "/activation-status",
    summary="Get menu activation statistics",
    description="""Get statistics about menu activation status and currently active menu.

Returns information about total menus, active/inactive counts, and details
about the currently active menu (if any).

**Security:** Requires Admin or SuperAdmin authentication.
    """,
    responses={
        200: {
            "description": "Activation statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_menus": 5,
                        "active_menus": 1,
                        "inactive_menus": 4,
                        "currently_active_menu": {
                            "id": 15,
                            "name": "Breakfast Menu",
                            "description": "Morning items"
                        }
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
async def get_menu_activation_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get menu activation statistics - Admin only.
    
    Returns comprehensive information about menu activation status,
    including which menu is currently active and overall statistics.
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Dictionary containing activation statistics and current active menu
    """
    try:
        return await menu_activation_deactivation_logic.get_menu_activation_statistics(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activation statistics: {str(e)}"
        )