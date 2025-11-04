# ReceiptDBCRUD.py
# Database CRUD operations for Receipt management (SlipReceipt, FiscalReceipt, SummaryReceipt)
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from ..database.models import (
    SlipReceipt,
    FiscalReceipt,
    SummaryReceipt,
    Order
)


class ReceiptDBCRUD:
    """Database CRUD operations for Receipt management"""

    # SlipReceipt operations
    def create_slip_receipt(self, db: Session, order_id: int, 
                           pos_terminal_returned_id: Optional[str],
                           receipt_body: Optional[Dict[str, Any]],
                           created_by: Optional[str] = None) -> SlipReceipt:
        """
        Create new SlipReceipt in the database.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_slip_receipt = SlipReceipt(
            order_id=order_id,
            receipt_pos_terminal_returned_id=pos_terminal_returned_id,
            receipt_body=receipt_body,
            created_by=created_by
        )

        db.add(db_slip_receipt)
        db.flush()  # Generate slip_receipt_id

        return db_slip_receipt

    def get_slip_receipt_by_id(self, db: Session, slip_receipt_id: UUID) -> Optional[SlipReceipt]:
        """Get slip receipt by ID."""
        return db.query(SlipReceipt).filter(
            SlipReceipt.slip_receipt_id == slip_receipt_id
        ).first()

    def get_slip_receipts_by_order_id(self, db: Session, order_id: int) -> List[SlipReceipt]:
        """Get all slip receipts for a specific order."""
        return db.query(SlipReceipt).filter(
            SlipReceipt.order_id == order_id
        ).all()

    # FiscalReceipt operations
    def create_fiscal_receipt(self, db: Session, order_id: int,
                             fiscal_machine_returned_id: Optional[str],
                             receipt_body: Optional[Dict[str, Any]],
                             created_by: Optional[str] = None) -> FiscalReceipt:
        """
        Create new FiscalReceipt in the database.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_fiscal_receipt = FiscalReceipt(
            order_id=order_id,
            receipt_fiscal_machine_returned_id=fiscal_machine_returned_id,
            receipt_body=receipt_body,
            created_by=created_by
        )

        db.add(db_fiscal_receipt)
        db.flush()  # Generate fiscal_receipt_id

        return db_fiscal_receipt

    def get_fiscal_receipt_by_id(self, db: Session, fiscal_receipt_id: UUID) -> Optional[FiscalReceipt]:
        """Get fiscal receipt by ID."""
        return db.query(FiscalReceipt).filter(
            FiscalReceipt.fiscal_receipt_id == fiscal_receipt_id
        ).first()

    def get_fiscal_receipts_by_order_id(self, db: Session, order_id: int) -> List[FiscalReceipt]:
        """Get all fiscal receipts for a specific order."""
        return db.query(FiscalReceipt).filter(
            FiscalReceipt.order_id == order_id
        ).all()

    # SummaryReceipt operations
    def create_summary_receipt(self, db: Session, order_id: int,
                              slip_receipt_id: Optional[UUID] = None,
                              fiscal_receipt_id: Optional[UUID] = None,
                              pickup_code: Optional[str] = None,
                              pin_code: Optional[str] = None,
                              created_by: Optional[str] = None) -> SummaryReceipt:
        """
        Create new SummaryReceipt in the database.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_summary_receipt = SummaryReceipt(
            order_id=order_id,
            slip_receipt_id=slip_receipt_id,
            fiscal_receipt_id=fiscal_receipt_id,
            pickup_code=pickup_code,
            pin_code=pin_code,
            created_by=created_by
        )

        db.add(db_summary_receipt)
        db.flush()  # Generate summary_receipt_id

        return db_summary_receipt

    def get_summary_receipt_by_id(self, db: Session, summary_receipt_id: UUID) -> Optional[SummaryReceipt]:
        """Get summary receipt by ID with related receipts."""
        return db.query(SummaryReceipt).options(
            joinedload(SummaryReceipt.slip_receipt),
            joinedload(SummaryReceipt.fiscal_receipt),
            joinedload(SummaryReceipt.order)
        ).filter(SummaryReceipt.summary_receipt_id == summary_receipt_id).first()

    def get_summary_receipt_by_order_id(self, db: Session, order_id: int) -> Optional[SummaryReceipt]:
        """Get summary receipt for a specific order."""
        return db.query(SummaryReceipt).options(
            joinedload(SummaryReceipt.slip_receipt),
            joinedload(SummaryReceipt.fiscal_receipt)
        ).filter(SummaryReceipt.order_id == order_id).first()

    def get_summary_receipts_by_pickup_code(self, db: Session, pickup_code: str) -> List[SummaryReceipt]:
        """Get summary receipts by pickup code."""
        return db.query(SummaryReceipt).options(
            joinedload(SummaryReceipt.order)
        ).filter(SummaryReceipt.pickup_code == pickup_code).all()

    # Validation methods
    def validate_order_exists(self, db: Session, order_id: int) -> Optional[Order]:
        """Validate that order exists."""
        return db.query(Order).filter(Order.order_id == order_id).first()

    def validate_slip_receipt_exists(self, db: Session, slip_receipt_id: UUID) -> Optional[SlipReceipt]:
        """Validate that slip receipt exists."""
        return db.query(SlipReceipt).filter(SlipReceipt.slip_receipt_id == slip_receipt_id).first()

    def validate_fiscal_receipt_exists(self, db: Session, fiscal_receipt_id: UUID) -> Optional[FiscalReceipt]:
        """Validate that fiscal receipt exists."""
        return db.query(FiscalReceipt).filter(FiscalReceipt.fiscal_receipt_id == fiscal_receipt_id).first()

    # Analytics and reporting methods
    def get_receipts_count_by_date(self, db: Session, receipt_date: datetime) -> Dict[str, int]:
        """Get count of receipts by type for a specific date."""
        slip_count = db.query(SlipReceipt).filter(
            SlipReceipt.created_at >= receipt_date.date(),
            SlipReceipt.created_at < receipt_date.date().replace(day=receipt_date.day + 1)
        ).count()
        
        fiscal_count = db.query(FiscalReceipt).filter(
            FiscalReceipt.created_at >= receipt_date.date(),
            FiscalReceipt.created_at < receipt_date.date().replace(day=receipt_date.day + 1)
        ).count()
        
        summary_count = db.query(SummaryReceipt).filter(
            SummaryReceipt.created_at >= receipt_date.date(),
            SummaryReceipt.created_at < receipt_date.date().replace(day=receipt_date.day + 1)
        ).count()
        
        return {
            "slip_receipts": slip_count,
            "fiscal_receipts": fiscal_count,
            "summary_receipts": summary_count
        }


# Global service instance
receipt_db_crud = ReceiptDBCRUD()