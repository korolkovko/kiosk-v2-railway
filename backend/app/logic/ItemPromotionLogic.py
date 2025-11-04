# ItemPromotionLogic.py
# Business logic for item promotion toggle functionality

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..models.ItemPromotionPydanticModel import ItemPromotionRequest, ItemPromotionResponse
from ..services.ItemPromotionDBCRUD import item_promotion_db_crud
from ..services.ItemEventService import item_event_service

class ItemPromotionLogic:
    """Business logic for item promotion management"""

    async def toggle_item_promotion(
        self,
        db: Session,
        request: ItemPromotionRequest
    ) -> ItemPromotionResponse:
        """
        Toggle item promotion status with validation and transaction management.
        """
        try:
            # Fetch existing item
            item = item_promotion_db_crud.get_item_by_id(db, request.item_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Item {request.item_id} not found"
                )

            # Update promotion status
            updated_item = item_promotion_db_crud.update_item_promotion_status(
                db, item, request.promoted
            )

            # Commit transaction
            db.commit()

            # Publish SSE event to all kiosks
            await item_event_service.publish_item_promotion_changed(updated_item)

            # Return updated item
            return ItemPromotionResponse.model_validate(updated_item)

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
item_promotion_logic = ItemPromotionLogic()