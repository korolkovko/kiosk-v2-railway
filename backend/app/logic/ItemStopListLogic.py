# ItemStopListLogic.py
# Business logic for updating LiveItem stop list status

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..models.ItemStopListPydanticModel import ItemStopListRequest, ItemStopListResponse
from ..services.ItemStopListDBCRUD import item_stop_list_db_crud
from ..services.ItemEventService import item_event_service

class ItemStopListLogic:
    """Business logic for updating LiveItem stop list status"""

    async def update_status(
        self,
        db: Session,
        request: ItemStopListRequest
    ) -> ItemStopListResponse:
        try:
            # Fetch the item
            item = item_stop_list_db_crud.get_item(db, request.item_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {request.item_id} not found"
                )

            # If requested status is same as current, nothing to change
            if item.is_active == request.is_active:
                db.commit()
                return ItemStopListResponse.model_validate(item)

            # Update status
            updated_item = item_stop_list_db_crud.update_status(db, item, request.is_active)
            db.commit()

            # Publish SSE event to all kiosks
            await item_event_service.publish_item_status_changed(updated_item)

            return ItemStopListResponse.model_validate(updated_item)

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
item_stop_list_logic = ItemStopListLogic()