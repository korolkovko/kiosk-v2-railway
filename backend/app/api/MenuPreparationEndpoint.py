# MenuPreparationEndpoint.py
# FastAPI endpoints for Menu Preparation CSV export functionality
# Provides dedicated API routes for admin users to export non-archived items and categories

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.MenuPreparationPydanticModel import (
    MenuCsvExportRequest, 
    MenuCsvExportResponse, 
    MenuCsvExportErrorResponse
)
from ..auth.dependencies import get_current_admin
from ..logic.MenuPreparationLogic import menu_preparation_logic
from ..database.models import User

router = APIRouter(
    prefix="/menu-management",
    tags=["Menu Management"]
)


@router.post(
    "/export-csv/GetAllUnarchivedLiveitemsToCreateMenu",
    response_model=MenuCsvExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Export non-archived live items and categories to CSV",
    description="""Export all non-archived live items and their categories to a CSV file for menu creation purposes.

**Purpose:**
This endpoint generates a CSV file containing all non-archived items and their associated categories, 
formatted specifically for menu creation workflows. The CSV includes both item data and category data 
in a structured format suitable for external menu management systems.

**CSV Structure:**
The generated CSV contains the following columns:
- `WhatSort`: Type indicator ("ITEMS" for item rows, "CATEGORY" for category rows)
- `FoodCategory`: Food category name (populated for both item and category rows)
- `ItemID`: Item ID (populated only for item rows, empty for category rows)
- `NameRus`: Russian name (populated only for item rows, empty for category rows)
- `DisplayOrder`: Display order (empty by default, integer field for future use)
- `StartAt`: Start time (always "00:00:00")
- `EndAt`: End time (always "23:59:59")

**Data Logic:**
- **ITEMS rows**: One row per non-archived item (where `is_archived = false`)
- **CATEGORY rows**: One row per unique category that has non-archived items
- Categories are included only if they have at least one non-archived item

**File Naming:**
Files are automatically named with timestamp: `LiveitemsNonArchived_YYYYMMDD_HHMMSS.csv`

**Authentication:**
- Requires Admin or SuperAdmin role
- Uses standard JWT authentication (not kiosk tokens)

**Error Handling:**
- **404 Not Found**: No non-archived items found to export
- **403 Forbidden**: Permission denied for folder access or file creation
- **500 Internal Server Error**: Database or system error occurred

**Security:** 
Requires Admin or SuperAdmin authentication. The endpoint validates folder permissions 
and creates directories as needed.
    """,
    responses={
        201: {
            "description": "CSV file created successfully",
            "model": MenuCsvExportResponse
        },
        404: {
            "description": "No non-archived items found",
            "model": MenuCsvExportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "NO_DATA",
                        "message": "No non-archived items found to export"
                    }
                }
            }
        },
        403: {
            "description": "Permission denied for folder access",
            "model": MenuCsvExportErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_path": {
                            "summary": "Invalid folder path",
                            "value": {
                                "success": False,
                                "error": "INVALID_PATH",
                                "message": "The specified folder path is invalid or inaccessible",
                                "folder_path": "/invalid/path"
                            }
                        },
                        "permission_denied": {
                            "summary": "Permission denied",
                            "value": {
                                "success": False,
                                "error": "PERMISSION_DENIED",
                                "message": "Permission denied: cannot write to the specified folder",
                                "folder_path": "/protected/folder"
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
async def export_non_archived_items_to_csv(
    request: MenuCsvExportRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Export non-archived live items and categories to CSV file - Admin only.
    
    This endpoint creates a CSV file containing all non-archived menu items and their 
    associated categories, formatted for menu creation workflows. The file is saved 
    to the specified folder path on the server filesystem.
    
    **CSV Format Example:**
    ```csv
    WhatSort,FoodCategory,ItemID,NameRus,DisplayOrder,StartAt,EndAt
    ITEMS,beverages,10,картофель фри,,00:00:00,23:59:59
    ITEMS,beverages,15,кока-кола,,00:00:00,23:59:59
    CATEGORY,beverages,,,00:00:00,23:59:59
    ITEMS,meals,20,бургер,,00:00:00,23:59:59
    CATEGORY,meals,,,00:00:00,23:59:59
    ```
    
    **Business Rules:**
    - Only non-archived items are included (where `is_archived = false`)
    - Each unique category referenced by non-archived items gets one CATEGORY row
    - Items are ordered by category name, then by item ID
    - Categories are ordered alphabetically
    - File is saved with timestamp in filename for uniqueness
    
    **File Operations:**
    - Creates target directory if it doesn't exist
    - Validates write permissions before file creation
    - Uses UTF-8 encoding for proper Russian text support
    
    Args:
        request: MenuCsvExportRequest containing folder_path for file destination
        current_user: Current authenticated admin user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        MenuCsvExportResponse with operation result and file details
        
    Raises:
        HTTPException: 
            - 404 if no non-archived items found
            - 403 if folder access denied or invalid path
            - 500 for database/system errors
    """
    try:
        return await menu_preparation_logic.export_non_archived_items_to_csv(
            db=db,
            request=request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV: {str(e)}"
        )


@router.get(
    "/export-statistics",
    summary="Get menu export statistics",
    description="""Get statistics about items and categories available for menu export.

Returns counts and information about non-archived vs archived items, 
and the number of unique categories that would be included in a CSV export.

**Security:** Requires Admin or SuperAdmin authentication.
    """,
    responses={
        200: {
            "description": "Export statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_items": 150,
                        "non_archived_items": 120,
                        "archived_items": 30,
                        "unique_categories_in_non_archived": 8,
                        "non_archived_percentage": 80.0
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
async def get_menu_export_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get statistics about menu export data - Admin only.
    
    Returns comprehensive statistics about items and categories that would be 
    included in a CSV export, useful for administrative monitoring and planning.
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Dictionary containing menu export statistics
    """
    try:
        return await menu_preparation_logic.get_menu_export_statistics(db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve export statistics: {str(e)}"
        )