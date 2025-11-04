# CategoryManagementLogic.py
# Business logic for Category Management (FoodCategory only)
# NOTE: This layer manages full transaction: validation → creation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
# Note: Day categories are no longer supported; food-only management

from ..models.CategoryManagementPydanticModel import (
    CreateCategoryRequest,
    DeleteCategoryRequest,
    CategoryLabelUpdateRequest,
    CategoryCreationResponse,
    CategoryDeletionResponse,
    FoodCategoryResponse
)
from ..services.CategoryManagementDBCRUD import category_management_db_crud
from ..database.models import User, FoodCategory
from sqlalchemy.exc import SQLAlchemyError


class CategoryManagementLogic:
    """Business logic for creating categories (FoodCategory only)"""

    async def create_category(self, db: Session, category_data: CreateCategoryRequest, 
                            current_user: User) -> CategoryCreationResponse:
        """
        Main logic flow for category creation:
        1. Validate admin permissions (handled by dependency)
        2. Validate category name uniqueness
        3. Create category based on type
        4. Commit all changes in one transaction
        5. Return success response

        Rollback is triggered automatically on any error.
        
        Args:
            db: Database session
            category_data: Category creation request data
            current_user: Current authenticated admin user
            
        Returns:
            CategoryCreationResponse with success status and created category details
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Step 1: Validate category name uniqueness (food-only)
            if not category_management_db_crud.validate_category_name_uniqueness(
                db, category_data.name
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Food category '{category_data.name}' already exists"
                )

            # Step 2: Create food category
            created_category = category_management_db_crud.create_food_category(db, category_data)

            # Step 3: Commit transaction
            db.commit()

            # Step 4: Prepare response (food-only)
            category_response = FoodCategoryResponse.model_validate(created_category)
            success_message = f"Food category '{category_data.name}' created successfully"

            # Step 5: Return success response
            return CategoryCreationResponse(
                success=True,
                message=success_message,
                category=category_response.model_dump()
            )

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Database error during category creation: {str(db_err)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Unexpected error during category creation: {str(e)}"
            )

    async def validate_category_creation_permissions(self, current_user: User) -> bool:
        """
        Validate that current user has permissions to create categories.
        
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

    async def get_category_creation_summary(self, db: Session) -> dict:
        """
        Get summary of existing categories for reference.
        This can be useful for admin interfaces.

        Note:
        - ru_label and en_label are optional, display-only fields for categories.
        - This method is backward compatible: it preserves the legacy "food_categories"
          shape and adds non-breaking fields with labels information.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with category counts and examples, plus labels:
            {
              "food_categories": { "count": int, "categories": [str] },
              "food_categories_details": [{ "name": str, "ru_label": str|None, "en_label": str|None }],
              "labels_map": { "<name>": { "ru_label": str|None, "en_label": str|None } }
            }
        """
        try:
            # Query full category objects to include optional labels
            categories = db.query(FoodCategory).order_by(FoodCategory.name.asc()).all()

            names = [c.name for c in categories]
            details = [
                {
                    "name": c.name,
                    "ru_label": c.ru_label,
                    "en_label": c.en_label
                }
                for c in categories
            ]
            labels_map = {
                c.name: {
                    "ru_label": c.ru_label,
                    "en_label": c.en_label
                } for c in categories
            }

            return {
                "food_categories": {
                    "count": len(names),
                    "categories": names
                },
                # Non-breaking, additive fields
                "food_categories_details": details,
                "labels_map": labels_map
            }
        except SQLAlchemyError as db_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving category summary: {str(db_err)}"
            )

    async def update_category_labels(self, db: Session, label_request: CategoryLabelUpdateRequest,
                                     current_user: User) -> FoodCategoryResponse:
        """
        Update display-only labels (ru_label/en_label) for an existing FoodCategory without renaming.

        Rules:
        - name identifies the category (PK)
        - ru_label/en_label are optional; only provided fields will be updated
        - labels are display-only and do not affect identity or relations
        """
        try:
            # Ensure category exists
            category = category_management_db_crud.get_food_category_by_name(db, label_request.name)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food category '{label_request.name}' not found"
                )

            # Perform partial labels update
            updated = category_management_db_crud.update_food_category_labels(
                db=db,
                name=label_request.name,
                ru_label=getattr(label_request, "ru_label", None),
                en_label=getattr(label_request, "en_label", None),
            )

            # Commit transaction
            db.commit()

            # Return updated category as DTO (now includes labels)
            return FoodCategoryResponse.model_validate(updated)

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during category labels update: {str(db_err)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during category labels update: {str(e)}"
            )

    async def delete_category(self, db: Session, delete_request: DeleteCategoryRequest,
                            current_user: User) -> CategoryDeletionResponse:
        """
        Main logic flow for category deletion:
        1. Validate admin permissions (handled by dependency)
        2. Check if category exists
        3. Check if category is referenced by any items (safety check)
        4. Delete category if safe
        5. Commit all changes in one transaction
        6. Return success response

        Rollback is triggered automatically on any error.
        
        Args:
            db: Database session
            delete_request: Category deletion request data
            current_user: Current authenticated admin user
            
        Returns:
            CategoryDeletionResponse with success status and message
            
        Raises:
            HTTPException: If validation fails, category not found, has references, or database error occurs
        """
        try:
            # Step 1: Check if category exists (food-only)
            existing_category = category_management_db_crud.get_food_category_by_name(db, delete_request.name)
            
            if not existing_category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Food category '{delete_request.name}' not found"
                )

            # Step 2: Safety check - ensure no items reference this category
            reference_count = category_management_db_crud.check_food_category_has_item_references(
                db, delete_request.name
            )
            
            if reference_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot delete food category '{delete_request.name}': {reference_count} menu items are using this category"
                )

            # Step 3: Delete category
            deletion_successful = category_management_db_crud.delete_food_category(db, delete_request.name)
            
            if not deletion_successful:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete food category '{delete_request.name}'"
                )

            # Step 4: Commit transaction
            db.commit()

            # Step 5: Return success response
            success_message = f"Food category '{delete_request.name}' deleted successfully"
            return CategoryDeletionResponse(
                success=True,
                message=success_message
            )

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during category deletion: {str(db_err)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during category deletion: {str(e)}"
            )


# Global logic instance
category_management_logic = CategoryManagementLogic()