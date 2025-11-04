# MenuImportEndpoint.py
# FastAPI endpoints for Menu Import CSV functionality
# Provides dedicated API routes for admin users to import menus from CSV files

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.MenuImportPydanticModel import (
    MenuImportRequest, 
    MenuImportResponse, 
    MenuImportErrorResponse
)
from ..auth.dependencies import get_current_admin
from ..logic.MenuImportLogic import menu_import_logic
from ..database.models import User

router = APIRouter(
    prefix="/menu-management",
    tags=["Menu Management"]
)


@router.post(
    "/import-csv/CreateMenuFromCsv",
    response_model=MenuImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import menu from CSV file",
    description="""Import a menu from a CSV file with comprehensive validation and error checking.

**Purpose:**
This endpoint reads a CSV file from the server filesystem, validates its structure and data integrity,
and creates a new menu with associated categories and items. The menu is created as inactive by default.

**CSV Structure Required:**
The CSV file must have exactly these columns in this order:
```csv
WhatSort,FoodCategory,ItemID,NameRus,DisplayOrder,StartAt,EndAt
```

**Row Types:**
- **ITEMS rows**: `WhatSort="ITEMS"`, ItemID filled, NameRus filled
- **CATEGORY rows**: `WhatSort="CATEGORY"`, ItemID empty, NameRus empty

**Validation Rules:**
1. **File Structure**: Must be valid CSV with required columns
2. **ItemID Validation**: Must exist in items_live table AND be non-archived
3. **FoodCategory Validation**: Must exist in food_categories table AND be used by non-archived items
4. **DisplayOrder**: Must be valid integers (non-negative)
5. **Time Format**: StartAt and EndAt must be HH:MM:SS format with StartAt < EndAt
6. **No Duplicates**: No duplicate ItemIDs, no duplicate categories
7. **Row Type Rules**: ITEMS rows must have ItemID/NameRus, CATEGORY rows must not

**Database Operations:**
If validation passes, the system will:
1. Create a new Menu record (inactive by default)
2. Create MenuCategory records for each unique category with display_order
3. Create MenuItem records for each item with display_order, start_at, end_at

**Authentication:**
- Requires Admin or SuperAdmin role
- Uses standard JWT authentication (not kiosk tokens)

**Error Handling:**
- **404 Not Found**: CSV file not found at specified path
- **400 Bad Request**: Invalid CSV structure or format errors
- **409 Conflict**: Menu name already exists
- **422 Unprocessable Entity**: Data validation errors with detailed error list
- **500 Internal Server Error**: Database or system error occurred

**Security:** 
Requires Admin or SuperAdmin authentication. File access is validated for security.
    """,
    responses={
        201: {
            "description": "Menu imported successfully",
            "model": MenuImportResponse
        },
        404: {
            "description": "CSV file not found",
            "model": MenuImportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "FILE_NOT_FOUND",
                        "message": "CSV file not found at path: /tmp/menu.csv",
                        "file_path": "/tmp/menu.csv"
                    }
                }
            }
        },
        400: {
            "description": "Invalid CSV structure",
            "model": MenuImportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "INVALID_CSV_STRUCTURE",
                        "message": "CSV file missing required columns: ItemID, DisplayOrder",
                        "file_path": "/tmp/menu.csv"
                    }
                }
            }
        },
        409: {
            "description": "Menu name already exists",
            "model": MenuImportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "MENU_NAME_EXISTS",
                        "message": "Menu with name 'Breakfast Menu' already exists"
                    }
                }
            }
        },
        422: {
            "description": "Data validation errors",
            "model": MenuImportResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "CSV validation failed with 2 errors",
                        "validation_errors": [
                            {
                                "row_number": 5,
                                "column": "ItemID",
                                "error_type": "ITEM_NOT_FOUND_OR_ARCHIVED",
                                "message": "Item with ID 999 does not exist or is archived",
                                "value": "999"
                            },
                            {
                                "row_number": 8,
                                "column": "DisplayOrder",
                                "error_type": "INVALID_INTEGER",
                                "message": "DisplayOrder must be an integer",
                                "value": "abc"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def import_menu_from_csv(
    request: MenuImportRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Import menu from CSV file - Admin only.
    
    This endpoint processes a CSV file to create a new menu with categories and items.
    The CSV file must be located on the server filesystem at the specified path.
    
    **CSV Format Example:**
    ```csv
    WhatSort,FoodCategory,ItemID,NameRus,DisplayOrder,StartAt,EndAt
    ITEMS,beverages,10,картофель фри,1,06:00:00,23:00:00
    ITEMS,beverages,15,кока-кола,2,06:00:00,23:00:00
    CATEGORY,beverages,,,1,00:00:00,23:59:59
    ITEMS,meals,20,бургер,1,10:00:00,22:00:00
    CATEGORY,meals,,,2,00:00:00,23:59:59
    ```
    
    **Validation Process:**
    1. File existence and accessibility check
    2. CSV structure validation (required columns)
    3. Data format validation (integers, time formats)
    4. Business logic validation (item existence, category usage)
    5. Duplicate detection (items and categories)
    6. Database integrity checks
    
    **Menu Creation:**
    - Menu is created as inactive (is_active = False)
    - Categories are created with display_order from CSV
    - Items are created with display_order, start_at, end_at from CSV
    - All operations are performed in a single database transaction
    
    Args:
        request: MenuImportRequest containing file_path, menu_name, and description
        current_user: Current authenticated admin user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        MenuImportResponse with operation result and validation details
        
    Raises:
        HTTPException: 
            - 404 if CSV file not found
            - 400 if CSV structure invalid
            - 409 if menu name already exists
            - 422 if data validation fails (returns validation errors)
            - 500 for database/system errors
    """
    try:
        return await menu_import_logic.import_menu_from_csv(
            db=db,
            request=request,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import menu: {str(e)}"
        )