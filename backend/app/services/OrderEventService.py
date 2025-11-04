# OrderEventService.py
# Shared service for publishing order-related SSE events to kiosk clients
# Follows the same pattern as ItemEventService.py for consistency

from typing import Optional
from ..websockets.event_bus import bus
from ..models.SSEEventModels import (
    OrderStatusChangedEvent,
    OrderEventTriggeredEvent,
    SSEEvent
)
from ..database.models import Order, OrderStatus
from ..orchestrator.fsm_spec import State, Event


class OrderEventService:
    """Service for publishing order-related events to all kiosk clients"""

    KIOSK_BROADCAST_CHANNEL = "kiosk_broadcast"

    async def publish_order_status_changed(
        self,
        order: Order,
        previous_status: Optional[OrderStatus] = None,
        kiosk_username: Optional[str] = None
    ) -> None:
        """
        Publish order status change event

        Event includes kiosk_username for frontend filtering.
        Frontend will only process events matching the current kiosk's username.
        Follows the same pattern as KIOSK_SERVICE_MODE_CHANGED event.

        Args:
            order: Order object
            previous_status: Previous order status (optional)
            kiosk_username: Username of kiosk that owns this order (for frontend filtering)
        """
        # Default to 'unknown' if not provided (shouldn't happen in normal flow)
        kiosk_username = kiosk_username or 'unknown'

        event = OrderStatusChangedEvent(
            order_id=order.order_id,
            kiosk_username=kiosk_username,
            status=order.status.value,
            previous_status=previous_status.value if previous_status else None
        )
        await self._broadcast_to_all_kiosks(event)
    
    async def publish_order_event_triggered(
        self,
        order_id: int,
        fsm_event: Event,
        current_state: State,
        previous_state: Optional[State] = None,
        actor_type: Optional[str] = None,
        kiosk_username: Optional[str] = None
    ) -> None:
        """
        Publish FSM event triggered during order processing

        Event includes kiosk_username for frontend filtering.
        Frontend will only process events matching the current kiosk's username.
        Follows the same pattern as KIOSK_SERVICE_MODE_CHANGED event.

        Args:
            order_id: ID of the order
            fsm_event: FSM event that was triggered
            current_state: Current FSM state
            previous_state: Previous FSM state (optional)
            actor_type: Type of actor that triggered the event (FISCAL_DEVICE, POS_TERMINAL, PRINTER, KITCHEN, SYSTEM)
            kiosk_username: Username of kiosk that owns this order (for frontend filtering)
        """
        # Default to 'unknown' if not provided (shouldn't happen in normal flow)
        kiosk_username = kiosk_username or 'unknown'

        event = OrderEventTriggeredEvent(
            order_id=order_id,
            kiosk_username=kiosk_username,
            fsm_event=fsm_event.value,
            fsm_state=current_state.value,
            previous_state=previous_state.value if previous_state else None,
            actor_type=actor_type
        )
        await self._broadcast_to_all_kiosks(event)
        print(f"🔔 ORDER_EVENT_TRIGGERED published for order {order_id} (kiosk: {kiosk_username}): {fsm_event.value} → {current_state.value}")

    async def _broadcast_to_all_kiosks(self, event: SSEEvent) -> None:
        """
        Broadcast event to all connected kiosk clients.
        Fire-and-forget pattern - doesn't wait for frontend responses.
        Safe against frontend glitches or non-responsive clients.

        Note:
            Events are broadcast to ALL kiosks via 'kiosk_broadcast' channel.
            Frontend filters events by kiosk_username field (for order events and service mode).
            Global events (stock, menu, media) have no kiosk_username and are processed by all.
        """
        try:
            # Use mode='json' to apply json_encoders (converts datetime to ISO string)
            event_dict = event.model_dump(mode='json')
            print(f"🔴 PUBLISHING ORDER SSE EVENT to '{self.KIOSK_BROADCAST_CHANNEL}': {event_dict}")
            print(f"🔍 EVENT BUS SUBSCRIBERS: {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} active subscribers")
            print(f"📡 EVENT TYPE: {event_dict.get('event_type')} for ORDER: {event_dict.get('order_id')} (KIOSK: {event_dict.get('kiosk_username', 'N/A')})")

            # Fire-and-forget publish - doesn't wait for frontend responses
            await bus.publish(self.KIOSK_BROADCAST_CHANNEL, event_dict)
            print(f"✅ ORDER EVENT PUBLISHED to {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} subscribers")
            print(f"🎯 Published event details: {event_dict.get('event_type')} - {event_dict.get('fsm_event', 'N/A')} - {event_dict.get('fsm_state', 'N/A')}")

        except Exception as e:
            # Log error but don't fail the order processing
            print(f"❌ Failed to publish order SSE event: {str(e)}")
            print(f"🔄 Order processing continues despite SSE publish failure")


# Global service instance
order_event_service = OrderEventService()