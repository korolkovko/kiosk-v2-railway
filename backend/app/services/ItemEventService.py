# ItemEventService.py
# Shared service for publishing item-related SSE events to kiosk clients
# Updated to send kopeck amounts to frontend

from typing import List
from ..websockets.event_bus import bus
from ..models.SSEEventModels import (
    ItemStatusChangedEvent,
    ItemPromotionChangedEvent,
    ItemStockChangedEvent,
    ItemCreatedEvent,
    ItemPropertiesChangedEvent,
    SSEEvent
)
from ..database.models import ItemLive, ItemLiveAvailable

class ItemEventService:
    """Service for publishing item-related events to all kiosk clients"""
    
    KIOSK_BROADCAST_CHANNEL = "kiosk_broadcast"
    
    async def publish_item_status_changed(self, item: ItemLive) -> None:
        """Publish item active status change event"""
        event = ItemStatusChangedEvent(
            item_id=item.item_id,
            is_active=item.is_active
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def publish_item_promotion_changed(self, item: ItemLive) -> None:
        """Publish item promotion status change event"""
        event = ItemPromotionChangedEvent(
            item_id=item.item_id,
            promoted=item.promoted
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def publish_item_stock_changed(
        self, 
        availability: ItemLiveAvailable, 
        change_quantity: int,
        changed_by: str
    ) -> None:
        """Publish item stock quantity change event"""
        event = ItemStockChangedEvent(
            item_id=availability.item_id,
            stock_quantity=availability.stock_quantity,
            change_quantity=change_quantity,
            changed_by=changed_by
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def publish_item_created(self, item: ItemLive, stock_quantity: int = 0) -> None:
        """Publish new item creation event with kopeck amounts"""
        event = ItemCreatedEvent(
            item_id=item.item_id,
            name_ru=item.name_ru,
            name_eng=item.name_eng,
            description_ru=item.description_ru,
            description_eng=item.description_eng,
            unit_measure_name_eng=item.unit_measure_name_eng,
            food_category_name=item.food_category_name,
            price_net_kopecks=str(item.price_net_kopecks),
            vat_rate=str(item.vat_rate) if item.vat_rate else None,
            vat_amount_kopecks=str(item.vat_amount_kopecks),
            price_gross_kopecks=str(item.price_gross_kopecks),
            is_active=item.is_active,
            promoted=item.promoted,
            stock_quantity=stock_quantity
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def publish_item_properties_changed(self, item: ItemLive) -> None:
        """Publish item properties change event with kopeck amounts"""
        event = ItemPropertiesChangedEvent(
            item_id=item.item_id,
            name_ru=item.name_ru,
            name_eng=item.name_eng,
            description_ru=item.description_ru,
            description_eng=item.description_eng,
            unit_measure_name_eng=item.unit_measure_name_eng,
            food_category_name=item.food_category_name,
            price_net_kopecks=str(item.price_net_kopecks),
            vat_rate=str(item.vat_rate) if item.vat_rate else None,
            vat_amount_kopecks=str(item.vat_amount_kopecks),
            price_gross_kopecks=str(item.price_gross_kopecks)
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def _broadcast_to_all_kiosks(self, event: SSEEvent) -> None:
        """Broadcast event to all connected kiosk clients"""
        # Use mode='json' to apply json_encoders (converts datetime to ISO string)
        event_dict = event.model_dump(mode='json')
        print(f"🔴 PUBLISHING SSE EVENT to '{self.KIOSK_BROADCAST_CHANNEL}': {event_dict}")
        print(f"🔍 EVENT BUS SUBSCRIBERS: {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} active subscribers")
        await bus.publish(self.KIOSK_BROADCAST_CHANNEL, event_dict)
        print(f"✅ EVENT PUBLISHED to {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} subscribers")

# Global service instance
item_event_service = ItemEventService()