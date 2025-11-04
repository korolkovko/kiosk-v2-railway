# KioskItemDetailEndpoint.py
# API endpoint for retrieving individual item details for kiosk

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..auth.kiosk_dependencies import get_current_kiosk_user
from ..database.models import User
from ..models.KioskAvailableItemsResponseModel import KioskAvailableItemResponse
from ..logic.KioskItemDetailLogic import kiosk_item_detail_logic

router = APIRouter(prefix="/kiosk", tags=["Kiosk Item Detail"])


@router.get("/items/{item_id}", response_model=KioskAvailableItemResponse)
async def get_kiosk_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user)
):
    """
    Get detailed information for a specific item by ID.
    
    This endpoint is used when SSE updates reference items that weren't
    in the initial available items list (e.g., items that had 0 stock
    when kiosk first loaded but now have stock).
    
    Args:
        item_id: The ID of the item to retrieve
        db: Database session
        current_user: Authenticated kiosk user
        
    Returns:
        KioskAvailableItemResponse with current item details and stock
        
    Raises:
        HTTPException: If item not found or not accessible to kiosk
    """
    return await kiosk_item_detail_logic.get_kiosk_item_detail(
        db=db,
        item_id=item_id,
        current_user=current_user
    )