# ItemArchiveEndpoint.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..auth.dependencies import get_current_admin
from ..database.models import User
from ..models.ItemArchivePydanticModel import (
    ItemArchiveStatusRequest, 
    ItemArchiveStatusResponse,
    ItemArchiveErrorResponse
)
from ..logic.ItemArchiveLogic import item_archive_logic
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/archive",
    tags=["item-management"]
)


@router.patch(
    "/status",
    response_model=ItemArchiveStatusResponse,
    status_code=200,
    summary="Archive or unarchive a menu item",
    description="""
**Archive or unarchive a menu item for long-term management.**

**Purpose**: 
This endpoint allows administrators to archive items for long-term storage or unarchive them to make them available for menu management again.

**Archive vs Stop List Distinction**:
- **Archive (is_archived)**: Long-term removal - item is hidden from ALL views (customer and most admin views)
- **Stop List (is_active)**: Temporary removal - item is hidden from customers but visible in admin for quick reactivation

**Business Rules**:
- Only Admin and SuperAdmin users can archive/unarchive items
- Archived items are completely hidden from customer-facing APIs
- Archived items are hidden from most admin views (except archive management)
- Cannot archive an already archived item (returns 409 Conflict)
- Cannot unarchive an already active item (returns 409 Conflict)
- Item must exist to be archived/unarchived (returns 404 Not Found)

**Use Cases**:
- **Archive**: Seasonal items, discontinued products, test items no longer needed
- **Unarchive**: Bringing back seasonal items, reactivating discontinued products

**Error Handling**:
- **404 Not Found**: Item with specified ID does not exist
- **409 Conflict**: Item is already in the requested state (archived/active)
- **403 Forbidden**: User lacks sufficient permissions (not admin/superadmin)
- **500 Internal Server Error**: Database or system error occurred

**Security**: Requires Admin or SuperAdmin authentication.
    """,
    responses={
        200: {
            "description": "Item archive status updated successfully",
            "model": ItemArchiveStatusResponse
        },
        404: {
            "description": "Item not found",
            "model": ItemArchiveErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "ITEM_NOT_FOUND",
                        "message": "Item with ID 999 not found",
                        "item_id": 999
                    }
                }
            }
        },
        409: {
            "description": "Item already in requested state",
            "model": ItemArchiveErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "already_archived": {
                            "summary": "Item already archived",
                            "value": {
                                "success": False,
                                "error": "ALREADY_ARCHIVED",
                                "message": "Item with ID 123 is already archived",
                                "item_id": 123
                            }
                        },
                        "already_active": {
                            "summary": "Item already active",
                            "value": {
                                "success": False,
                                "error": "ALREADY_ACTIVE", 
                                "message": "Item with ID 123 is already active (not archived)",
                                "item_id": 123
                            }
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
async def update_item_archive_status(
    request: ItemArchiveStatusRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Archive or unarchive a menu item.
    
    This endpoint provides long-term item management by allowing administrators to:
    - Archive items that should be removed from all views (seasonal, discontinued, test items)
    - Unarchive items to bring them back into active management
    
    The archive functionality is distinct from the stop list (is_active) feature:
    - Archive: Complete removal from customer and most admin views
    - Stop List: Temporary removal from customers, still visible to admins
    
    Args:
        request: ItemArchiveStatusRequest containing item_id and desired archive status
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        ItemArchiveStatusResponse with operation result and updated status
        
    Raises:
        HTTPException: 
            - 404 if item not found
            - 409 if item already in requested state
            - 403 if user lacks permissions
            - 500 for database/system errors
    """
    try:
        logger.info(
            f"Archive operation requested by user {current_user.username}: "
            f"item_id={request.item_id}, is_archived={request.is_archived}"
        )
        
        result = await item_archive_logic.update_item_archive_status(
            db=db,
            request=request,
            current_user=current_user
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is (they're already properly formatted)
        raise
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error in archive endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the archive request"
        )


@router.get(
    "/statistics",
    summary="Get archive statistics",
    description="""
**Get statistics about archived vs active items.**

Returns counts and percentages of archived and active items in the system.
Useful for administrative dashboards and monitoring.

**Security**: Requires Admin or SuperAdmin authentication.
    """,
    responses={
        200: {
            "description": "Archive statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_items": 150,
                        "active_items": 120,
                        "archived_items": 30,
                        "archive_percentage": 20.0
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
async def get_archive_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get statistics about item archive status.
    
    Returns comprehensive statistics about archived vs active items,
    useful for administrative monitoring and reporting.
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Dictionary containing archive statistics
    """
    try:
        logger.info(f"Archive statistics requested by user {current_user.username}")
        
        statistics = await item_archive_logic.get_archive_statistics(db)
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting archive statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving archive statistics"
        )