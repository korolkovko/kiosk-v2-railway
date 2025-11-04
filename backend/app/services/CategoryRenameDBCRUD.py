# CategoryRenameDBCRUD.py
# Database CRUD operations for Category Rename with cascade updates
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

from ..database.models import FoodCategory, ItemLive, MenuCategory, MenuItem
from ..models.CategoryRenameEndpointPydanticModel import RenameCategoryRequest


class CategoryRenameDBCRUD:
    """Database CRUD operations for Category Rename with cascade updates"""

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

    def count_items_using_food_category(self, db: Session, category_name: str) -> int:
        """
        Count how many ItemLive records reference the given FoodCategory.
        
        Args:
            db: Database session
            category_name: Name of the food category to check
            
        Returns:
            Number of ItemLive records referencing this category
        """
        return db.query(ItemLive).filter(ItemLive.food_category_name == category_name).count()

    def rename_food_category_with_cascade(self, db: Session, current_name: str, new_name: str) -> int:
        """
        Rename FoodCategory using Create-New-Update-Refs-Delete-Old approach to avoid FK constraint violations.

        NOTE: This method only performs database operations and db.flush().
        It does NOT commit. The Logic layer manages the transaction.

        Strategy:
        1. Create new FoodCategory with new name
        2. Update all MenuCategory references from old name to new name
        3. Update all MenuItem references from old name to new name
        4. Update all ItemLive references from old name to new name
        5. Delete old FoodCategory (safe after references updated)

        Args:
            db: Database session
            current_name: Current category name
            new_name: New category name

        Returns:
            Number of ItemLive records that were updated

        Raises:
            SQLAlchemyError: If database operation fails
        """
        # Step 1: Get the existing category to copy its attributes
        old_food_category = self.get_food_category_by_name(db, current_name)
        if not old_food_category:
            return 0

        # Step 2: Create new category with new name (copying attributes)
        new_food_category = FoodCategory(
            name=new_name
            # Note: created_at will be set automatically by server_default
        )
        db.add(new_food_category)
        db.flush()  # Ensure new category is created and available

        # Step 3: Update all MenuCategory records to reference the new category
        db.query(MenuCategory).filter(
            MenuCategory.food_category_name == current_name
        ).update(
            {MenuCategory.food_category_name: new_name},
            synchronize_session=False
        )
        db.flush()  # Ensure MenuCategory updates are processed

        # Step 4: Update all MenuItem records to reference the new category
        db.query(MenuItem).filter(
            MenuItem.food_category_name == current_name
        ).update(
            {MenuItem.food_category_name: new_name},
            synchronize_session=False
        )
        db.flush()  # Ensure MenuItem updates are processed

        # Step 5: Update all ItemLive records to reference the new category
        items_updated = db.query(ItemLive).filter(
            ItemLive.food_category_name == current_name
        ).update(
            {ItemLive.food_category_name: new_name},
            synchronize_session=False
        )
        db.flush()  # Ensure all ItemLive updates are processed

        # Step 6: Delete the old category (safe since no references remain)
        db.delete(old_food_category)
        db.flush()  # Ensure old category is deleted

        return items_updated

    def rename_food_category_with_cascade_with_labels(self, db: Session, rename_request: RenameCategoryRequest) -> int:
        """
        Rename FoodCategory using Create-New-Update-Refs-Delete-Old approach, handling optional ru/en label overrides.

        Behavior:
        - If rename_request.ru_label / en_label provided → set on the new category
        - Else → copy labels from the old category

        NOTE: This method only performs database operations and db.flush().
        It does NOT commit. The Logic layer manages the transaction.
        """
        # Step 1: Get existing category
        old_food_category = self.get_food_category_by_name(db, rename_request.current_name)
        if not old_food_category:
            return 0

        # Determine resulting labels
        ru_label_new = getattr(rename_request, "ru_label", None)
        en_label_new = getattr(rename_request, "en_label", None)

        # Step 2: Create new category with labels (override if provided, else copy)
        new_food_category = FoodCategory(
            name=rename_request.new_name,
            ru_label=ru_label_new if ru_label_new is not None else old_food_category.ru_label,
            en_label=en_label_new if en_label_new is not None else old_food_category.en_label,
        )
        db.add(new_food_category)
        db.flush()

        # Step 3: Update MenuCategory references
        db.query(MenuCategory).filter(
            MenuCategory.food_category_name == rename_request.current_name
        ).update(
            {MenuCategory.food_category_name: rename_request.new_name},
            synchronize_session=False
        )
        db.flush()

        # Step 4: Update MenuItem references
        db.query(MenuItem).filter(
            MenuItem.food_category_name == rename_request.current_name
        ).update(
            {MenuItem.food_category_name: rename_request.new_name},
            synchronize_session=False
        )
        db.flush()

        # Step 5: Update ItemLive references
        items_updated = db.query(ItemLive).filter(
            ItemLive.food_category_name == rename_request.current_name
        ).update(
            {ItemLive.food_category_name: rename_request.new_name},
            synchronize_session=False
        )
        db.flush()

        # Step 6: Delete old category
        db.delete(old_food_category)
        db.flush()

        return items_updated

    def validate_rename_request(self, db: Session, rename_request: RenameCategoryRequest) -> Tuple[bool, str, int]:
        """
        Validate category rename request for FoodCategory only.
        
        Args:
            db: Database session
            rename_request: Category rename request data
            
        Returns:
            Tuple of (is_valid, error_message, items_count)
            - is_valid: True if validation passes, False otherwise
            - error_message: Error description if validation fails, empty string if valid
            - items_count: Number of ItemLive records that would be affected by the rename
        """
        # Basic validation: names must differ
        if rename_request.new_name == rename_request.current_name:
            return False, "New name must be different from current name", 0

        # Check if current category exists
        current_category = self.get_food_category_by_name(db, rename_request.current_name)
        if not current_category:
            return False, f"Food category '{rename_request.current_name}' not found", 0

        # New name must be unique
        if self.check_food_category_name_exists(db, rename_request.new_name):
            items_count = self.count_items_using_food_category(db, rename_request.current_name)
            return False, f"Food category '{rename_request.new_name}' already exists", items_count

        # Impact count = number of items that will be updated
        items_count = self.count_items_using_food_category(db, rename_request.current_name)
        return True, "", items_count

    def rename_category_with_cascade_by_type(self, db: Session, rename_request: RenameCategoryRequest) -> int:
        """
        Rename category with cascade updates.

        Note: Endpoint simplified to FoodCategory only. This method now delegates
        directly to the food category rename implementation.
        
        Args:
            db: Database session
            rename_request: Category rename request data
            
        Returns:
            Number of ItemLive records that were updated
        """
        # Use method that handles ru_label/en_label overrides or copies old labels
        return self.rename_food_category_with_cascade_with_labels(db, rename_request)


# Global service instance
category_rename_db_crud = CategoryRenameDBCRUD()