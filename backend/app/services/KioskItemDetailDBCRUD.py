# KioskItemDetailDBCRUD.py
# Database CRUD operations for retrieving individual item details for kiosk

from sqlalchemy.orm import Session, joinedload
from typing import Optional, Tuple
from datetime import time
from ..database.models import ItemLive, ItemLiveAvailable, MenuItem, Menu

class KioskItemDetailDBCRUD:
    """
    Database CRUD operations for retrieving individual item details for kiosk display.
    
    Used when SSE updates reference items that weren't in the initial
    available items list (e.g., items that had 0 stock initially but now have stock > 0).
    """

    def get_item_by_id(self, db: Session, item_id: int) -> Optional[Tuple[ItemLive, int, Optional[time], Optional[time]]]:
        """
        Get a specific item by ID with its availability and menu information.

        Returns the item only if it's in the active menu, is active, not archived, AND has stock quantity > 0.
        Eagerly loads availability information to avoid N+1 query issues.
        Returns None if no active menu exists or item is not in active menu.

        Args:
            db: Database session
            item_id: The ID of the item to retrieve

        Returns:
            Tuple of (ItemLive, display_order, start_at, end_at) if found, or None if:
            - Item not found
            - Item not in active menu
            - No active menu exists
            - Item is archived or inactive
            - Item has no stock
        """
        # First, get the currently active menu
        active_menu = db.query(Menu).filter(Menu.is_active == True).first()

        # If no active menu, return None
        if not active_menu:
            return None

        # Query item that is in the active menu
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
            .filter(ItemLive.item_id == item_id)
            .filter(ItemLive.is_active == True)
            .filter(ItemLive.is_archived == False)
            .filter(ItemLiveAvailable.stock_quantity > 0)
            .options(joinedload(ItemLive.availability))
            .first()
        )

# Global service instance
kiosk_item_detail_db_crud = KioskItemDetailDBCRUD()