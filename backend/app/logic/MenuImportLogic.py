# MenuImportLogic.py
# Business logic for Menu Import CSV functionality

import csv
import os
import re
from datetime import time
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List, Dict, Any, Set, Tuple, Optional

from ..models.MenuImportPydanticModel import (
    MenuImportRequest, 
    MenuImportResponse,
    MenuImportValidationError,
    CsvRowData
)
from ..services.MenuImportDBCRUD import menu_import_db_crud
from ..database.models import User
import logging

logger = logging.getLogger(__name__)


class MenuImportLogic:
    """Business logic for menu import operations"""

    REQUIRED_COLUMNS = ['WhatSort', 'FoodCategory', 'ItemID', 'NameRus', 'DisplayOrder', 'StartAt', 'EndAt']
    VALID_WHAT_SORT_VALUES = ['ITEMS', 'CATEGORY']

    async def import_menu_from_csv(
        self, 
        db: Session, 
        request: MenuImportRequest, 
        current_user: User
    ) -> MenuImportResponse:
        """
        Import menu from CSV file with comprehensive validation
        
        Args:
            db: Database session
            request: Menu import request containing file path, menu name, and description
            current_user: Current authenticated admin user
            
        Returns:
            MenuImportResponse with operation result and validation details
            
        Raises:
            HTTPException: For various error conditions (404, 400, 409, 500)
        """
        try:
            logger.info(f"Menu import requested by user {current_user.username}: {request.menu_name}")
            
            # Step 1: Check if menu name already exists
            if menu_import_db_crud.check_menu_name_exists(db, request.menu_name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Menu with name '{request.menu_name}' already exists"
                )
            
            # Step 2: Validate file exists
            if not os.path.exists(request.file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"CSV file not found at path: {request.file_path}"
                )
            
            # Step 3: Parse CSV file
            csv_rows = self._parse_csv_file(request.file_path)
            
            # Step 4: Validate CSV structure and data
            validation_errors = self._validate_csv_data(db, csv_rows)
            
            if validation_errors:
                return MenuImportResponse(
                    success=False,
                    message=f"CSV validation failed with {len(validation_errors)} errors",
                    validation_errors=validation_errors
                )
            
            # Step 5: Prepare data for database insertion
            items_data, categories_data = self._prepare_menu_data(csv_rows)
            
            # Step 6: Create menu in database
            created_menu = menu_import_db_crud.create_menu_from_validated_data(
                db=db,
                menu_name=request.menu_name,
                description=request.description,
                items_data=items_data,
                categories_data=categories_data
            )
            
            # Step 7: Commit transaction
            db.commit()
            
            logger.info(
                f"Menu '{request.menu_name}' imported successfully by user {current_user.username}: "
                f"{len(items_data)} items, {len(categories_data)} categories"
            )
            
            return MenuImportResponse(
                success=True,
                message="Menu imported successfully",
                menu_id=created_menu.id,
                menu_name=created_menu.name,
                items_imported=len(items_data),
                categories_imported=len(categories_data)
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            db.rollback()
            raise
        except SQLAlchemyError as e:
            # Handle database errors
            db.rollback()
            logger.error(f"Database error during menu import: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while importing menu"
            )
        except Exception as e:
            # Handle unexpected errors
            db.rollback()
            logger.error(f"Unexpected error during menu import: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while importing menu"
            )

    def _parse_csv_file(self, file_path: str) -> List[CsvRowData]:
        """
        Parse CSV file and return structured data
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of CsvRowData objects
            
        Raises:
            HTTPException: If file cannot be read or has invalid structure
        """
        try:
            csv_rows = []
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Detect delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Validate header
                if not reader.fieldnames:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="CSV file is empty or has no header"
                    )
                
                missing_columns = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
                if missing_columns:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"CSV file missing required columns: {', '.join(missing_columns)}"
                    )
                
                # Parse rows
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    csv_rows.append(CsvRowData(
                        row_number=row_num,
                        what_sort=row.get('WhatSort', '').strip(),
                        food_category=row.get('FoodCategory', '').strip(),
                        item_id=row.get('ItemID', '').strip(),
                        name_rus=row.get('NameRus', '').strip(),
                        display_order=row.get('DisplayOrder', '').strip(),
                        start_at=row.get('StartAt', '').strip(),
                        end_at=row.get('EndAt', '').strip()
                    ))
            
            if not csv_rows:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV file contains no data rows"
                )
            
            return csv_rows
            
        except (OSError, PermissionError) as e:
            logger.error(f"File access error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot read CSV file: {str(e)}"
            )
        except UnicodeDecodeError as e:
            logger.error(f"File encoding error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file encoding error. Please ensure file is UTF-8 encoded"
            )

    def _validate_csv_data(self, db: Session, csv_rows: List[CsvRowData]) -> List[MenuImportValidationError]:
        """
        Comprehensive validation of CSV data
        
        Args:
            db: Database session
            csv_rows: Parsed CSV data
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        # Collect data for batch validation
        item_ids = []
        category_names = set()
        seen_item_ids = set()
        seen_categories = set()
        
        # Step 1: Basic structure and format validation
        for row in csv_rows:
            # Validate WhatSort
            if row.what_sort not in self.VALID_WHAT_SORT_VALUES:
                errors.append(MenuImportValidationError(
                    row_number=row.row_number,
                    column="WhatSort",
                    error_type="INVALID_WHAT_SORT",
                    message=f"WhatSort must be 'ITEMS' or 'CATEGORY', got '{row.what_sort}'",
                    value=row.what_sort
                ))
                continue
            
            # Validate DisplayOrder is integer
            try:
                display_order = int(row.display_order)
                if display_order < 0:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="DisplayOrder",
                        error_type="INVALID_DISPLAY_ORDER",
                        message="DisplayOrder must be a non-negative integer",
                        value=row.display_order
                    ))
            except ValueError:
                errors.append(MenuImportValidationError(
                    row_number=row.row_number,
                    column="DisplayOrder",
                    error_type="INVALID_INTEGER",
                    message="DisplayOrder must be an integer",
                    value=row.display_order
                ))
                continue
            
            # Validate time formats
            start_time_error = self._validate_time_format(row.start_at, "StartAt", row.row_number)
            if start_time_error:
                errors.append(start_time_error)
            
            end_time_error = self._validate_time_format(row.end_at, "EndAt", row.row_number)
            if end_time_error:
                errors.append(end_time_error)
            
            # Validate StartAt < EndAt
            if not start_time_error and not end_time_error:
                try:
                    start_time = time.fromisoformat(row.start_at)
                    end_time = time.fromisoformat(row.end_at)
                    if start_time >= end_time:
                        errors.append(MenuImportValidationError(
                            row_number=row.row_number,
                            column="StartAt/EndAt",
                            error_type="INVALID_TIME_RANGE",
                            message="StartAt must be less than EndAt",
                            value=f"{row.start_at} >= {row.end_at}"
                        ))
                except ValueError:
                    pass  # Time format errors already caught above
            
            # Validate row type specific requirements
            if row.what_sort == "ITEMS":
                # ITEMS rows must have ItemID and NameRus
                if not row.item_id:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="ItemID",
                        error_type="MISSING_ITEM_ID",
                        message="ITEMS rows must have ItemID filled",
                        value=row.item_id
                    ))
                else:
                    try:
                        item_id = int(row.item_id)
                        if item_id in seen_item_ids:
                            errors.append(MenuImportValidationError(
                                row_number=row.row_number,
                                column="ItemID",
                                error_type="DUPLICATE_ITEM_ID",
                                message=f"Duplicate ItemID {item_id}",
                                value=row.item_id
                            ))
                        else:
                            seen_item_ids.add(item_id)
                            item_ids.append(item_id)
                    except ValueError:
                        errors.append(MenuImportValidationError(
                            row_number=row.row_number,
                            column="ItemID",
                            error_type="INVALID_ITEM_ID",
                            message="ItemID must be an integer",
                            value=row.item_id
                        ))
                
                if not row.name_rus:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="NameRus",
                        error_type="MISSING_NAME_RUS",
                        message="ITEMS rows must have NameRus filled",
                        value=row.name_rus
                    ))
            
            elif row.what_sort == "CATEGORY":
                # CATEGORY rows must have empty ItemID and NameRus
                if row.item_id:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="ItemID",
                        error_type="CATEGORY_SHOULD_NOT_HAVE_ITEM_ID",
                        message="CATEGORY rows must have empty ItemID",
                        value=row.item_id
                    ))
                
                if row.name_rus:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="NameRus",
                        error_type="CATEGORY_SHOULD_NOT_HAVE_NAME_RUS",
                        message="CATEGORY rows must have empty NameRus",
                        value=row.name_rus
                    ))
                
                # Check for duplicate categories
                if row.food_category in seen_categories:
                    errors.append(MenuImportValidationError(
                        row_number=row.row_number,
                        column="FoodCategory",
                        error_type="DUPLICATE_CATEGORY",
                        message=f"Duplicate category '{row.food_category}'",
                        value=row.food_category
                    ))
                else:
                    seen_categories.add(row.food_category)
            
            # Collect all categories for validation
            if row.food_category:
                category_names.add(row.food_category)
        
        # Step 2: Database validation (only if no structural errors)
        if not errors:
            # Validate items exist and are non-archived
            if item_ids:
                item_errors = menu_import_db_crud.validate_items_exist_and_non_archived(db, item_ids)
                for error in item_errors:
                    # Find the row number for this item ID
                    for row in csv_rows:
                        if row.what_sort == "ITEMS" and row.item_id == error.value:
                            error.row_number = row.row_number
                            break
                    errors.append(error)
            
            # Validate categories exist and are used by non-archived items
            if category_names:
                category_errors = menu_import_db_crud.validate_categories_exist_and_used_by_non_archived(
                    db, list(category_names)
                )
                for error in category_errors:
                    # Find the first row number for this category
                    for row in csv_rows:
                        if row.food_category == error.value:
                            error.row_number = row.row_number
                            break
                    errors.append(error)
        
        return errors

    def _validate_time_format(self, time_str: str, column_name: str, row_number: int) -> Optional[MenuImportValidationError]:
        """
        Validate time format is HH:MM:SS
        
        Args:
            time_str: Time string to validate
            column_name: Name of the column being validated
            row_number: Row number for error reporting
            
        Returns:
            MenuImportValidationError if invalid, None if valid
        """
        if not time_str:
            return MenuImportValidationError(
                row_number=row_number,
                column=column_name,
                error_type="MISSING_TIME",
                message=f"{column_name} cannot be empty",
                value=time_str
            )
        
        # Validate HH:MM:SS format
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$'
        if not re.match(time_pattern, time_str):
            return MenuImportValidationError(
                row_number=row_number,
                column=column_name,
                error_type="INVALID_TIME_FORMAT",
                message=f"{column_name} must be in HH:MM:SS format",
                value=time_str
            )
        
        # Try to parse as time object
        try:
            time.fromisoformat(time_str)
        except ValueError:
            return MenuImportValidationError(
                row_number=row_number,
                column=column_name,
                error_type="INVALID_TIME_VALUE",
                message=f"{column_name} contains invalid time value",
                value=time_str
            )
        
        return None

    def _prepare_menu_data(self, csv_rows: List[CsvRowData]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Prepare validated CSV data for database insertion
        
        Args:
            csv_rows: Validated CSV row data
            
        Returns:
            Tuple of (items_data, categories_data) for database insertion
        """
        items_data = []
        categories_data = []
        
        for row in csv_rows:
            if row.what_sort == "ITEMS":
                items_data.append({
                    'item_id': int(row.item_id),
                    'food_category': row.food_category,
                    'display_order': int(row.display_order),
                    'start_at': time.fromisoformat(row.start_at),
                    'end_at': time.fromisoformat(row.end_at),
                    'row_number': row.row_number
                })
            
            elif row.what_sort == "CATEGORY":
                categories_data.append({
                    'food_category': row.food_category,
                    'display_order': int(row.display_order),
                    'row_number': row.row_number
                })
        
        return items_data, categories_data


# Create a singleton instance
menu_import_logic = MenuImportLogic()