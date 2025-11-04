# PromotedLabelDBCRUD.py
# Database CRUD operations for Promoted Label (single-record configuration)
# NOTE: This layer does not perform commit/rollback. Transaction management is in the Logic layer.

from typing import Optional
from sqlalchemy.orm import Session

from ..database.models import PromotedLabel
from ..models.PromotedLabelModels import PromotedLabelCreateRequest, PromotedLabelUpdateRequest


class PromotedLabelDBCRUD:
    """Database CRUD operations for Promoted Label"""

    def get_any(self, db: Session) -> Optional[PromotedLabel]:
        """Return the single promoted label record if it exists (table should have at most one row)."""
        return db.query(PromotedLabel).first()

    def get_by_name(self, db: Session, name: str) -> Optional[PromotedLabel]:
        """Return promoted label by its primary key name."""
        return db.query(PromotedLabel).filter(PromotedLabel.name == name).first()

    def count(self, db: Session) -> int:
        """Return total number of records (should be 0 or 1)."""
        return db.query(PromotedLabel).count()

    def create_label(self, db: Session, data: PromotedLabelCreateRequest) -> PromotedLabel:
        """
        Create a new promoted label record.

        NOTE: This method only performs db.add() and db.flush(). It does NOT commit.
        """
        entity = PromotedLabel(
            name=data.name,
            ru_label=data.ru_label,
            en_label=data.en_label,
        )
        db.add(entity)
        db.flush()
        return entity

    def update_label(self, db: Session, data: PromotedLabelUpdateRequest) -> Optional[PromotedLabel]:
        """
        Update existing promoted label identified by name.

        NOTE: This method only performs field updates and db.flush(). It does NOT commit.
        """
        entity = self.get_by_name(db, data.name)
        if not entity:
            return None

        if data.ru_label is not None:
            entity.ru_label = data.ru_label
        if data.en_label is not None:
            entity.en_label = data.en_label

        db.flush()
        return entity


# Global service instance
promoted_label_db_crud = PromotedLabelDBCRUD()