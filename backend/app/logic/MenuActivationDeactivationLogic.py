# MenuActivationDeactivationLogic.py
# Business logic for Menu Activation/Deactivation functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import Optional

from ..models.MenuActivationDeactivationPydanticModel import (
    MenuActivationRequest,
    MenuActivationResponse
)
from ..models.SSEEventModels import MenuActivatedEvent
from ..services.MenuActivationDeactivationDBCRUD import menu_activation_deactivation_db_crud
from ..database.models import User, Menu
from ..websockets.event_bus import bus
import logging

logger = logging.getLogger(__name__)


class MenuActivationDeactivationLogic:
    """Business logic for menu activation/deactivation operations"""

    async def toggle_menu_activation(
        self, 
        db: Session, 
        request: MenuActivationRequest, 
        current_user: User
    ) -> MenuActivationResponse:
        """
        Activate or deactivate a menu with single active menu constraint
        
        Business Rules:
        1. Only one menu can be active at a time
        2. When activating a menu, any currently active menu is automatically deactivated
        3. System allows having no active menus
        4. Cannot activate an already active menu or deactivate an already inactive menu
        
        Args:
            db: Database session
            request: Menu activation request containing menu_id/menu_name and is_active
            current_user: Current authenticated admin user
            
        Returns:
            MenuActivationResponse with operation result
            
        Raises:
            HTTPException: For various error conditions (404, 409, 500)
        """
        try:
            logger.info(
                f"Menu activation toggle requested by user {current_user.username}: "
                f"ID={request.menu_id}, Name={request.menu_name}, is_active={request.is_active}"
            )
            
            # Step 1: Find the target menu
            target_menu = menu_activation_deactivation_db_crud.find_menu_by_id_or_name(
                db, request.menu_id, request.menu_name
            )
            
            if not target_menu:
                # Determine which identifier was used for better error message
                if request.menu_id and request.menu_name:
                    detail = f"Menu with ID {request.menu_id} or name '{request.menu_name}' not found"
                elif request.menu_id:
                    detail = f"Menu with ID {request.menu_id} not found"
                else:
                    detail = f"Menu with name '{request.menu_name}' not found"
                
                logger.warning(f"Menu activation failed: {detail}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=detail
                )
            
            # Step 2: Check current status to prevent redundant operations
            current_status = target_menu.is_active
            
            if request.is_active and current_status:
                # Trying to activate an already active menu
                logger.info(f"Menu activation skipped: Menu '{target_menu.name}' is already active")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Menu '{target_menu.name}' is already active"
                )
            
            if not request.is_active and not current_status:
                # Trying to deactivate an already inactive menu
                logger.info(f"Menu deactivation skipped: Menu '{target_menu.name}' is already inactive")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Menu '{target_menu.name}' is already inactive"
                )
            
            # Step 3: Handle activation logic (single active menu constraint)
            previously_active_menu = None
            
            if request.is_active:
                # Activating a menu - first deactivate any currently active menu
                currently_active_menu = menu_activation_deactivation_db_crud.get_currently_active_menu(db)
                
                if currently_active_menu and currently_active_menu.id != target_menu.id:
                    # Deactivate the currently active menu
                    menu_activation_deactivation_db_crud.deactivate_menu(db, currently_active_menu)
                    previously_active_menu = {
                        "id": currently_active_menu.id,
                        "name": currently_active_menu.name
                    }
                    logger.info(f"Deactivated previously active menu '{currently_active_menu.name}' (ID: {currently_active_menu.id})")
                
                # Activate the target menu
                menu_activation_deactivation_db_crud.activate_menu(db, target_menu)
                action_performed = "activated"
                
            else:
                # Deactivating a menu
                menu_activation_deactivation_db_crud.deactivate_menu(db, target_menu)
                action_performed = "deactivated"
            
            # Step 4: Commit the transaction
            db.commit()

            logger.info(
                f"Menu '{target_menu.name}' (ID: {target_menu.id}) {action_performed} by user {current_user.username}"
            )

            # Step 5: Broadcast SSE event to all kiosks (only if activated)
            if request.is_active:
                await self._broadcast_menu_activated_event(
                    menu_id=target_menu.id,
                    menu_name=target_menu.name
                )

            return MenuActivationResponse(
                success=True,
                message=f"Menu {action_performed} successfully",
                menu_id=target_menu.id,
                menu_name=target_menu.name,
                is_active=target_menu.is_active,
                action_performed=action_performed,
                previously_active_menu=previously_active_menu
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            db.rollback()
            raise
        except SQLAlchemyError as e:
            # Handle database errors
            db.rollback()
            logger.error(f"Database error during menu activation toggle: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while updating menu activation status"
            )
        except Exception as e:
            # Handle unexpected errors
            db.rollback()
            logger.error(f"Unexpected error during menu activation toggle: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while updating menu activation status"
            )

    async def get_menu_activation_statistics(self, db: Session) -> dict:
        """
        Get statistics about menu activation status

        Args:
            db: Database session

        Returns:
            Dictionary with activation statistics
        """
        try:
            stats = menu_activation_deactivation_db_crud.get_menu_activation_statistics(db)
            currently_active_menu = menu_activation_deactivation_db_crud.get_currently_active_menu(db)

            result = {
                **stats,
                "currently_active_menu": None
            }

            if currently_active_menu:
                result["currently_active_menu"] = {
                    "id": currently_active_menu.id,
                    "name": currently_active_menu.name,
                    "description": currently_active_menu.description
                }

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error getting activation statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving menu activation statistics"
            )

    async def _broadcast_menu_activated_event(self, menu_id: int, menu_name: str):
        """
        Broadcast MENU_ACTIVATED SSE event to all kiosks

        Args:
            menu_id: ID of the activated menu
            menu_name: Name of the activated menu
        """
        try:
            # Create SSE event
            event = MenuActivatedEvent(
                menu_id=menu_id,
                menu_name=menu_name
            )

            # Broadcast to all kiosk subscribers
            await bus.publish("kiosk_broadcast", event.model_dump(mode='json'))

            logger.info(f"📡 Menu activated event broadcasted: menu_id={menu_id}, menu_name='{menu_name}'")

        except Exception as e:
            logger.error(f"❌ Failed to broadcast menu activated event: {e}")
            # Don't raise exception - menu activation should succeed even if SSE fails


# Create a singleton instance
menu_activation_deactivation_logic = MenuActivationDeactivationLogic()