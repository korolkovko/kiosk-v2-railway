# CategoryRenameLogic.py
# Business logic for Category Rename with cascade updates to ItemLive table
# NOTE: This layer manages full transaction: validation → rename → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.CategoryRenameEndpointPydanticModel import (
    RenameCategoryRequest,
    CategoryRenameResponse
)
from ..services.CategoryRenameDBCRUD import category_rename_db_crud
from ..services.CategoryManagementDBCRUD import category_management_db_crud
from ..database.models import User
from sqlalchemy.exc import SQLAlchemyError


class CategoryRenameLogic:
    """Business logic for renaming categories with cascade updates to ItemLive references"""

    async def rename_category(self, db: Session, rename_request: RenameCategoryRequest, 
                            current_user: User) -> CategoryRenameResponse:
        """
        Main logic flow for category renaming:
        1. Validate admin permissions (handled by dependency)
        2. Validate rename request (category exists, new name available)
        3. Perform atomic rename with cascade updates to ItemLive
        4. Commit all changes in one transaction
        5. Return success response with update count

        Rollback is triggered automatically on any error.
        
        Args:
            db: Database session
            rename_request: Category rename request data
            current_user: Current authenticated admin user
            
        Returns:
            CategoryRenameResponse with success status and update details
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Labels-only path: if new_name is not provided, update only ru/en labels without renaming
            if rename_request.new_name is None:
                # Ensure current category exists
                existing_category = category_rename_db_crud.get_food_category_by_name(db, rename_request.current_name)
                if not existing_category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Food category '{rename_request.current_name}' not found"
                    )

                # Perform partial labels update (only provided fields are updated)
                updated_category = category_management_db_crud.update_food_category_labels(
                    db=db,
                    name=rename_request.current_name,
                    ru_label=getattr(rename_request, "ru_label", None),
                    en_label=getattr(rename_request, "en_label", None),
                )

                # Commit and return response (no items updated since no rename occurred)
                db.commit()
                return CategoryRenameResponse(
                    success=True,
                    message=f"Food category '{rename_request.current_name}' labels updated successfully",
                    old_name=rename_request.current_name,
                    new_name=rename_request.current_name,
                    category_type="food",
                    items_updated_count=0,
                    ru_label=updated_category.ru_label if updated_category else None,
                    en_label=updated_category.en_label if updated_category else None
                )

            # Step 1: Validate rename request (rename + optional labels override)
            is_valid, error_message, items_count = category_rename_db_crud.validate_rename_request(
                db, rename_request
            )
            
            if not is_valid:
                if "not found" in error_message:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=error_message
                    )
                elif "already exists" in error_message:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=error_message
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_message
                    )

            # Step 2: Perform atomic rename with cascade updates
            items_updated_count = category_rename_db_crud.rename_category_with_cascade_by_type(
                db, rename_request
            )

            # Step 3: Commit transaction
            db.commit()

            # Step 4: Prepare success response (food-only)
            category_type_name = "food"
            success_message = f"Food category renamed successfully from '{rename_request.current_name}' to '{rename_request.new_name}'"

            # Fetch resulting labels for the new category (display-only)
            new_category = category_rename_db_crud.get_food_category_by_name(db, rename_request.new_name)
            ru_label = new_category.ru_label if new_category else None
            en_label = new_category.en_label if new_category else None

            return CategoryRenameResponse(
                success=True,
                message=success_message,
                old_name=rename_request.current_name,
                new_name=rename_request.new_name,
                category_type="food",
                items_updated_count=items_updated_count,
                ru_label=ru_label,
                en_label=en_label
            )

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during category rename: {str(db_err)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during category rename: {str(e)}"
            )

    async def validate_category_rename_permissions(self, current_user: User) -> bool:
        """
        Validate that current user has permissions to rename categories.
        
        Note: This is handled by the get_current_admin dependency,
        but this method provides additional validation if needed.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            True if user has permissions, False otherwise
        """
        # Admin role validation is handled by FastAPI dependency
        # This method can be extended for more granular permissions if needed
        return current_user.role_name in ["admin", "superadmin"]

    async def get_category_rename_impact_summary(self, db: Session, rename_request: RenameCategoryRequest) -> dict:
        """
        Get summary of what would be affected by the rename operation.
        This can be useful for admin interfaces to show impact before confirming.
        
        Args:
            db: Database session
            rename_request: Category rename request data
            
        Returns:
            Dictionary with impact analysis
        """
        try:
            # Get validation results and impact count
            is_valid, error_message, items_count = category_rename_db_crud.validate_rename_request(
                db, rename_request
            )
            
            category_type_name = "food"
            
            # Capture current labels for reference
            current_category = category_rename_db_crud.get_food_category_by_name(db, rename_request.current_name)
            current_labels = {
                "ru_label": current_category.ru_label if current_category else None,
                "en_label": current_category.en_label if current_category else None
            }

            # Proposed labels (if provided; otherwise None, meaning copy-on-rename)
            proposed_labels = {
                "ru_label": getattr(rename_request, "ru_label", None),
                "en_label": getattr(rename_request, "en_label", None)
            }

            return {
                "is_valid": is_valid,
                "error_message": error_message if not is_valid else None,
                "category_type": category_type_name,
                "current_name": rename_request.current_name,
                "new_name": rename_request.new_name,
                "items_affected_count": items_count,
                "impact_description": f"Renaming will update {items_count} menu items" if is_valid else None,
                # Non-breaking, additive fields for labels visibility
                "current_labels": current_labels,
                "proposed_labels": proposed_labels
            }
        except SQLAlchemyError as db_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving rename impact: {str(db_err)}"
            )


# Global logic instance
category_rename_logic = CategoryRenameLogic()