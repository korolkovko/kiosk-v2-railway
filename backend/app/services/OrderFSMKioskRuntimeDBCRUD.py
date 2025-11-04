# OrderFSMKioskRuntimeDBCRUD.py
# Database CRUD operations for OrderFSMKioskRuntime management
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..database.models import (
    OrderFSMKioskRuntime,
    OrderLifecycleLog,
    Order,
    Device
)
from ..orchestrator.fsm_spec import State, Event


class OrderFSMKioskRuntimeDBCRUD:
    """Database CRUD operations for OrderFSMKioskRuntime management"""

    def create_fsm_runtime(self, db: Session, order_id: int) -> OrderFSMKioskRuntime:
        """
        Create new FSM runtime for an order.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_fsm_runtime = OrderFSMKioskRuntime(
            order_id=order_id,
            fsm_kiosk_state=State.INIT
        )

        db.add(db_fsm_runtime)
        db.flush()  # Generate runtime_id

        return db_fsm_runtime

    def get_fsm_runtime_by_order_id(self, db: Session, order_id: int) -> Optional[OrderFSMKioskRuntime]:
        """Get FSM runtime by order ID."""
        return db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()

    def get_fsm_runtime_by_id(self, db: Session, runtime_id: UUID) -> Optional[OrderFSMKioskRuntime]:
        """Get FSM runtime by runtime ID."""
        return db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_fsm_kiosk_runtime_id == runtime_id
        ).first()

    def update_fsm_state(self, db: Session, order_id: int, new_state: State) -> Optional[OrderFSMKioskRuntime]:
        """
        Update FSM state for an order.

        NOTE: No commit here. Logic layer handles transaction.
        """
        fsm_runtime = db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
        
        if fsm_runtime:
            fsm_runtime.fsm_kiosk_state = new_state
            fsm_runtime.updated_at = datetime.utcnow()
            db.flush()
        
        return fsm_runtime

    def update_payment_context(self, db: Session, order_id: int, 
                              payment_context: Dict[str, Any]) -> Optional[OrderFSMKioskRuntime]:
        """
        Update payment context in FSM runtime.

        NOTE: No commit here. Logic layer handles transaction.
        """
        fsm_runtime = db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
        
        if fsm_runtime:
            fsm_runtime.payment_session_id = payment_context.get("session_id")
            fsm_runtime.pos_terminal_id = payment_context.get("pos_terminal_id")
            fsm_runtime.payment_attempt_started_at = payment_context.get("started_at")
            fsm_runtime.payment_attempt_response_at = payment_context.get("response_at")
            fsm_runtime.payment_attempt_result_code = payment_context.get("result_code")
            fsm_runtime.payment_attempt_result_description = payment_context.get("result_description")
            fsm_runtime.payment_id_transaction = payment_context.get("transaction_id")
            fsm_runtime.payment_slip_number_id = payment_context.get("slip_number_id")
            fsm_runtime.updated_at = datetime.utcnow()
            db.flush()
        
        return fsm_runtime

    def update_fiscal_context(self, db: Session, order_id: int,
                             fiscal_context: Dict[str, Any]) -> Optional[OrderFSMKioskRuntime]:
        """
        Update fiscal context in FSM runtime.

        NOTE: No commit here. Logic layer handles transaction.
        """
        fsm_runtime = db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
        
        if fsm_runtime:
            fsm_runtime.fiscal_session_id = fiscal_context.get("session_id")
            fsm_runtime.fiscal_device_id = fiscal_context.get("fiscal_device_id")
            fsm_runtime.fiscal_attempt_started_at = fiscal_context.get("started_at")
            fsm_runtime.fiscal_attempt_response_at = fiscal_context.get("response_at")
            fsm_runtime.fiscal_attempt_result_code = fiscal_context.get("result_code")
            fsm_runtime.fiscal_attempt_result_description = fiscal_context.get("result_description")
            fsm_runtime.fiscal_id_transaction = fiscal_context.get("transaction_id")
            fsm_runtime.fiscalisation_number_id = fiscal_context.get("fiscalisation_number_id")
            fsm_runtime.updated_at = datetime.utcnow()
            db.flush()
        
        return fsm_runtime

    def update_printing_context(self, db: Session, order_id: int,
                               printing_context: Dict[str, Any]) -> Optional[OrderFSMKioskRuntime]:
        """
        Update printing context in FSM runtime.

        NOTE: No commit here. Logic layer handles transaction.
        """
        fsm_runtime = db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
        
        if fsm_runtime:
            fsm_runtime.printing_session_id = printing_context.get("session_id")
            fsm_runtime.printing_device_id = printing_context.get("printing_device_id")
            fsm_runtime.printing_attempt_started_at = printing_context.get("started_at")
            fsm_runtime.printing_attempt_response_at = printing_context.get("response_at")
            fsm_runtime.printing_attempt_result_code = printing_context.get("result_code")
            fsm_runtime.printing_attempt_result_description = printing_context.get("result_description")
            fsm_runtime.updated_at = datetime.utcnow()
            db.flush()
        
        return fsm_runtime

    def update_pickup_context(self, db: Session, order_id: int,
                             pickup_code: str, pin_code: str, qr_code: Optional[str] = None) -> Optional[OrderFSMKioskRuntime]:
        """
        Update pickup context in FSM runtime.

        NOTE: No commit here. Logic layer handles transaction.
        """
        fsm_runtime = db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
        
        if fsm_runtime:
            fsm_runtime.pickup_code = pickup_code
            fsm_runtime.pin_code = pin_code
            fsm_runtime.qr_code = qr_code
            fsm_runtime.updated_at = datetime.utcnow()
            db.flush()
        
        return fsm_runtime

    def get_fsm_runtimes_by_state(self, db: Session, state: State,
                                 limit: int = 50, offset: int = 0) -> List[OrderFSMKioskRuntime]:
        """Get FSM runtimes by current state."""
        return db.query(OrderFSMKioskRuntime).options(
            joinedload(OrderFSMKioskRuntime.order)
        ).filter(OrderFSMKioskRuntime.fsm_kiosk_state == state).offset(offset).limit(limit).all()

    def get_incomplete_fsm_runtimes(self, db: Session) -> List[OrderFSMKioskRuntime]:
        """
        Get all FSM runtimes that are not in terminal states.
        Used for recovery operations.
        """
        terminal_states = [
            State.SENT_TO_KDS,
            State.SENT_TO_KDS_FAILED,
            State.CANCELED_BY_USER,
            State.CANCELED_BY_TIMEOUT,
            State.UNSUCCESSFUL_PAYMENT,
            State.PRINTING_FAILED,
            State.UNSUCCESSFUL_FISCALIZATION
        ]
        
        return db.query(OrderFSMKioskRuntime).options(
            joinedload(OrderFSMKioskRuntime.order)
        ).filter(~OrderFSMKioskRuntime.fsm_kiosk_state.in_(terminal_states)).all()

    def get_fsm_runtime_with_devices(self, db: Session, order_id: int) -> Optional[OrderFSMKioskRuntime]:
        """Get FSM runtime with related device information."""
        return db.query(OrderFSMKioskRuntime).options(
            joinedload(OrderFSMKioskRuntime.order),
            joinedload(OrderFSMKioskRuntime.pos_terminal),
            joinedload(OrderFSMKioskRuntime.fiscal_device),
            joinedload(OrderFSMKioskRuntime.printing_device)
        ).filter(OrderFSMKioskRuntime.order_id == order_id).first()

    def validate_order_exists(self, db: Session, order_id: int) -> Optional[Order]:
        """Validate that order exists."""
        return db.query(Order).filter(Order.order_id == order_id).first()

    def validate_device_exists(self, db: Session, device_id: int) -> Optional[Device]:
        """Validate that device exists."""
        return db.query(Device).filter(Device.device_id == device_id).first()


# Global service instance
order_fsm_kiosk_runtime_db_crud = OrderFSMKioskRuntimeDBCRUD()