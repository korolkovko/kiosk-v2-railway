# ItemLiveAddEndPoint.py
# API endpoint for creating LiveItem

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.ItemLiveAddPydanticModel import ItemLiveCreateRequest, ItemLiveResponse
from ..auth.dependencies import get_current_admin
from ..logic.ItemLiveAddLogic import item_live_add_logic
from ..database.models import User

router = APIRouter(
    prefix="/addliveitem",
    tags=["item-management"]
)

@router.post(
    "/",
    response_model=ItemLiveResponse,
    status_code=201,
    summary="Create new LiveItem",
    description="Create a new active menu item (LiveItem). Only accessible by Admin or SuperAdmin."
)
async def create_live_item(
    item_data: ItemLiveCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new LiveItem (admin only).
    """
    try:
        return await item_live_add_logic.create_live_item(
            db=db,
            item_data=item_data,
            created_by=current_user.user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )