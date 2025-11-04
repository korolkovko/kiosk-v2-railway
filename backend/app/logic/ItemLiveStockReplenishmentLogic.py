# ItemLiveStockReplenishmentLogic.py
# Business logic for stock replenishment or removal

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..models.ItemLiveStockReplenishmentPydanticModel import (
    ItemLiveStockReplenishmentRequest,
    ItemLiveStockReplenishmentResponse
)
from ..services.ItemLiveStockReplenishmentDBCRUD import item_live_stock_replenishment_db_crud
from ..services.ItemEventService import item_event_service

class ItemLiveStockReplenishmentLogic:
    """Business logic for LiveItem stock replenishment/removal"""

    async def replenish_or_remove(
        self,
        db: Session,
        request: ItemLiveStockReplenishmentRequest,
        changed_by_username: str
    ) -> ItemLiveStockReplenishmentResponse:
        """
        Adjust stock by positive (replenish) or negative (remove) quantity.
        Ensures stock_quantity never goes below zero.
        Logs each operation.
        
        Args:
            db: Database session
            request: Stock replenishment request
            changed_by_username: Username or identifier of who made the change
                                (e.g., 'admin_user', 'SYSTEM', 'KIOSK_AUTO_DEDUCTION')
        """
        try:
            # Fetch current availability
            availability = item_live_stock_replenishment_db_crud.get_item_available(db, request.item_id)
            if not availability:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Availability for item {request.item_id} not found"
                )

            # Compute effective change
            initial_qty = availability.stock_quantity
            change_qty = request.quantity
            if change_qty < 0 and abs(change_qty) > initial_qty:
                effective_change = -initial_qty
            else:
                effective_change = change_qty

            new_qty = initial_qty + effective_change

            # Update availability
            updated_availability = item_live_stock_replenishment_db_crud.update_stock_quantity(
                db, availability, new_qty
            )

            # Log stock change (use original requested change for record)
            log_entry = item_live_stock_replenishment_db_crud.create_stock_replenishment(
                db, updated_availability, change_qty, changed_by_username
            )

            # Commit transaction
            db.commit()

            # Publish SSE event to all kiosks
            await item_event_service.publish_item_stock_changed(
                updated_availability, change_qty, changed_by_username
            )

            # Prepare response
            return ItemLiveStockReplenishmentResponse.model_validate({
                "item_id": updated_availability.item_id,
                "unit_name_ru": updated_availability.unit_name_ru,
                "unit_name_eng": updated_availability.unit_name_eng,
                "stock_quantity": updated_availability.stock_quantity,
                "reserved_quantity": updated_availability.reserved_quantity,
                "operation_id": log_entry.operation_id,
                "changed_at": log_entry.changed_at
            })

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(db_err)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )

# Global logic instance
item_live_stock_replenishment_logic = ItemLiveStockReplenishmentLogic()