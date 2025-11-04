# GetAllItemsAndCategoriesFromMenuForPreloadLogic.py
# Business logic for retrieving ALL items and categories from active menu for media preload

from typing import Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..services.GetAllItemsAndCategoriesFromMenuForPreloadDBCRUD import get_all_items_and_categories_from_menu_for_preload_db_crud
from ..database.models import User

class GetAllItemsAndCategoriesFromMenuForPreloadLogic:
    """
    Business logic for retrieving ALL items and categories from active menu for media preloading.

    Returns ALL items and categories regardless of stock or availability.
    Used at login to cache media for items that might become available via SSE updates.
    """

    async def get_all_items_and_categories_from_menu_for_preload(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, List]:
        """
        Get ALL item IDs and category names from active menu for media preloading.

        NO filters applied - returns everything in the active menu regardless of:
        - Stock quantity
        - Availability status
        - Active/archived status

        Purpose: Ensures kiosk has cached media for all items that might appear
        during the session when stock is replenished via SSE updates.

        Args:
            db: Database session
            current_user: Authenticated kiosk user (for audit trail)

        Returns:
            Dict with keys:
            - 'item_ids': List[int] - All item IDs in active menu
            - 'category_names': List[str] - All category names in active menu

            Returns empty lists if no active menu exists.

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            return get_all_items_and_categories_from_menu_for_preload_db_crud.get_all_items_and_categories_from_menu_for_preload(db)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve menu items for preload: {str(e)}"
            )

# Global logic instance
get_all_items_and_categories_from_menu_for_preload_logic = GetAllItemsAndCategoriesFromMenuForPreloadLogic()
