# AllItemsAndCategoriesFromMenuForPreloadEndpoint.py
# FastAPI endpoint for retrieving ALL items and categories from active menu for media preload
# Used at kiosk login to cache media files for items that might become available via SSE

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.AllItemsAndCategoriesFromMenuForPreloadResponseModel import AllItemsAndCategoriesFromMenuForPreloadResponse
from ..auth.kiosk_dependencies import get_current_kiosk_user
from ..logic.GetAllItemsAndCategoriesFromMenuForPreloadLogic import get_all_items_and_categories_from_menu_for_preload_logic
from ..database.models import User

router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Menu"]
)

@router.get(
    "/menu/all-for-preload",
    response_model=AllItemsAndCategoriesFromMenuForPreloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all items and categories from menu for media preload",
    description="Retrieve ALL item IDs and category names from active menu for media preloading. Returns items regardless of stock or availability. Only authenticated kiosk users can access this endpoint."
)
async def get_all_items_and_categories_from_menu_for_preload(
    current_user: User = Depends(get_current_kiosk_user),
    db: Session = Depends(get_db)
):
    """
    Get ALL item IDs and category names from active menu for media preloading.

    This endpoint returns ALL items and categories in the active menu regardless of:
    - Stock quantity (includes items with stock_quantity = 0)
    - Availability status
    - Active/archived status

    Purpose:
    - Called at kiosk login to download and cache ALL media files
    - Ensures media is available for items that might get restocked during session
    - Items become visible via SSE updates when stock is replenished
    - Without this preload, newly available items would have no poster image

    Authentication:
    - Requires kiosk user authentication (kiosk role)
    - Uses dedicated kiosk JWT tokens

    Args:
        current_user: Authenticated kiosk user (injected by dependency)
        db: Database session (injected by dependency)

    Returns:
        AllItemsAndCategoriesFromMenuForPreloadResponse:
            - item_ids: List of all item IDs in active menu
            - category_names: List of all category names in active menu
            Returns empty lists if no active menu exists.

    Raises:
        HTTPException 401: If authentication fails or user is not a kiosk
        HTTPException 500: If database query fails
    """
    try:
        result = await get_all_items_and_categories_from_menu_for_preload_logic.get_all_items_and_categories_from_menu_for_preload(
            db=db,
            current_user=current_user
        )
        return AllItemsAndCategoriesFromMenuForPreloadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menu items for preload: {str(e)}"
        )
