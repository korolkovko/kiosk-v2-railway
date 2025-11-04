# MenuActivationDeactivationDBCRUD.py
# Database CRUD operations for Menu Activation/Deactivation functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from ..database.models import Menu
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class MenuActivationDeactivationDBCRUD:
    """Database CRUD operations for menu activation/deactivation functionality"""

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

    def get_currently_active_menu(self, db: Session) -> Optional[Menu]:
        """
        Get the currently active menu (if any)
        
        Args:
            db: Database session
            
        Returns:
            Currently active Menu object, or None if no menu is active
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return db.query(Menu).filter(Menu.is_active == True).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active menu: {str(e)}")
            raise

    def get_all_active_menus(self, db: Session) -> List[Menu]:
        """
        Get all currently active menus (should be 0 or 1, but checking for data integrity)
        
        Args:
            db: Database session
            
        Returns:
            List of active Menu objects
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return db.query(Menu).filter(Menu.is_active == True).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all active menus: {str(e)}")
            raise

    def deactivate_menu(self, db: Session, menu: Menu) -> Menu:
        """
        Deactivate a menu
        
        Args:
            db: Database session
            menu: Menu object to deactivate
            
        Returns:
            Updated Menu object
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            menu.is_active = False
            db.add(menu)
            db.flush()  # Flush to catch any database errors before commit
            return menu
        except SQLAlchemyError as e:
            logger.error(f"Database error deactivating menu {menu.id}: {str(e)}")
            db.rollback()
            raise

    def activate_menu(self, db: Session, menu: Menu) -> Menu:
        """
        Activate a menu
        
        Args:
            db: Database session
            menu: Menu object to activate
            
        Returns:
            Updated Menu object
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            menu.is_active = True
            db.add(menu)
            db.flush()  # Flush to catch any database errors before commit
            return menu
        except SQLAlchemyError as e:
            logger.error(f"Database error activating menu {menu.id}: {str(e)}")
            db.rollback()
            raise

    def deactivate_all_menus(self, db: Session) -> List[Menu]:
        """
        Deactivate all currently active menus
        
        Args:
            db: Database session
            
        Returns:
            List of menus that were deactivated
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            active_menus = self.get_all_active_menus(db)
            
            for menu in active_menus:
                menu.is_active = False
                db.add(menu)
            
            db.flush()  # Flush to catch any database errors before commit
            return active_menus
            
        except SQLAlchemyError as e:
            logger.error(f"Database error deactivating all menus: {str(e)}")
            db.rollback()
            raise

    def get_menu_activation_statistics(self, db: Session) -> dict:
        """
        Get statistics about menu activation status
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with activation statistics
        """
        try:
            total_menus = db.query(Menu).count()
            active_menus = db.query(Menu).filter(Menu.is_active == True).count()
            inactive_menus = total_menus - active_menus
            
            return {
                "total_menus": total_menus,
                "active_menus": active_menus,
                "inactive_menus": inactive_menus
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting activation statistics: {str(e)}")
            raise


# Create a singleton instance
menu_activation_deactivation_db_crud = MenuActivationDeactivationDBCRUD()