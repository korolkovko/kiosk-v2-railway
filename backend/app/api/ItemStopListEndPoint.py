# ItemStopListEndPoint.py
# API endpoint for updating LiveItem stop list status

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.dependencies import get_current_admin
from ..models.ItemStopListPydanticModel import ItemStopListRequest, ItemStopListResponse
from ..logic.ItemStopListLogic import item_stop_list_logic
from ..database.models import User

router = APIRouter(
    prefix="/stop-list",
    tags=["item-management"]
)

@router.put(
    "/",
    response_model=ItemStopListResponse,
    status_code=200,
    summary="Update LiveItem stop list status",
    description="Update the stop list status of a LiveItem. Only accessible by Admin or SuperAdmin."
)
async def update_item_stop_list(
    request: ItemStopListRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update the active status of a LiveItem.
    """
    try:
        return await item_stop_list_logic.update_status(
            db=db,
            request=request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item stop list status: {str(e)}"
        )