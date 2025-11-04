# MenuPreparationDBCRUD.py
# Database CRUD operations for Menu Preparation CSV export functionality

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import distinct
from ..database.models import ItemLive, FoodCategory
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class MenuPreparationDBCRUD:
    """Database CRUD operations for menu preparation functionality"""

    def get_non_archived_items_with_categories(self, db: Session) -> List[ItemLive]:
        """
        Retrieve all non-archived items with their food category information
        
        Args:
            db: Database session
            
        Returns:
            List of ItemLive objects where is_archived = False
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return (
                db.query(ItemLive)
                .filter(ItemLive.is_archived == False)
                .order_by(ItemLive.food_category_name, ItemLive.item_id)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving non-archived items: {str(e)}")
            raise

    def get_unique_categories_from_non_archived_items(self, db: Session) -> Set[str]:
        """
        Get unique food category names that are referenced by non-archived items
        
        Args:
            db: Database session
            
        Returns:
            Set of unique food category names
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            result = (
                db.query(distinct(ItemLive.food_category_name))
                .filter(ItemLive.is_archived == False)
                .all()
            )
            return {category_name[0] for category_name in result if category_name[0]}
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving unique categories: {str(e)}")
            raise

    def get_non_archived_items_count(self, db: Session) -> int:
        """
        Get the total count of non-archived items
        
        Args:
            db: Database session
            
        Returns:
            Number of non-archived items
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return db.query(ItemLive).filter(ItemLive.is_archived == False).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting non-archived items: {str(e)}")
            raise

    def validate_food_categories_exist(self, db: Session, category_names: Set[str]) -> bool:
        """
        Validate that all provided food category names exist in the FoodCategory table
        
        Args:
            db: Database session
            category_names: Set of category names to validate
            
        Returns:
            True if all categories exist, False otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            if not category_names:
                return True
                
            existing_categories = (
                db.query(FoodCategory.name)
                .filter(FoodCategory.name.in_(category_names))
                .all()
            )
            existing_names = {cat[0] for cat in existing_categories}
            
            missing_categories = category_names - existing_names
            if missing_categories:
                logger.warning(f"Missing food categories: {missing_categories}")
                return False
                
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error validating food categories: {str(e)}")
            raise

    def get_menu_export_statistics(self, db: Session) -> dict:
        """
        Get statistics about items and categories available for menu export
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with export statistics
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            non_archived_count = self.get_non_archived_items_count(db)
            archived_count = db.query(ItemLive).filter(ItemLive.is_archived == True).count()
            total_count = non_archived_count + archived_count
            
            unique_categories = self.get_unique_categories_from_non_archived_items(db)
            categories_count = len(unique_categories)
            
            return {
                "total_items": total_count,
                "non_archived_items": non_archived_count,
                "archived_items": archived_count,
                "unique_categories_in_non_archived": categories_count,
                "non_archived_percentage": round((non_archived_count / total_count * 100), 2) if total_count > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting menu export statistics: {str(e)}")
            raise


# Create a singleton instance
menu_preparation_db_crud = MenuPreparationDBCRUD()