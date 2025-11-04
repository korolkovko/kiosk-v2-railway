# PromotedLabelLogic.py
# Business logic for Promoted Label (single-record configuration)
# NOTE: This layer manages full transaction: validation → create/update → commit/rollback
# IMPORTANT: This is NOT a category. It is only for displaying the name of promoted items.

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..models.PromotedLabelModels import (
    PromotedLabelCreateRequest,
    PromotedLabelUpdateRequest,
    PromotedLabelResponse,
)
from ..services.PromotedLabelDBCRUD import promoted_label_db_crud
from ..database.models import User


class PromotedLabelLogic:
    """Business logic for creating and editing the Promoted Label single-record."""

    async def create_label(
        self,
        db: Session,
        data: PromotedLabelCreateRequest,
        current_user: User,
    ) -> PromotedLabelResponse:
        """
        Create Promoted Label record.

        Rules:
        - Single-record table: if any record exists, creation is blocked with 409 Conflict.
        - This is NOT a category; used only to display name for promoted items.
        """
        try:
            # Enforce single-record constraint at logic level
            existing_count = promoted_label_db_crud.count(db)
            if existing_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Promoted label already exists (single-record table)",
                )

            entity = promoted_label_db_crud.create_label(db, data)
            db.commit()

            return PromotedLabelResponse.model_validate(entity)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during promoted label creation: {str(db_err)}",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during promoted label creation: {str(e)}",
            )

    async def edit_label(
        self,
        db: Session,
        data: PromotedLabelUpdateRequest,
        current_user: User,
    ) -> PromotedLabelResponse:
        """
        Edit existing Promoted Label by primary key 'name'.

        Notes:
        - This is NOT a category; used only to display name for promoted items.
        """
        try:
            entity = promoted_label_db_crud.update_label(db, data)
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Promoted label with name '{data.name}' not found",
                )

            db.commit()
            return PromotedLabelResponse.model_validate(entity)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during promoted label edit: {str(db_err)}",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during promoted label edit: {str(e)}",
            )


# Global logic instance
promoted_label_logic = PromotedLabelLogic()