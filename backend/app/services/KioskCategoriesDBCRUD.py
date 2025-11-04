# KioskCategoriesDBCRUD.py
# Database CRUD operations for kiosk categories functionality
# Provides data access layer for food categories retrieval

from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import asc

from ..database.models import FoodCategory, MenuCategory, Menu


class KioskCategoriesDBCRUD:
    """
    Database CRUD operations for kiosk categories
    
    Handles all database operations related to food categories
    for kiosk menu display functionality.
    """
    
    @staticmethod
    def get_all_food_categories(db: Session) -> List[Tuple[FoodCategory, int]]:
        """
        Retrieve all food categories that are in the active menu

        Returns categories filtered by active menu with their display order.
        If no active menu exists, returns an empty list.

        Args:
            db: Database session

        Returns:
            List[Tuple[FoodCategory, display_order]]: List of tuples containing:
                - FoodCategory: The category object
                - display_order: Display position from menu_categories
            Returns empty list if no active menu.

        Raises:
            SQLAlchemyError: If database query fails
        """
        # First, get the currently active menu
        active_menu = db.query(Menu).filter(Menu.is_active == True).first()

        # If no active menu, return empty list
        if not active_menu:
            return []

        # Query categories that are in the active menu
        return (
            db.query(
                FoodCategory,
                MenuCategory.display_order
            )
            .join(MenuCategory, FoodCategory.name == MenuCategory.food_category_name)
            .filter(MenuCategory.menu_id == active_menu.id)
            .filter(MenuCategory.is_visible == True)
            .order_by(asc(MenuCategory.display_order))
            .all()
        )
    
    @staticmethod
    def get_categories_count(db: Session) -> int:
        """
        Get total count of food categories
        
        Args:
            db: Database session
            
        Returns:
            int: Total number of food categories
            
        Raises:
            SQLAlchemyError: If database query fails
        """
        return db.query(FoodCategory).count()


# Create singleton instance for dependency injection
kiosk_categories_db_crud = KioskCategoriesDBCRUD()