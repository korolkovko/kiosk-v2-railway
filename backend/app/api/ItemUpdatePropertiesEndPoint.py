# ItemUpdatePropertiesEndPoint.py
# API endpoint for updating LiveItem properties (description, price, VAT, categories, etc.)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.dependencies import get_current_admin
from ..models.ItemUpdatePropertiesPydanticModel import (
    ItemUpdatePropertiesRequest,
    ItemUpdatePropertiesResponse
)
from ..logic.ItemUpdatePropertiesLogic import item_update_properties_logic
from ..database.models import User

router = APIRouter(
    prefix="/update-item-properties",
    tags=["item-management"]
)

@router.put(
    "/",
    response_model=ItemUpdatePropertiesResponse,
    status_code=200,
    summary="Update LiveItem properties",
    description="Update properties of an existing LiveItem (description, price, VAT, categories, etc.). Only accessible by Admin or SuperAdmin."
)
async def update_item_properties(
    request: ItemUpdatePropertiesRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update properties of a LiveItem (admin only).
    """
    try:
        return await item_update_properties_logic.update_properties(
            db=db,
            request=request
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item properties: {str(e)}"
        )