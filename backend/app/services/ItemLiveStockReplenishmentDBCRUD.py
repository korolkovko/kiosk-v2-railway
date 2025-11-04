# ItemLiveStockReplenishmentDBCRUD.py
# Database CRUD operations for stock replenishment/removal
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional
from ..database.models import (
    ItemLive,
    ItemLiveAvailable,
    UnitOfMeasure,
    ItemLiveStockReplenishment
)



class ItemLiveStockReplenishmentDBCRUD:
    """Database CRUD operations for LiveItem stock replenishment/removal"""

    def get_item_available(self, db: Session, item_id: int) -> Optional[ItemLiveAvailable]:
        return db.query(ItemLiveAvailable).filter(ItemLiveAvailable.item_id == item_id).first()

    def update_stock_quantity(self, db: Session, item_available: ItemLiveAvailable, new_quantity: int) -> ItemLiveAvailable:
        item_available.stock_quantity = new_quantity
        db.flush()
        return item_available

    def create_stock_replenishment(self, db: Session, item_available: ItemLiveAvailable, change_quantity: int, changed_by_username: str) -> ItemLiveStockReplenishment:
        """
        Create stock replenishment log entry.
        
        Args:
            db: Database session
            item_available: ItemLiveAvailable instance
            change_quantity: Quantity change (positive for replenishment, negative for deduction)
            changed_by_username: Username or identifier of who made the change (e.g., 'admin_user', 'SYSTEM', 'KIOSK_AUTO')
        """
        db_log = ItemLiveStockReplenishment(
            item_id=item_available.item_id,
            name_ru=item_available.item.name_ru,
            description_ru=item_available.item.description_ru,
            unit_name_ru=item_available.unit_name_ru,
            unit_name_eng=item_available.unit_name_eng,
            change_quantity=change_quantity,
            changed_by=changed_by_username  # Now accepts username string instead of user_id
        )
        db.add(db_log)
        db.flush()
        return db_log

# Global service instance
item_live_stock_replenishment_db_crud = ItemLiveStockReplenishmentDBCRUD()