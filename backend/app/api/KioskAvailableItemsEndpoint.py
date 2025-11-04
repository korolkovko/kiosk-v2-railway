# KioskAvailableItemsEndpoint.py
# FastAPI endpoint for retrieving available items for kiosk menu display
# Provides dedicated API route for kiosk to fetch menu items with stock

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.KioskAvailableItemsResponseModel import KioskAvailableItemResponse
from ..auth.kiosk_dependencies import get_current_kiosk_user
from ..logic.GetAvailableItemsForKioskLogic import get_available_items_for_kiosk_logic
from ..database.models import User

router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Menu"]
)

@router.get(
    "/items/available",
    response_model=List[KioskAvailableItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get available menu items for kiosk",
    description="Retrieve list of active menu items with available stock for kiosk display. Only authenticated kiosk users can access this endpoint."
)
async def get_available_items_for_kiosk(
    current_user: User = Depends(get_current_kiosk_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available menu items for kiosk display.

    This endpoint returns only:
    - Active items (is_active = True)
    - Items with stock available (stock_quantity > 0)

    Items are returned with full details including pricing, descriptions,
    and category information for menu display.

    Authentication:
    - Requires kiosk user authentication (kiosk role)
    - Uses dedicated kiosk JWT tokens

    Args:
        current_user: Authenticated kiosk user (injected by dependency)
        db: Database session (injected by dependency)

    Returns:
        List[KioskAvailableItemResponse]: List of available menu items with stock quantities

    Raises:
        HTTPException 401: If authentication fails or user is not a kiosk
        HTTPException 500: If database query fails
    """
    try:
        return await get_available_items_for_kiosk_logic.get_available_items_for_kiosk(
            db=db,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available items: {str(e)}"
        )
