# MenuRemoveLogic.py
# Business logic for Menu Remove functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import Optional

from ..models.MenuRemovePydanticModel import (
    MenuDeleteRequest, 
    MenuDeleteResponse
)
from ..services.MenuRemoveDBCRUD import menu_remove_db_crud
from ..database.models import User, Menu
import logging

logger = logging.getLogger(__name__)


class MenuRemoveLogic:
    """Business logic for menu removal operations"""

    async def delete_menu(
        self, 
        db: Session, 
        request: MenuDeleteRequest, 
        current_user: User
    ) -> MenuDeleteResponse:
        """
        Delete a menu by ID or name with business logic validation
        
        Args:
            db: Database session
            request: Menu delete request containing menu_id and/or menu_name
            current_user: Current authenticated admin user
            
        Returns:
            MenuDeleteResponse with operation result
            
        Raises:
            HTTPException: For various error conditions (404, 409, 500)
        """
        try:
            logger.info(
                f"Menu deletion requested by user {current_user.username}: "
                f"ID={request.menu_id}, Name={request.menu_name}"
            )
            
            # Step 1: Find the menu
            menu = menu_remove_db_crud.find_menu_by_id_or_name(
                db, request.menu_id, request.menu_name
            )
            
            if not menu:
                # Determine which identifier was used for better error message
                if request.menu_id and request.menu_name:
                    detail = f"Menu with ID {request.menu_id} or name '{request.menu_name}' not found"
                elif request.menu_id:
                    detail = f"Menu with ID {request.menu_id} not found"
                else:
                    detail = f"Menu with name '{request.menu_name}' not found"
                
                logger.warning(f"Menu deletion failed: {detail}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=detail
                )
            
            # Step 2: Business logic validation - check if menu is active
            if menu.is_active:
                logger.warning(
                    f"Menu deletion blocked: Menu '{menu.name}' (ID: {menu.id}) is active"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot delete active menu '{menu.name}'. Deactivate the menu first."
                )
            
            # Step 3: Get deletion statistics before deletion
            items_count, categories_count = menu_remove_db_crud.get_menu_deletion_statistics(db, menu)
            
            # Step 4: Perform deletion
            deleted_items, deleted_categories = menu_remove_db_crud.delete_menu_with_cascade(db, menu)
            
            # Step 5: Commit transaction
            db.commit()
            
            logger.info(
                f"Menu '{menu.name}' (ID: {menu.id}) deleted successfully by user {current_user.username}: "
                f"{deleted_items} items, {deleted_categories} categories"
            )
            
            return MenuDeleteResponse(
                success=True,
                message="Menu deleted successfully",
                deleted_menu_id=menu.id,
                deleted_menu_name=menu.name,
                items_deleted=deleted_items,
                categories_deleted=deleted_categories
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            db.rollback()
            raise
        except SQLAlchemyError as e:
            # Handle database errors
            db.rollback()
            logger.error(f"Database error during menu deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while deleting menu"
            )
        except Exception as e:
            # Handle unexpected errors
            db.rollback()
            logger.error(f"Unexpected error during menu deletion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while deleting menu"
            )

    async def get_all_menus_summary(self, db: Session) -> dict:
        """
        Get summary of all existing menus
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with menus summary
        """
        try:
            menus = menu_remove_db_crud.get_all_menus_summary(db)
            
            active_count = sum(1 for menu in menus if menu['is_active'])
            inactive_count = len(menus) - active_count
            
            return {
                "total_menus": len(menus),
                "active_menus": active_count,
                "inactive_menus": inactive_count,
                "menus": menus
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting menus summary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving menus summary"
            )


# Create a singleton instance
menu_remove_logic = MenuRemoveLogic()