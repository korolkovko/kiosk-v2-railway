# GetAllItemLiveEndPoint.py
# API endpoint for retrieving all LiveItems

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.ItemLiveAddPydanticModel import ItemLiveResponse
from ..auth.dependencies import get_current_user
from ..logic.GetAllItemLiveLogic import get_all_item_live_logic
from ..database.models import User

router = APIRouter(
    prefix="/getallitemlive",
    tags=["item-management"]
)

@router.get(
    "/",
    response_model=List[ItemLiveResponse],
    status_code=200,
    summary="Get all LiveItems",
    description="Retrieve list of all LiveItems. Accessible by any authenticated user."
)
async def get_all_item_live(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all LiveItems.
    """
    try:
        return await get_all_item_live_logic.get_all_live_items(db=db, current_user=current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve items: {str(e)}"
        )