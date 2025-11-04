# GetAllItemsAndCategoriesFromMenuForPreloadDBCRUD.py
# Database CRUD operations for retrieving ALL items and categories in active menu for media preload
# Returns ALL items and categories in menu regardless of stock or availability (for media caching)

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ..database.models import MenuItem, MenuCategory, Menu, PromotedLabel

class GetAllItemsAndCategoriesFromMenuForPreloadDBCRUD:
    """
    Database CRUD operations for retrieving ALL menu items and categories for media preload.

    Returns ALL items and categories in active menu regardless of:
    - Stock quantity (even if stock_quantity = 0)
    - Availability status
    - Active/archived status

    Purpose: Used at login to download ALL media files for items and categories
    that might become available during the session via SSE updates.
    """

    def get_all_items_and_categories_from_menu_for_preload(self, db: Session) -> Dict[str, List]:
        """
        Get ALL item IDs and category names from the active menu for media preloading.

        Returns ALL items and categories in active menu regardless of stock or availability.
        This ensures media is cached even for items that might get restocked
        during the kiosk session (via SSE updates).

        Args:
            db: Database session

        Returns:
            Dict with keys:
            - 'item_ids': List[int] - List of all item IDs in the active menu
            - 'category_names': List[str] - List of all category names in the active menu

            Returns {'item_ids': [], 'category_names': []} if no active menu exists.
        """
        # First, get the currently active menu
        active_menu = db.query(Menu).filter(Menu.is_active == True).first()

        # If no active menu, return empty lists
        if not active_menu:
            return {'item_ids': [], 'category_names': []}

        # Query ALL items in the active menu (no filters for stock/availability)
        menu_items = (
            db.query(MenuItem.item_id)
            .filter(MenuItem.menu_id == active_menu.id)
            .distinct()
            .all()
        )

        # Query ALL categories in the active menu
        menu_categories = (
            db.query(MenuCategory.food_category_name)
            .filter(MenuCategory.menu_id == active_menu.id)
            .filter(MenuCategory.is_visible == True)
            .distinct()
            .all()
        )

        # Extract IDs and names from tuples
        item_ids = [item_id for (item_id,) in menu_items]
        regular_category_names = [food_category_name for (food_category_name,) in menu_categories]

        # Query promoted label to get synthetic promoted category name
        promoted_label_record = db.query(PromotedLabel).filter(
            PromotedLabel.name == "promoted"
        ).first()

        # Get synthetic promoted category name (defaults to "promoted" if not found)
        synthetic_promoted_name = promoted_label_record.name if promoted_label_record else "promoted"

        # Build unified category_names array: synthetic promoted first, then regular categories
        # This matches the structure returned by /kiosk/categories endpoint
        unified_category_names = [synthetic_promoted_name] + regular_category_names

        return {
            'item_ids': item_ids,
            'category_names': unified_category_names  # Now includes synthetic promoted at [0]
        }

# Global service instance
get_all_items_and_categories_from_menu_for_preload_db_crud = GetAllItemsAndCategoriesFromMenuForPreloadDBCRUD()
