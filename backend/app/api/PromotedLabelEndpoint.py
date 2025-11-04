# PromotedLabelEndpoint.py
# FastAPI endpoints for Promoted Label (single-record configuration)
# NOTE: This is NOT a category. It is only for displaying the name of promoted items.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..auth.dependencies import get_current_admin
from ..logic.PromotedLabelLogic import promoted_label_logic
from ..models.PromotedLabelModels import (
    PromotedLabelCreateRequest,
    PromotedLabelUpdateRequest,
    PromotedLabelResponse,
)
from ..database.models import User

# Use Category Management tag and categories prefix to align with current patterns
router = APIRouter(
    prefix="/categories",
    tags=["Category Management"]
)


@router.post(
    "/promoted-label/create",
    response_model=PromotedLabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Promoted Label",
    description="""Create the Promoted Label configuration record (single-record table).

IMPORTANT:
- This is NOT a category; it is only used to display a label for promoted items.
- Table is expected to contain only one record globally. Creation will fail if a record already exists.
- Accessible only by Admin or SuperAdmin users.
"""
)
async def create_promoted_label(
    payload: PromotedLabelCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create Promoted Label - Admin only.

    The table is intended to hold a single configuration record.
    """
    try:
        return await promoted_label_logic.create_label(
            db=db,
            data=payload,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create promoted label: {str(e)}"
        )


@router.put(
    "/promoted-label/edit",
    response_model=PromotedLabelResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit Promoted Label",
    description="""Edit the Promoted Label configuration record by primary key 'name'.

IMPORTANT:
- This is NOT a category; it is only used to display a label for promoted items.
- Table is expected to contain only one record globally.
- Accessible only by Admin or SuperAdmin users.
"""
)
async def edit_promoted_label(
    payload: PromotedLabelUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Edit Promoted Label - Admin only.

    Edits labels for the single configuration record.
    """
    try:
        return await promoted_label_logic.edit_label(
            db=db,
            data=payload,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit promoted label: {str(e)}"
        )