# CategoryManagementDBCRUD.py
# Database CRUD operations for Category Management
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import time

from ..database.models import FoodCategory, ItemLive
from ..models.CategoryManagementPydanticModel import CreateCategoryRequest, DeleteCategoryRequest


class CategoryManagementDBCRUD:
    """Database CRUD operations for Category Management"""

    def create_food_category(self, db: Session, category_data: CreateCategoryRequest) -> FoodCategory:
        """
        Create new FoodCategory in the database.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        
        Args:
            db: Database session
            category_data: Category creation request data
            
        Returns:
            Created FoodCategory instance
        """
        db_food_category = FoodCategory(
            name=category_data.name,
            ru_label=getattr(category_data, "ru_label", None),
            en_label=getattr(category_data, "en_label", None),
        )

        db.add(db_food_category)
        db.flush()  # Ensure the category is persisted and accessible

        return db_food_category

    def check_food_category_name_exists(self, db: Session, category_name: str) -> bool:
        """
        Check if a FoodCategory with the given name already exists.
        
        Args:
            db: Database session
            category_name: Name to check for duplicates
            
        Returns:
            True if category name exists, False otherwise
        """
        return db.query(FoodCategory).filter(FoodCategory.name == category_name).first() is not None

    def get_food_category_by_name(self, db: Session, category_name: str) -> Optional[FoodCategory]:
        """
        Get FoodCategory by name.
        
        Args:
            db: Database session
            category_name: Name of the category to retrieve
            
        Returns:
            FoodCategory instance if found, None otherwise
        """
        return db.query(FoodCategory).filter(FoodCategory.name == category_name).first()

    def validate_category_name_uniqueness(self, db: Session, category_name: str) -> bool:
        """
        Validate that food category name is unique.
        
        Args:
            db: Database session
            category_name: Name to validate
            
        Returns:
            True if name is unique, False if duplicate exists
        """
        return not self.check_food_category_name_exists(db, category_name)

    def create_category_by_type(self, db: Session, category_data: CreateCategoryRequest) -> FoodCategory:
        """
        Create category.

        Note: Only FoodCategory is supported. Kept for backward compatibility.
        """
        return self.create_food_category(db, category_data)

    def check_food_category_has_item_references(self, db: Session, category_name: str) -> int:
        """
        Check if any ItemLive records reference the given FoodCategory.
        
        Args:
            db: Database session
            category_name: Name of the food category to check
            
        Returns:
            Number of ItemLive records referencing this category
        """
        return db.query(ItemLive).filter(ItemLive.food_category_name == category_name).count()

    def check_category_has_item_references(self, db: Session, category_name: str, category_type=None) -> int:
        """
        Check if any ItemLive records reference the given category.

        Note: Only FoodCategory is supported. 'category_type' is ignored.
        
        Args:
            db: Database session
            category_name: Name of the category to check
            
        Returns:
            Number of ItemLive records referencing this category
        """
        return self.check_food_category_has_item_references(db, category_name)

    def delete_food_category(self, db: Session, category_name: str) -> bool:
        """
        Delete FoodCategory from the database.

        NOTE: This method only performs db.delete() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        
        Args:
            db: Database session
            category_name: Name of the food category to delete
            
        Returns:
            True if category was found and deleted, False if not found
        """
        food_category = self.get_food_category_by_name(db, category_name)
        if food_category:
            db.delete(food_category)
            db.flush()  # Ensure the deletion is processed
            return True
        return False

    def delete_category_by_type(self, db: Session, delete_request: DeleteCategoryRequest) -> bool:
        """
        Delete category.

        Note: Only FoodCategory is supported. 'category_type' is ignored for backward compatibility.
        
        Args:
            db: Database session
            delete_request: Category deletion request data

        Returns:
            True if category was found and deleted, False if not found
        """
        return self.delete_food_category(db, delete_request.name)
 
    def update_food_category_labels(self, db: Session, name: str,
                                    ru_label: Optional[str], en_label: Optional[str],
                                    ru_provided: bool, en_provided: bool) -> Optional[FoodCategory]:
        """
        Update display-only labels (ru_label/en_label) for an existing FoodCategory without renaming.

        Args:
            db: Database session
            name: Category name (primary key) to update
            ru_label: New Russian display label (may be None to clear if ru_provided=True)
            en_label: New English display label (may be None to clear if en_provided=True)
            ru_provided: True if 'ru_label' was explicitly provided in the request payload
            en_provided: True if 'en_label' was explicitly provided in the request payload

        Returns:
            Updated FoodCategory if found, None otherwise

        NOTE:
            - When a label is provided with value None, the stored value is cleared.
            - When a label is not provided, the stored value remains unchanged.
            - This method only performs field updates and db.flush(). It does NOT commit.
        """
        category = self.get_food_category_by_name(db, name)
        if not category:
            return None

        if ru_provided:
            category.ru_label = ru_label  # may be None → clear
        if en_provided:
            category.en_label = en_label  # may be None → clear

        db.flush()
        return category
 
 
# Global service instance
category_management_db_crud = CategoryManagementDBCRUD()