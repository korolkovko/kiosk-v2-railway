# GetAllItemLiveDBCRUD.py
# Database CRUD operations for listing all LiveItems

from sqlalchemy.orm import Session
from typing import List
from ..database.models import ItemLive

class GetAllItemLiveDBCRUD:
    """Database CRUD operations for listing all LiveItems"""

    def get_all_item_live(self, db: Session) -> List[ItemLive]:
        return db.query(ItemLive).all()

# Global service instance
get_all_item_live_db_crud = GetAllItemLiveDBCRUD()