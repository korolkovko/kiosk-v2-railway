# KioskCategoriesLogic.py
# Business logic for kiosk categories functionality
# Handles business rules and data transformation for categories endpoint

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..database.models import User, PromotedLabel
from ..models.KioskCategoriesResponseModel import (
    KioskCategoryResponse,
    KioskCategoriesListResponse,
    PromotedLabelResponse
)
from ..services.KioskCategoriesDBCRUD import kiosk_categories_db_crud


class KioskCategoriesLogic:
    """
    Business logic for kiosk categories operations
    
    Handles business rules, validation, and data transformation
    for food categories functionality in kiosk system.
    """
    
    async def get_all_categories_with_synthetic_promoted(
        self,
        db: Session,
        current_user: User
    ) -> KioskCategoriesListResponse:
        """
        Get all categories with synthetic promoted category at position 0

        Returns unified category structure where:
        - Index [0]: Synthetic promoted category (from promoted_label table, display_order=0)
        - Index [1+]: Regular categories (from menu_categories, display_order shifted by +1)

        The promoted category is synthetic - it doesn't exist in food_categories.
        Regular categories are shifted to make room for synthetic promoted at position 0.

        Args:
            db: Database session
            current_user: Authenticated kiosk user

        Returns:
            KioskCategoriesListResponse: Unified list with synthetic promoted + regular categories

        Raises:
            HTTPException: If database operation fails or user validation fails
        """
        try:
            # Validate user is active (business rule)
            if not current_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user cannot access categories"
                )

            # 1. Create synthetic promoted category from promoted_label table (display_order=0)
            promoted_label_record = db.query(PromotedLabel).filter(
                PromotedLabel.name == "promoted"
            ).first()

            synthetic_promoted_response = KioskCategoryResponse(
                name=promoted_label_record.name if promoted_label_record else "promoted",
                display_order=0,  # Synthetic promoted always at position 0
                ru_label=promoted_label_record.ru_label if promoted_label_record else None,
                en_label=promoted_label_record.en_label if promoted_label_record else None,
                created_at=promoted_label_record.created_at if promoted_label_record else None
            )

            # 2. Fetch regular categories from active menu (filtered by menu_categories)
            categories_with_order = kiosk_categories_db_crud.get_all_food_categories(db)

            # 3. Transform regular categories with shifted display_order (+1 for synthetic promoted)
            regular_category_responses = [
                KioskCategoryResponse(
                    name=category.name,
                    display_order=display_order + 1,  # Shift by +1 for synthetic promoted at 0
                    ru_label=category.ru_label,
                    en_label=category.en_label,
                    created_at=category.created_at
                )
                for category, display_order in categories_with_order
            ]

            # 4. Combine: synthetic promoted first, then regular categories
            all_categories_with_synthetic_promoted = [
                synthetic_promoted_response
            ] + regular_category_responses

            return KioskCategoriesListResponse(
                categories=all_categories_with_synthetic_promoted,
                total_count=len(all_categories_with_synthetic_promoted)
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Handle unexpected database or processing errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve categories with synthetic promoted: {str(e)}"
            )


# Create singleton instance for dependency injection
kiosk_categories_logic = KioskCategoriesLogic()