# GetAvailableItemsForKioskLogic.py
# Business logic for retrieving available items for kiosk menu display

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.KioskAvailableItemsResponseModel import KioskAvailableItemResponse
from ..services.GetAvailableItemsForKioskDBCRUD import get_available_items_for_kiosk_db_crud
from ..database.models import User

class GetAvailableItemsForKioskLogic:
    """
    Business logic for retrieving available menu items for kiosk display.

    Returns only active items with stock available (stock_quantity > 0),
    formatted for customer-facing kiosk menu.
    """

    async def get_available_items_for_kiosk(
        self,
        db: Session,
        current_user: User
    ) -> List[KioskAvailableItemResponse]:
        """
        Get list of available items for kiosk menu filtered by active menu.

        Filters:
        - Only items in active menu
        - Only active items (is_active = True)
        - Only items with stock (stock_quantity > 0)

        Args:
            db: Database session
            current_user: Authenticated kiosk user (for audit trail)

        Returns:
            List of KioskAvailableItemResponse objects with stock quantity and menu display info.
            Returns empty list if no active menu exists.

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            items_with_menu_info = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db)

            # Unpack tuples (item, display_order, start_at, end_at) and construct response
            return [
                KioskAvailableItemResponse(
                    item_id=item.item_id,
                    name_ru=item.name_ru,
                    name_eng=item.name_eng,
                    description_ru=item.description_ru,
                    description_eng=item.description_eng,
                    unit_measure_name_eng=item.unit_measure_name_eng,
                    food_category_name=item.food_category_name,
                    price_net_kopecks=item.price_net_kopecks,
                    vat_rate=item.vat_rate,
                    vat_amount_kopecks=item.vat_amount_kopecks,
                    price_gross_kopecks=item.price_gross_kopecks,
                    is_active=item.is_active,
                    promoted=item.promoted,
                    stock_quantity=item.availability.stock_quantity,
                    display_order=display_order,
                    start_at=start_at,
                    end_at=end_at
                )
                for item, display_order, start_at, end_at in items_with_menu_info
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve available items: {str(e)}"
            )

# Global logic instance
get_available_items_for_kiosk_logic = GetAvailableItemsForKioskLogic()
