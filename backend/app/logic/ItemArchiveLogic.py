# ItemArchiveLogic.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from ..models.ItemArchivePydanticModel import ItemArchiveStatusRequest, ItemArchiveStatusResponse
from ..services.ItemArchiveDBCRUD import item_archive_db_crud
from ..database.models import User
import logging

logger = logging.getLogger(__name__)


class ItemArchiveLogic:
    """Business logic for item archive operations"""

    async def update_item_archive_status(
        self, 
        db: Session, 
        request: ItemArchiveStatusRequest, 
        current_user: User
    ) -> ItemArchiveStatusResponse:
        """
        Archive or unarchive an item with comprehensive error handling
        
        Args:
            db: Database session
            request: Archive status request containing item_id and is_archived
            current_user: Current authenticated user (admin/superadmin)
            
        Returns:
            ItemArchiveStatusResponse with operation result
            
        Raises:
            HTTPException: For various error conditions (404, 409, 500)
        """
        try:
            # Step 1: Validate item exists
            item = item_archive_db_crud.get_item_by_id(db, request.item_id)
            if not item:
                logger.warning(f"Archive operation failed: Item {request.item_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with ID {request.item_id} not found"
                )

            # Step 2: Check current archive status to prevent redundant operations
            current_archive_status = item.is_archived
            
            if request.is_archived and current_archive_status:
                # Trying to archive an already archived item
                logger.info(f"Archive operation skipped: Item {request.item_id} is already archived")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Item with ID {request.item_id} is already archived"
                )
            
            if not request.is_archived and not current_archive_status:
                # Trying to unarchive an already active item
                logger.info(f"Unarchive operation skipped: Item {request.item_id} is already active")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Item with ID {request.item_id} is already active (not archived)"
                )

            # Step 3: Update archive status
            updated_item = item_archive_db_crud.update_archive_status(
                db, item, request.is_archived
            )
            
            # Step 4: Commit the transaction
            db.commit()
            
            # Step 5: Prepare response
            action_performed = "archived" if request.is_archived else "unarchived"
            success_message = f"Item successfully {action_performed}"
            
            logger.info(
                f"Item {request.item_id} {action_performed} by user {current_user.username}"
            )
            
            return ItemArchiveStatusResponse(
                success=True,
                message=success_message,
                item_id=updated_item.item_id,
                is_archived=updated_item.is_archived,
                action_performed=action_performed
            )

        except HTTPException:
            # Re-raise HTTP exceptions (404, 409) as-is
            db.rollback()
            raise
        except SQLAlchemyError as e:
            # Handle database errors
            db.rollback()
            logger.error(f"Database error during archive operation for item {request.item_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while updating item archive status"
            )
        except Exception as e:
            # Handle unexpected errors
            db.rollback()
            logger.error(f"Unexpected error during archive operation for item {request.item_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while updating item archive status"
            )

    async def get_archive_statistics(self, db: Session) -> dict:
        """
        Get statistics about archived vs active items
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with archive statistics
        """
        try:
            archived_count = item_archive_db_crud.get_archived_items_count(db)
            active_count = item_archive_db_crud.get_active_items_count(db)
            total_count = archived_count + active_count
            
            return {
                "total_items": total_count,
                "active_items": active_count,
                "archived_items": archived_count,
                "archive_percentage": round((archived_count / total_count * 100), 2) if total_count > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting archive statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving archive statistics"
            )


# Create a singleton instance
item_archive_logic = ItemArchiveLogic()