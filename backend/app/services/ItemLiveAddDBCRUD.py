# ItemLiveAddDBCRUD.py
# Database CRUD operations for LiveItem creation
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.
# All money operations now use integer kopecks

from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

from ..database.models import (
    ItemLive,
    ItemLiveAvailable,
    UnitOfMeasure,
    FoodCategory
)
from ..models.ItemLiveAddPydanticModel import ItemLiveCreateRequest


class ItemLiveAddDBCRUD:
    """Database CRUD operations for LiveItem creation"""

    def create_item_live(self, db: Session, item_data: ItemLiveCreateRequest,
                         created_by: int, vat_amount_kopecks: int,
                         price_gross_kopecks: int) -> ItemLive:
        """
        Create new LiveItem in the database with kopeck amounts.

        NOTE: This method only performs db.add() and db.flush().
        It does NOT commit. This allows Logic layer to manage full transaction.
        """
        db_item = ItemLive(
            name_ru=item_data.name_ru,
            name_eng=item_data.name_eng,
            description_ru=item_data.description_ru,
            description_eng=item_data.description_eng,
            unit_measure_name_eng=item_data.unit_measure_name_eng,
            food_category_name=item_data.food_category_name,
            price_net_kopecks=item_data.price_net_kopecks,
            vat_rate=item_data.vat_rate,
            vat_amount_kopecks=vat_amount_kopecks,
            price_gross_kopecks=price_gross_kopecks,
            is_active=item_data.is_active,
            created_by=created_by
        )

        db.add(db_item)
        db.flush()  # Generate item_id (required for availability relation)

        return db_item

    def create_item_available(self, db: Session, item: ItemLive, unit: UnitOfMeasure) -> ItemLiveAvailable:
        """
        Create availability record for new item.

        NOTE: No commit/refresh here. Return object immediately.
        """
        db_available = ItemLiveAvailable(
            item_id=item.item_id,
            stock_quantity=0,
            reserved_quantity=0,
            unit_name_ru=unit.name_eng,  # Use name_eng since UnitOfMeasure only has name_eng field
            unit_name_eng=unit.name_eng
        )

        db.add(db_available)
        return db_available

    def validate_unit_exists(self, db: Session, unit_name_eng: str) -> Optional[UnitOfMeasure]:
        return db.query(UnitOfMeasure).filter(UnitOfMeasure.name_eng == unit_name_eng).first()

    def validate_food_category_exists(self, db: Session, category_name: str) -> Optional[FoodCategory]:
        return db.query(FoodCategory).filter(FoodCategory.name == category_name).first()

    def check_item_name_exists(self, db: Session, name_ru: str) -> bool:
        return db.query(ItemLive).filter(ItemLive.name_ru == name_ru).first() is not None


# Global service instance
item_live_add_db_crud = ItemLiveAddDBCRUD()