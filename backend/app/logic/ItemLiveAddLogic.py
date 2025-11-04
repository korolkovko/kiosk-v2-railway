# ItemLiveAddLogic.py
# Business logic for LiveItem creation (external price input)
# NOTE: This layer manages full transaction: validation → creation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.ItemLiveAddPydanticModel import ItemLiveCreateRequest, ItemLiveResponse
from ..services.ItemLiveAddDBCRUD import item_live_add_db_crud
from ..services.ItemEventService import item_event_service
from sqlalchemy.exc import SQLAlchemyError


class ItemLiveAddLogic:
    """Business logic for creating LiveItem (no price calculation)"""

    async def create_live_item(self, db: Session, item_data: ItemLiveCreateRequest,
                               created_by: int) -> ItemLiveResponse:
        """
        Main logic flow:
        1. Validate foreign keys
        2. Check uniqueness
        3. Create item
        4. Create availability
        5. Commit all changes in one transaction

        Rollback is triggered automatically on any error.
        """
        try:
            # Step 1: Validate references
            unit = item_live_add_db_crud.validate_unit_exists(db, item_data.unit_measure_name_eng)
            if not unit:
                raise HTTPException(status_code=400, detail=f"Unit '{item_data.unit_measure_name_eng}' not found")

            if not item_live_add_db_crud.validate_food_category_exists(db, item_data.food_category_name):
                raise HTTPException(status_code=400, detail=f"Food category '{item_data.food_category_name}' not found")

            # Step 2: Business rules
            if item_live_add_db_crud.check_item_name_exists(db, item_data.name_ru):
                raise HTTPException(status_code=409, detail=f"Item '{item_data.name_ru}' already exists")

            # Step 3: Create item
            item = item_live_add_db_crud.create_item_live(
                db=db,
                item_data=item_data,
                created_by=created_by,
                vat_amount_kopecks=item_data.vat_amount_kopecks,
                price_gross_kopecks=item_data.price_gross_kopecks
            )

            # Step 4: Create availability with snapshot
            item_live_add_db_crud.create_item_available(db=db, item=item, unit=unit)

            # Step 5: Commit transaction
            db.commit()

            # Step 6: Publish SSE event to all kiosks (with initial stock 0)
            await item_event_service.publish_item_created(item, stock_quantity=0)

            # Step 7: Return response
            return ItemLiveResponse.model_validate(item)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# Global logic instance
item_live_add_logic = ItemLiveAddLogic()