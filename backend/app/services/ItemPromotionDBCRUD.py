# ItemPromotionDBCRUD.py
# Database CRUD operations for item promotion toggle functionality

from sqlalchemy.orm import Session
from typing import Optional

from ..database.models import ItemLive
from ..models.ItemPromotionPydanticModel import ItemPromotionRequest

class ItemPromotionDBCRUD:
    """Database CRUD operations for item promotion management"""

    def get_item_by_id(self, db: Session, item_id: int) -> Optional[ItemLive]:
        """Fetch ItemLive by ID"""
        return db.query(ItemLive).filter(ItemLive.item_id == item_id).first()

    def update_item_promotion_status(self, db: Session, item: ItemLive, promoted: bool) -> ItemLive:
        """Update item promotion status"""
        item.promoted = promoted
        db.flush()
        return item

# Global service instance
item_promotion_db_crud = ItemPromotionDBCRUD()