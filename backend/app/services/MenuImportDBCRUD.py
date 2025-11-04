# MenuImportDBCRUD.py
# Database CRUD operations for Menu Import CSV functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
from ..database.models import ItemLive, FoodCategory, Menu, MenuCategory, MenuItem
from ..models.MenuImportPydanticModel import CsvRowData, MenuImportValidationError
from typing import List, Set, Dict, Optional, Tuple, Any
from datetime import time
import logging

logger = logging.getLogger(__name__)


class MenuImportDBCRUD:
    """Database CRUD operations for menu import functionality"""

    def validate_items_exist_and_non_archived(self, db: Session, item_ids: List[int]) -> List[MenuImportValidationError]:
        """
        Validate that all item IDs exist in items_live and are non-archived
        
        Args:
            db: Database session
            item_ids: List of item IDs to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        try:
            # Get all existing non-archived items
            existing_items = (
                db.query(ItemLive.item_id)
                .filter(
                    and_(
                        ItemLive.item_id.in_(item_ids),
                        ItemLive.is_archived == False
                    )
                )
                .all()
            )
            existing_item_ids = {item[0] for item in existing_items}
            
            # Find missing or archived items
            for item_id in item_ids:
                if item_id not in existing_item_ids:
                    errors.append(MenuImportValidationError(
                        row_number=0,  # Will be updated by caller
                        column="ItemID",
                        error_type="ITEM_NOT_FOUND_OR_ARCHIVED",
                        message=f"Item with ID {item_id} does not exist or is archived",
                        value=str(item_id)
                    ))
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error validating items: {str(e)}")
            errors.append(MenuImportValidationError(
                row_number=0,
                column="ItemID",
                error_type="DATABASE_ERROR",
                message="Database error while validating items",
                value=None
            ))
            
        return errors

    def validate_categories_exist_and_used_by_non_archived(self, db: Session, category_names: List[str]) -> List[MenuImportValidationError]:
        """
        Validate that all categories exist in food_categories and are used by non-archived items
        
        Args:
            db: Database session
            category_names: List of category names to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        try:
            # Get all existing food categories
            existing_categories = (
                db.query(FoodCategory.name)
                .filter(FoodCategory.name.in_(category_names))
                .all()
            )
            existing_category_names = {cat[0] for cat in existing_categories}
            
            # Get categories that are actually used by non-archived items
            used_categories = (
                db.query(ItemLive.food_category_name)
                .filter(
                    and_(
                        ItemLive.food_category_name.in_(category_names),
                        ItemLive.is_archived == False
                    )
                )
                .distinct()
                .all()
            )
            used_category_names = {cat[0] for cat in used_categories}
            
            # Check each category
            for category_name in category_names:
                if category_name not in existing_category_names:
                    errors.append(MenuImportValidationError(
                        row_number=0,  # Will be updated by caller
                        column="FoodCategory",
                        error_type="CATEGORY_NOT_FOUND",
                        message=f"Food category '{category_name}' does not exist",
                        value=category_name
                    ))
                elif category_name not in used_category_names:
                    errors.append(MenuImportValidationError(
                        row_number=0,  # Will be updated by caller
                        column="FoodCategory",
                        error_type="CATEGORY_NOT_USED_BY_NON_ARCHIVED",
                        message=f"Food category '{category_name}' is not used by any non-archived items",
                        value=category_name
                    ))
                    
        except SQLAlchemyError as e:
            logger.error(f"Database error validating categories: {str(e)}")
            errors.append(MenuImportValidationError(
                row_number=0,
                column="FoodCategory",
                error_type="DATABASE_ERROR",
                message="Database error while validating categories",
                value=None
            ))
            
        return errors

    def check_menu_name_exists(self, db: Session, menu_name: str) -> bool:
        """
        Check if a menu with the given name already exists
        
        Args:
            db: Database session
            menu_name: Name to check
            
        Returns:
            True if menu name exists, False otherwise
        """
        try:
            existing_menu = db.query(Menu).filter(Menu.name == menu_name).first()
            return existing_menu is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking menu name: {str(e)}")
            raise

    def create_menu_from_validated_data(
        self, 
        db: Session, 
        menu_name: str, 
        description: Optional[str],
        items_data: List[Dict[str, Any]],
        categories_data: List[Dict[str, Any]]
    ) -> Menu:
        """
        Create menu and related records from validated CSV data
        
        Args:
            db: Database session
            menu_name: Name for the new menu
            description: Optional menu description
            items_data: List of validated item data dictionaries
            categories_data: List of validated category data dictionaries
            
        Returns:
            Created Menu object
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Step 1: Create the main Menu record (inactive by default)
            new_menu = Menu(
                name=menu_name,
                description=description,
                is_active=False  # Always create as inactive
            )
            db.add(new_menu)
            db.flush()  # Get the menu ID
            
            # Step 2: Create MenuCategory records
            for category_data in categories_data:
                menu_category = MenuCategory(
                    menu_id=new_menu.id,
                    food_category_name=category_data['food_category'],
                    display_order=category_data['display_order'],
                    is_visible=True
                )
                db.add(menu_category)
            
            # Step 3: Create MenuItem records
            for item_data in items_data:
                menu_item = MenuItem(
                    menu_id=new_menu.id,
                    item_id=item_data['item_id'],
                    food_category_name=item_data['food_category'],
                    display_order=item_data['display_order'],
                    start_at=item_data['start_at'],
                    end_at=item_data['end_at']
                )
                db.add(menu_item)
            
            # Flush to catch any constraint violations before commit
            db.flush()
            
            return new_menu
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating menu: {str(e)}")
            db.rollback()
            raise

    def get_item_food_category_mapping(self, db: Session, item_ids: List[int]) -> Dict[int, str]:
        """
        Get food category mapping for given item IDs
        
        Args:
            db: Database session
            item_ids: List of item IDs
            
        Returns:
            Dictionary mapping item_id to food_category_name
        """
        try:
            items = (
                db.query(ItemLive.item_id, ItemLive.food_category_name)
                .filter(
                    and_(
                        ItemLive.item_id.in_(item_ids),
                        ItemLive.is_archived == False
                    )
                )
                .all()
            )
            return {item[0]: item[1] for item in items}
        except SQLAlchemyError as e:
            logger.error(f"Database error getting item categories: {str(e)}")
            raise

    def validate_display_orders_unique_per_category(
        self, 
        items_data: List[Dict[str, Any]], 
        categories_data: List[Dict[str, Any]]
    ) -> List[MenuImportValidationError]:
        """
        Validate that display orders are unique within each category
        
        Args:
            items_data: List of item data dictionaries
            categories_data: List of category data dictionaries
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        # Track display orders by category
        category_orders = {}
        item_orders_by_category = {}
        
        # Check category display orders
        for category_data in categories_data:
            category = category_data['food_category']
            order = category_data['display_order']
            
            if category in category_orders:
                errors.append(MenuImportValidationError(
                    row_number=category_data.get('row_number', 0),
                    column="DisplayOrder",
                    error_type="DUPLICATE_CATEGORY_DISPLAY_ORDER",
                    message=f"Duplicate display order {order} for category '{category}'",
                    value=str(order)
                ))
            else:
                category_orders[category] = order
        
        # Check item display orders within categories
        for item_data in items_data:
            category = item_data['food_category']
            order = item_data['display_order']
            
            if category not in item_orders_by_category:
                item_orders_by_category[category] = set()
            
            if order in item_orders_by_category[category]:
                errors.append(MenuImportValidationError(
                    row_number=item_data.get('row_number', 0),
                    column="DisplayOrder",
                    error_type="DUPLICATE_ITEM_DISPLAY_ORDER",
                    message=f"Duplicate display order {order} for items in category '{category}'",
                    value=str(order)
                ))
            else:
                item_orders_by_category[category].add(order)
        
        return errors


# Create a singleton instance
menu_import_db_crud = MenuImportDBCRUD()