# MenuPreparationLogic.py
# Business logic for Menu Preparation CSV export functionality

import csv
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import List, Dict, Any

from ..models.MenuPreparationPydanticModel import (
    MenuCsvExportRequest,
    MenuCsvExportResponse
)
from ..services.MenuPreparationDBCRUD import menu_preparation_db_crud
from ..database.models import User, ItemLive
import logging

logger = logging.getLogger(__name__)


class MenuPreparationLogic:
    """Business logic for menu preparation operations"""

    async def export_non_archived_items_to_csv(
        self, 
        db: Session, 
        request: MenuCsvExportRequest, 
        current_user: User
    ) -> MenuCsvExportResponse:
        """
        Export non-archived live items and their categories to CSV file
        
        Args:
            db: Database session
            request: CSV export request containing folder path
            current_user: Current authenticated admin user
            
        Returns:
            MenuCsvExportResponse with operation result and file details
            
        Raises:
            HTTPException: For various error conditions (404, 403, 500)
        """
        try:
            # Step 1: Fetch non-archived items from database
            logger.info(f"CSV export requested by user {current_user.username} to path: {request.folder_path}")
            
            non_archived_items = menu_preparation_db_crud.get_non_archived_items_with_categories(db)
            
            if not non_archived_items:
                logger.warning("No non-archived items found for CSV export")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No non-archived items found to export"
                )

            # Step 2: Extract unique categories
            unique_categories = menu_preparation_db_crud.get_unique_categories_from_non_archived_items(db)
            
            # Step 3: Generate CSV filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"LiveitemsNonArchived_{timestamp}.csv"
            
            # Step 4: Validate and create directory path
            folder_path = Path(request.folder_path)
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to create directory {folder_path}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: cannot create or write to folder {request.folder_path}"
                )
            
            file_path = folder_path / filename
            
            # Step 5: Generate CSV content
            csv_rows = self._generate_csv_rows(non_archived_items, unique_categories)
            
            # Step 6: Write CSV file
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['WhatSort', 'FoodCategory', 'ItemID', 'NameRus', 'DisplayOrder', 'StartAt', 'EndAt'])
                    
                    # Write data rows
                    writer.writerows(csv_rows)
                    
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to write CSV file {file_path}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: cannot write file to {request.folder_path}"
                )
            
            # Step 7: Prepare response
            items_count = len(non_archived_items)
            categories_count = len(unique_categories)
            total_rows = items_count + categories_count
            
            logger.info(
                f"CSV export completed by user {current_user.username}: "
                f"{items_count} items, {categories_count} categories, {total_rows} total rows"
            )
            
            return MenuCsvExportResponse(
                success=True,
                message="CSV file generated successfully",
                file_path=str(file_path),
                filename=filename,
                items_count=items_count,
                categories_count=categories_count,
                total_rows=total_rows
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except SQLAlchemyError as e:
            # Handle database errors
            logger.error(f"Database error during CSV export: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while fetching data for export"
            )
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error during CSV export: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating CSV file"
            )

    def _generate_csv_rows(self, items: List[ItemLive], categories: set) -> List[List[str]]:
        """
        Generate CSV rows for items and categories
        
        Args:
            items: List of non-archived ItemLive objects
            categories: Set of unique category names
            
        Returns:
            List of CSV rows (each row is a list of strings)
        """
        csv_rows = []
        
        # Generate ITEMS rows
        for item in items:
            csv_rows.append([
                'ITEMS',                           # WhatSort
                item.food_category_name or '',     # FoodCategory
                str(item.item_id),                 # ItemID
                item.name_ru or '',                # NameRus
                '',                                # DisplayOrder (empty, integer possible to fill)
                '00:00:00',                        # StartAt (always prefilled)
                '23:59:59'                         # EndAt (always prefilled)
            ])
        
        # Generate CATEGORY rows (sorted for consistency)
        for category in sorted(categories):
            csv_rows.append([
                'CATEGORY',                        # WhatSort
                category,                          # FoodCategory
                '',                                # ItemID (empty for categories)
                '',                                # NameRus (empty for categories)
                '',                                # DisplayOrder (empty, integer possible to fill)
                '00:00:00',                        # StartAt (always prefilled)
                '23:59:59'                         # EndAt (always prefilled)
            ])
        
        return csv_rows

    async def get_menu_export_statistics(self, db: Session) -> dict:
        """
        Get statistics about items and categories available for menu export
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with export statistics
        """
        try:
            return menu_preparation_db_crud.get_menu_export_statistics(db)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting menu export statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving menu export statistics"
            )


# Create a singleton instance
menu_preparation_logic = MenuPreparationLogic()