# ItemStopListDBCRUD.py
# Database CRUD operations for updating LiveItem stop list status
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional

from ..database.models import ItemLive

class ItemStopListDBCRUD:
    """Database CRUD operations for LiveItem stop list update"""

    def get_item(self, db: Session, item_id: int) -> Optional[ItemLive]:
        """Fetch LiveItem by ID"""
        return db.query(ItemLive).filter(ItemLive.item_id == item_id).first()

    def update_status(self, db: Session, item: ItemLive, is_active: bool) -> ItemLive:
        """Update the is_active status of LiveItem"""
        item.is_active = is_active
        db.flush()
        return item

# Global service instance
item_stop_list_db_crud = ItemStopListDBCRUD()