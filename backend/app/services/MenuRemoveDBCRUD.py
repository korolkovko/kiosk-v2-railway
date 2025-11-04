# MenuRemoveDBCRUD.py
# Database CRUD operations for Menu Remove functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from ..database.models import Menu, MenuCategory, MenuItem
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MenuRemoveDBCRUD:
    """Database CRUD operations for menu removal functionality"""

    def find_menu_by_id_or_name(self, db: Session, menu_id: Optional[int], menu_name: Optional[str]) -> Optional[Menu]:
        """
        Find a menu by ID or name
        
        Args:
            db: Database session
            menu_id: Optional menu ID to search for
            menu_name: Optional menu name to search for
            
        Returns:
            Menu object if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            query = db.query(Menu)
            
            conditions = []
            if menu_id is not None:
                conditions.append(Menu.id == menu_id)
            if menu_name is not None:
                conditions.append(Menu.name == menu_name)
            
            if not conditions:
                return None
                
            return query.filter(or_(*conditions)).first()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error finding menu: {str(e)}")
            raise

    def get_menu_deletion_statistics(self, db: Session, menu: Menu) -> Tuple[int, int]:
        """
        Get statistics about what will be deleted with the menu
        
        Args:
            db: Database session
            menu: Menu object to analyze
            
        Returns:
            Tuple of (items_count, categories_count)
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            items_count = db.query(MenuItem).filter(MenuItem.menu_id == menu.id).count()
            categories_count = db.query(MenuCategory).filter(MenuCategory.menu_id == menu.id).count()
            
            return items_count, categories_count
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting deletion statistics: {str(e)}")
            raise

    def delete_menu_with_cascade(self, db: Session, menu: Menu) -> Tuple[int, int]:
        """
        Delete menu and all associated records (cascade delete)
        
        Args:
            db: Database session
            menu: Menu object to delete
            
        Returns:
            Tuple of (items_deleted_count, categories_deleted_count)
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get counts before deletion
            items_count, categories_count = self.get_menu_deletion_statistics(db, menu)
            
            # Delete the menu (cascade will handle MenuCategory and MenuItem)
            # The cascade="all, delete-orphan" in the Menu model relationships
            # will automatically delete associated MenuCategory and MenuItem records
            db.delete(menu)
            db.flush()  # Flush to catch any constraint violations
            
            logger.info(f"Menu '{menu.name}' (ID: {menu.id}) deleted with {items_count} items and {categories_count} categories")
            
            return items_count, categories_count
            
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting menu {menu.id}: {str(e)}")
            db.rollback()
            raise

    def get_all_menus_summary(self, db: Session) -> list:
        """
        Get summary of all existing menus
        
        Args:
            db: Database session
            
        Returns:
            List of menu summaries with basic information
        """
        try:
            menus = db.query(Menu).all()
            return [
                {
                    "id": menu.id,
                    "name": menu.name,
                    "description": menu.description,
                    "is_active": menu.is_active
                }
                for menu in menus
            ]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting menus summary: {str(e)}")
            raise


# Create a singleton instance
menu_remove_db_crud = MenuRemoveDBCRUD()