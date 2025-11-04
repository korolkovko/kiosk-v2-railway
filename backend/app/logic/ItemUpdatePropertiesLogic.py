# ItemUpdatePropertiesLogic.py
# Business logic for updating LiveItem properties (description, price, VAT, categories, etc.)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..models.ItemUpdatePropertiesPydanticModel import ItemUpdatePropertiesRequest, ItemUpdatePropertiesResponse
from ..services.ItemUpdatePropertiesDBCRUD import item_update_properties_db_crud
from ..services.ItemEventService import item_event_service

class ItemUpdatePropertiesLogic:
    """Business logic for updating LiveItem properties"""

    async def update_properties(
        self,
        db: Session,
        request: ItemUpdatePropertiesRequest
    ) -> ItemUpdatePropertiesResponse:
        """
        Validate references, update item properties, commit transaction, and return updated item.
        """
        try:
            # Fetch existing item
            item = item_update_properties_db_crud.get_item(db, request.item_id)
            if not item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {request.item_id} not found")

            # Validate foreign keys for categories and unit
            if request.unit_measure_name_eng is not None:
                unit = item_update_properties_db_crud.validate_unit_exists(db, request.unit_measure_name_eng)
                if not unit:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit '{request.unit_measure_name_eng}' not found")

            if request.food_category_name is not None:
                if not item_update_properties_db_crud.validate_food_category_exists(db, request.food_category_name):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Food category '{request.food_category_name}' not found")

            # Update item properties
            updated_item = item_update_properties_db_crud.update_item(db, item, request)

            # Commit transaction
            db.commit()

            # Publish SSE event to all kiosks
            await item_event_service.publish_item_properties_changed(updated_item)

            # Return updated item
            return ItemUpdatePropertiesResponse.model_validate(updated_item)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(db_err)}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

# Global logic instance
item_update_properties_logic = ItemUpdatePropertiesLogic()