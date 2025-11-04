# GetAvailableItemsForKioskDBCRUD.py
# Database CRUD operations for retrieving available items for kiosk menu
# Returns only active items with stock quantity > 0

from sqlalchemy.orm import Session, joinedload
from typing import List, Tuple, Optional
from datetime import time
from ..database.models import ItemLive, ItemLiveAvailable, MenuItem, Menu

class GetAvailableItemsForKioskDBCRUD:
    """
    Database CRUD operations for retrieving available menu items for kiosk display.

    Filters items to show only:
    - Active items (is_active = True)
    - Non-archived items (is_archived = False)
    - Items with available stock (stock_quantity > 0)
    """

    def get_available_items_for_kiosk(self, db: Session) -> List[Tuple[ItemLive, int, Optional[time], Optional[time]]]:
        """
        Get all active, non-archived items that are in the active menu and have stock available.

        Returns ALL items in active menu with their time restrictions (no time filtering here).
        Frontend will filter by time client-side for real-time transitions.
        If no active menu exists, returns an empty list.

        Args:
            db: Database session

        Returns:
            List of tuples: (ItemLive, display_order, start_at, end_at)
            - ItemLive: The item object with all fields and availability loaded
            - display_order: Display position within category from menu_items
            - start_at: Optional time when item starts displaying (None = all day)
            - end_at: Optional time when item stops displaying (None = all day)

            Returns empty list if no active menu exists.
            Note: Time filtering NOT applied here - frontend handles time-based visibility.
        """
        # First, get the currently active menu
        active_menu = db.query(Menu).filter(Menu.is_active == True).first()

        # If no active menu, return empty list
        if not active_menu:
            return []

        # Query items that are in the active menu
        return (
            db.query(
                ItemLive,
                MenuItem.display_order,
                MenuItem.start_at,
                MenuItem.end_at
            )
            .join(ItemLiveAvailable, ItemLive.item_id == ItemLiveAvailable.item_id)
            .join(MenuItem, ItemLive.item_id == MenuItem.item_id)
            .filter(MenuItem.menu_id == active_menu.id)
            .filter(ItemLive.is_active == True)
            .filter(ItemLive.is_archived == False)
            .filter(ItemLiveAvailable.stock_quantity > 0)
            .options(joinedload(ItemLive.availability))
            .all()
        )

# Global service instance
get_available_items_for_kiosk_db_crud = GetAvailableItemsForKioskDBCRUD()
