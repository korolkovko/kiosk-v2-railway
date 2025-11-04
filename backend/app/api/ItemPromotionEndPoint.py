# ItemPromotionEndPoint.py
# API endpoint for toggling LiveItem promotion status

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.dependencies import get_current_admin
from ..models.ItemPromotionPydanticModel import (
    ItemPromotionRequest,
    ItemPromotionResponse
)
from ..logic.ItemPromotionLogic import item_promotion_logic
from ..database.models import User

router = APIRouter(
    prefix="/item-promotion-toggle",
    tags=["item-management"]
)

@router.put(
    "/",
    response_model=ItemPromotionResponse,
    status_code=200,
    summary="Toggle LiveItem promotion status",
    description="Toggle promotion status of an existing LiveItem. Only accessible by Admin or SuperAdmin."
)
async def toggle_item_promotion(
    request: ItemPromotionRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Toggle promotion status of a LiveItem (admin only).
    """
    try:
        return await item_promotion_logic.toggle_item_promotion(
            db=db,
            request=request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle item promotion: {str(e)}"
        )