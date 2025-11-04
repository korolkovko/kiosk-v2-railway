# GetAllItemLiveLogic.py
# Business logic for retrieving all LiveItems

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.ItemLiveAddPydanticModel import ItemLiveResponse
from ..services.GetAllItemLiveDBCRUD import get_all_item_live_db_crud
from ..auth.dependencies import get_current_user
from ..database.models import User

class GetAllItemLiveLogic:
    """Business logic for retrieving all LiveItems"""

    async def get_all_live_items(self, db: Session, current_user: User) -> List[ItemLiveResponse]:
        try:
            items = get_all_item_live_db_crud.get_all_item_live(db)
            return [ItemLiveResponse.model_validate(item) for item in items]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve items: {str(e)}"
            )

# Global logic instance
get_all_item_live_logic = GetAllItemLiveLogic()