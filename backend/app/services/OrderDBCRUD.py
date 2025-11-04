# OrderDBCRUD.py
# Database CRUD operations for Order management
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.
# All money operations now use integer kopecks for consistency

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
import random
import string

from ..database.models import (
    Order,
    OrderItem,
    OrderStatus,
    KnownCustomer,
    Session as SessionModel,
    ItemLive
)
from ..models.OrderPydanticModels import OrderCreateRequest, OrderItemRequest


class OrderDBCRUD:
    """Database CRUD operations for Order management"""

    def create_order(self, db: Session, order_data: OrderCreateRequest,
                    total_net_kopecks: int, total_vat_kopecks: int, total_gross_kopecks: int,
                    pickup_number: str, pin_code: str) -> Order:
        """
        Create new Order in the database with kopeck amounts.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_order = Order(
            order_date=date.today(),
            status=OrderStatus.PENDING,
            currency=order_data.currency,
            total_amount_net_kopecks=total_net_kopecks,
            total_amount_vat_kopecks=total_vat_kopecks,
            total_amount_gross_kopecks=total_gross_kopecks,
            customer_id=order_data.customer_id,
            session_id=order_data.session_id,
            pickup_number=pickup_number,
            pin_code=pin_code
        )

        db.add(db_order)
        db.flush()  # Generate order_id (required for order items)

        return db_order

    def create_order_item(self, db: Session, order_id: int, item_request: OrderItemRequest,
                         item_live: ItemLive) -> OrderItem:
        """
        Create OrderItem with snapshots from ItemLive using kopeck amounts.

        NOTE: No commit/refresh here. Return object immediately.
        """
        # Calculate totals in kopecks (integer arithmetic)
        total_net_kopecks = item_live.price_net_kopecks * item_request.quantity
        total_vat_kopecks = item_live.vat_amount_kopecks * item_request.quantity
        total_gross_kopecks = item_live.price_gross_kopecks * item_request.quantity

        db_order_item = OrderItem(
            order_id=order_id,
            item_id=item_live.item_id,
            name_ru=item_live.name_ru,
            name_eng=item_live.name_eng,
            description_ru=item_live.description_ru,
            description_eng=item_live.description_eng,
            unit_of_measure_ru=item_live.unit_measure.name_eng,  # Using name_eng as primary
            unit_of_measure_eng=item_live.unit_measure.name_eng,
            item_price_net_kopecks=item_live.price_net_kopecks,
            item_vat_rate=item_live.vat_rate or Decimal('0'),
            item_vat_amount_kopecks=item_live.vat_amount_kopecks,
            item_price_gross_kopecks=item_live.price_gross_kopecks,
            quantity=item_request.quantity,
            total_price_net_kopecks=total_net_kopecks,
            applied_vat_rate=item_live.vat_rate or Decimal('0'),
            total_vat_amount_kopecks=total_vat_kopecks,
            total_price_gross_kopecks=total_gross_kopecks,
            wishes=item_request.wishes
        )

        db.add(db_order_item)
        return db_order_item

    def get_order_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID with all related data."""
        return db.query(Order).options(
            joinedload(Order.order_items),
            joinedload(Order.customer),
            joinedload(Order.session),
            joinedload(Order.payments),
            joinedload(Order.fsm_runtime),
            joinedload(Order.lifecycle_logs)
        ).filter(Order.order_id == order_id).first()

    def get_orders_by_status(self, db: Session, status: OrderStatus, 
                           limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders by status with pagination."""
        return db.query(Order).options(
            joinedload(Order.order_items),
            joinedload(Order.customer)
        ).filter(Order.status == status).offset(offset).limit(limit).all()

    def get_orders_by_date(self, db: Session, order_date: date,
                          limit: int = 50, offset: int = 0) -> List[Order]:
        """Get orders by date with pagination."""
        return db.query(Order).options(
            joinedload(Order.order_items),
            joinedload(Order.customer)
        ).filter(Order.order_date == order_date).offset(offset).limit(limit).all()

    def update_order_status(self, db: Session, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """
        Update order status.

        NOTE: No commit here. Logic layer handles transaction.
        """
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = new_status
            db.flush()
        return order

    def get_item_live_by_id(self, db: Session, item_id: int) -> Optional[ItemLive]:
        """Get ItemLive by ID with unit measure relationship."""
        return db.query(ItemLive).options(
            joinedload(ItemLive.unit_measure),
            joinedload(ItemLive.availability)
        ).filter(ItemLive.item_id == item_id).first()

    def validate_customer_exists(self, db: Session, customer_id: int) -> Optional[KnownCustomer]:
        """Validate that customer exists."""
        return db.query(KnownCustomer).filter(KnownCustomer.customer_id == customer_id).first()

    def validate_session_exists(self, db: Session, session_id: str) -> Optional[SessionModel]:
        """Validate that session exists."""
        return db.query(SessionModel).filter(SessionModel.session_id == session_id).first()

    def generate_pickup_number(self, db: Session) -> str:
        """
        Generate unique pickup number for order.
        Format: 3-digit number (001-999)
        """
        # Simple implementation - in production might want date-based or more sophisticated logic
        for _ in range(100):  # Try up to 100 times
            pickup_num = f"{random.randint(1, 999):03d}"
            existing = db.query(Order).filter(
                Order.pickup_number == pickup_num,
                Order.order_date == date.today()
            ).first()
            if not existing:
                return pickup_num
        
        # Fallback to timestamp-based if all numbers taken
        return f"{datetime.now().strftime('%H%M%S')}"[-3:]

    def generate_pin_code(self, db: Session) -> str:
        """
        Generate unique PIN code for order.
        Format: 4-digit number (1000-9999)
        """
        for _ in range(100):  # Try up to 100 times
            pin = f"{random.randint(1000, 9999)}"
            existing = db.query(Order).filter(
                Order.pin_code == pin,
                Order.order_date == date.today()
            ).first()
            if not existing:
                return pin
        
        # Fallback to timestamp-based if all PINs taken
        return f"{datetime.now().strftime('%M%S')}{random.randint(10, 99)}"

    def get_order_count_by_status(self, db: Session, status: OrderStatus) -> int:
        """Get count of orders by status."""
        return db.query(Order).filter(Order.status == status).count()

    def get_order_count_by_date(self, db: Session, order_date: date) -> int:
        """Get count of orders by date."""
        return db.query(Order).filter(Order.order_date == order_date).count()


# Global service instance
order_db_crud = OrderDBCRUD()