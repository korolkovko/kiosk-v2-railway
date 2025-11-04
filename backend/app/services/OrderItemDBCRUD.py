# OrderItemDBCRUD.py
# Database CRUD operations for OrderItem management
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from uuid import UUID

from ..database.models import OrderItem, Order


class OrderItemDBCRUD:
    """Database CRUD operations for OrderItem management"""

    def get_order_item_by_id(self, db: Session, item_in_order_id: UUID) -> Optional[OrderItem]:
        """Get order item by ID."""
        return db.query(OrderItem).filter(
            OrderItem.item_in_order_id == item_in_order_id
        ).first()

    def get_order_items_by_order_id(self, db: Session, order_id: int) -> List[OrderItem]:
        """Get all order items for a specific order."""
        return db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).all()

    def update_order_item_wishes(self, db: Session, item_in_order_id: UUID, 
                                new_wishes: str) -> Optional[OrderItem]:
        """
        Update order item wishes/preferences.

        NOTE: No commit here. Logic layer handles transaction.
        """
        order_item = db.query(OrderItem).filter(
            OrderItem.item_in_order_id == item_in_order_id
        ).first()
        
        if order_item:
            order_item.wishes = new_wishes
            db.flush()
        
        return order_item

    def delete_order_item(self, db: Session, item_in_order_id: UUID) -> bool:
        """
        Delete order item (soft delete by removing from order).

        NOTE: No commit here. Logic layer handles transaction.
        """
        order_item = db.query(OrderItem).filter(
            OrderItem.item_in_order_id == item_in_order_id
        ).first()
        
        if order_item:
            db.delete(order_item)
            db.flush()
            return True
        
        return False

    def get_order_items_with_order_details(self, db: Session, order_id: int) -> List[OrderItem]:
        """Get order items with related order information."""
        return db.query(OrderItem).options(
            joinedload(OrderItem.order)
        ).filter(OrderItem.order_id == order_id).all()

    def validate_order_exists(self, db: Session, order_id: int) -> Optional[Order]:
        """Validate that order exists."""
        return db.query(Order).filter(Order.order_id == order_id).first()

    def get_order_items_count(self, db: Session, order_id: int) -> int:
        """Get count of items in an order."""
        return db.query(OrderItem).filter(OrderItem.order_id == order_id).count()

    def get_order_items_by_item_id(self, db: Session, item_id: int, 
                                  limit: int = 50, offset: int = 0) -> List[OrderItem]:
        """Get order items by original item ID (for analytics)."""
        return db.query(OrderItem).options(
            joinedload(OrderItem.order)
        ).filter(OrderItem.item_id == item_id).offset(offset).limit(limit).all()


# Global service instance
order_item_db_crud = OrderItemDBCRUD()