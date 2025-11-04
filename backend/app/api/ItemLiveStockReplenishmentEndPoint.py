# ItemLiveStockReplenishmentEndPoint.py
# API endpoint for stock replenishment or removal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.dependencies import get_current_admin
from ..models.ItemLiveStockReplenishmentPydanticModel import (
    ItemLiveStockReplenishmentRequest,
    ItemLiveStockReplenishmentResponse
)
from ..logic.ItemLiveStockReplenishmentLogic import item_live_stock_replenishment_logic
from ..database.models import User

router = APIRouter(
    prefix="/replenish-or-remove",
    tags=["item-management"]
)

@router.post(
    "/",
    response_model=ItemLiveStockReplenishmentResponse,
    status_code=200,
    summary="Replenish or remove stock",
    description="Adjust stock quantity by positive or negative amount; only Admin or SuperAdmin."
)
async def replenish_or_remove_stock(
    request: ItemLiveStockReplenishmentRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Adjust stock for a LiveItem. Positive quantity replenishes, negative removes.
    """
    try:
        return await item_live_stock_replenishment_logic.replenish_or_remove(
            db=db,
            request=request,
            changed_by_username=current_user.username  # Changed from user_id to username
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adjust stock: {str(e)}"
        )