# KioskCategoriesEndpoint.py
# FastAPI endpoint for retrieving food categories for kiosk menu display
# Provides dedicated API route for kiosk to fetch menu categories

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models.KioskCategoriesResponseModel import KioskCategoriesListResponse
from ..auth.kiosk_dependencies import get_current_kiosk_user
from ..logic.KioskCategoriesLogic import kiosk_categories_logic
from ..database.models import User

router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Menu"]
)

@router.get(
    "/categories",
    response_model=KioskCategoriesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all food categories for kiosk with synthetic promoted",
    description="Retrieve unified category list with synthetic promoted category at index 0. Only authenticated kiosk users can access this endpoint."
)
async def get_categories_for_kiosk(
    current_user: User = Depends(get_current_kiosk_user),
    db: Session = Depends(get_db)
):
    """
    Get unified category list with synthetic promoted category at position 0.

    Returns a unified structure where:
    - Index [0]: Synthetic promoted category (from promoted_label table)
    - Index [1+]: Regular categories (from menu_categories, display_order shifted by +1)

    The promoted category is synthetic - doesn't exist in food_categories table.
    All categories include optional ru_label/en_label for i18n support.

    Authentication:
    - Requires kiosk user authentication (kiosk role)
    - Uses dedicated kiosk JWT tokens

    Args:
        current_user: Authenticated kiosk user (injected by dependency)
        db: Database session (injected by dependency)

    Returns:
        KioskCategoriesListResponse: Unified list with synthetic promoted + regular categories

    Raises:
        HTTPException 401: If authentication fails or user is not a kiosk
        HTTPException 403: If user is inactive
        HTTPException 500: If database query fails
    """
    try:
        return await kiosk_categories_logic.get_all_categories_with_synthetic_promoted(
            db=db,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories with synthetic promoted: {str(e)}"
        )