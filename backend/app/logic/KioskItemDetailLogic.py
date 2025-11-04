# KioskItemDetailLogic.py
# Business logic for retrieving individual item details for kiosk

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.KioskAvailableItemsResponseModel import KioskAvailableItemResponse
from ..services.KioskItemDetailDBCRUD import kiosk_item_detail_db_crud
from ..database.models import User

class KioskItemDetailLogic:
    """
    Business logic for retrieving individual item details for kiosk display.
    
    Used when SSE updates reference items that weren't in the initial
    available items list (e.g., items that had 0 stock initially).
    """

    async def get_kiosk_item_detail(
        self,
        db: Session,
        item_id: int,
        current_user: User
    ) -> KioskAvailableItemResponse:
        """
        Get detailed information for a specific item by ID.

        Returns item details only if the item is in the active menu.
        Returns 404 if no active menu exists or item is not in the menu.

        Args:
            db: Database session
            item_id: The ID of the item to retrieve
            current_user: Authenticated kiosk user (for audit trail)

        Returns:
            KioskAvailableItemResponse with current item details, stock, and menu info

        Raises:
            HTTPException 404: If item not found, not in active menu, or no active menu exists
            HTTPException 500: If database operation fails
        """
        try:
            result = kiosk_item_detail_db_crud.get_item_by_id(db, item_id)

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with ID {item_id} not found or not available in current menu"
                )

            # Unpack the tuple
            item, display_order, start_at, end_at = result

            # Return item details with current stock quantity and menu info
            return KioskAvailableItemResponse(
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
                stock_quantity=item.availability.stock_quantity if item.availability else 0,
                display_order=display_order,
                start_at=start_at,
                end_at=end_at
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve item details: {str(e)}"
            )

# Global logic instance
kiosk_item_detail_logic = KioskItemDetailLogic()