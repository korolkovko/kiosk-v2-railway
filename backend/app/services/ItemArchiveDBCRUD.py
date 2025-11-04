# ItemArchiveDBCRUD.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.models import ItemLive
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ItemArchiveDBCRUD:
    """Database CRUD operations for item archive functionality"""

    def get_item_by_id(self, db: Session, item_id: int) -> Optional[ItemLive]:
        """
        Retrieve an item by its ID
        
        Args:
            db: Database session
            item_id: ID of the item to retrieve
            
        Returns:
            ItemLive object if found, None otherwise
        """
        try:
            return db.query(ItemLive).filter(ItemLive.item_id == item_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving item {item_id}: {str(e)}")
            raise

    def update_archive_status(self, db: Session, item: ItemLive, is_archived: bool) -> ItemLive:
        """
        Update the archive status of an item
        
        Args:
            db: Database session
            item: ItemLive object to update
            is_archived: New archive status
            
        Returns:
            Updated ItemLive object
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            item.is_archived = is_archived
            db.add(item)
            db.flush()  # Flush to get any database errors before commit
            return item
        except SQLAlchemyError as e:
            logger.error(f"Database error updating archive status for item {item.item_id}: {str(e)}")
            db.rollback()
            raise

    def get_item_archive_status(self, db: Session, item_id: int) -> Optional[bool]:
        """
        Get the current archive status of an item
        
        Args:
            db: Database session
            item_id: ID of the item
            
        Returns:
            True if archived, False if not archived, None if item not found
        """
        try:
            result = db.query(ItemLive.is_archived).filter(ItemLive.item_id == item_id).first()
            return result[0] if result else None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting archive status for item {item_id}: {str(e)}")
            raise

    def get_archived_items_count(self, db: Session) -> int:
        """
        Get the total count of archived items
        
        Args:
            db: Database session
            
        Returns:
            Number of archived items
        """
        try:
            return db.query(ItemLive).filter(ItemLive.is_archived == True).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting archived items: {str(e)}")
            raise

    def get_active_items_count(self, db: Session) -> int:
        """
        Get the total count of non-archived items
        
        Args:
            db: Database session
            
        Returns:
            Number of non-archived items
        """
        try:
            return db.query(ItemLive).filter(ItemLive.is_archived == False).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting active items: {str(e)}")
            raise


# Create a singleton instance
item_archive_db_crud = ItemArchiveDBCRUD()