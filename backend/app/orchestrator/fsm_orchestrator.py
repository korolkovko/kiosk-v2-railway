# fsm_orchestrator.py
# FSM orchestration logic for managing order state transitions and coordinating with EventBus

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .fsm_spec import State, Event, next_state, can_transition, is_terminal, state_timeout, is_retry_allowed
from ..database.models import OrderFSMKioskRuntime, OrderLifecycleLog, ActorType
from ..websockets.event_bus import bus
from ..services.OrderEventService import order_event_service


class FSMOrchestrator:
    """
    FSM orchestration engine for managing order state transitions.
    Handles state changes, logging, and event publishing via EventBus.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._active_timers: Dict[int, asyncio.Task] = {}  # order_id -> timer task
    
    async def initialize_fsm(self, order_id: int, kiosk_username: str) -> OrderFSMKioskRuntime:
        """
        Initialize FSM runtime for a new order.
        Creates FSM runtime record and logs initial transition.
        """
        try:
            # Create FSM runtime record
            fsm_runtime = OrderFSMKioskRuntime(
                order_id=order_id,
                fsm_kiosk_state=State.INIT,
                created_at=datetime.utcnow()
            )
            self.db.add(fsm_runtime)
            self.db.flush()  # Get the ID
            
            # Log initial state
            await self._log_transition(
                order_id=order_id,
                fsm_runtime_id=fsm_runtime.order_fsm_kiosk_runtime_id,
                from_state=None,
                to_state=State.INIT,
                trigger_event=None,  # Initial state has no trigger
                actor_type=ActorType.SYSTEM,
                comment="FSM initialized for new order"
            )
            
            self.db.commit()
            
            # CRITICAL FIX: Trigger state handler for initial INIT state
            # This was missing - state handler only called during transitions, not initialization
            async def trigger_initial_state_handler():
                try:
                    from .fsm_state_handler import handle_state_change
                    from ..database.connection import SessionLocal

                    # Create new DB session for async handler
                    db_handler = SessionLocal()
                    try:
                        await handle_state_change(order_id, State.INIT, kiosk_username, db_handler)
                    finally:
                        db_handler.close()
                except Exception as e:
                    # Log error but don't crash
                    print(f"ERROR in initial state handler for order {order_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # Start the state handler asynchronously (fire-and-forget)
            asyncio.create_task(trigger_initial_state_handler())
            
            return fsm_runtime
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to initialize FSM for order {order_id}: {str(e)}")
    
    async def transition_state(
        self,
        order_id: int,
        trigger_event: Event,
        kiosk_username: str,
        actor_type: Optional[ActorType] = None,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempt to transition FSM state based on trigger event.
        Returns True if transition was successful, False otherwise.
        """
        try:
            # Get current FSM runtime
            fsm_runtime = self.db.query(OrderFSMKioskRuntime).filter(
                OrderFSMKioskRuntime.order_id == order_id
            ).first()
            
            if not fsm_runtime:
                raise Exception(f"FSM runtime not found for order {order_id}")
            
            current_state = fsm_runtime.fsm_kiosk_state
            
            # Check if transition is valid
            if not can_transition(current_state, trigger_event):
                await self._log_invalid_transition(
                    order_id, fsm_runtime.order_fsm_kiosk_runtime_id,
                    current_state, trigger_event, actor_type, actor_id
                )
                return False
            
            # Get next state
            new_state = next_state(current_state, trigger_event)
            if not new_state:
                return False
            
            # Update FSM runtime
            fsm_runtime.fsm_kiosk_state = new_state
            fsm_runtime.updated_at = datetime.utcnow()
            
            # Update context based on event data
            if event_data:
                await self._update_fsm_context(fsm_runtime, trigger_event, event_data)
            
            # Log successful transition
            await self._log_transition(
                order_id=order_id,
                fsm_runtime_id=fsm_runtime.order_fsm_kiosk_runtime_id,
                from_state=current_state,
                to_state=new_state,
                trigger_event=trigger_event,
                actor_type=actor_type,
                actor_id=actor_id,
                comment=comment
            )
            
            # Cancel any existing timer for this order
            await self._cancel_timer(order_id)
            
            # Set up new timer if needed
            if not is_terminal(new_state):
                await self._setup_state_timer(order_id, new_state, kiosk_username)

            # Publish FSM event triggered via SSE (fire-and-forget, safe)
            try:
                await order_event_service.publish_order_event_triggered(
                    order_id=order_id,
                    fsm_event=trigger_event,
                    current_state=new_state,
                    previous_state=current_state,
                    actor_type=actor_type.value if actor_type else None,
                    kiosk_username=kiosk_username
                )
            except Exception as sse_error:
                # Log error but don't fail the FSM transition
                print(f"❌ Failed to publish FSM event SSE: {sse_error}")

            self.db.commit()

            # Trigger state handler asynchronously (fire-and-forget)
            # This will call external services based on the new state
            async def trigger_state_handler():
                try:
                    from .fsm_state_handler import handle_state_change
                    from ..database.connection import SessionLocal

                    # Create new DB session for async handler
                    db_handler = SessionLocal()
                    try:
                        await handle_state_change(order_id, new_state, kiosk_username, db_handler)
                    finally:
                        db_handler.close()
                except Exception as e:
                    # Log error but don't crash
                    print(f"ERROR in state handler for order {order_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()

            asyncio.create_task(trigger_state_handler())

            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to transition state for order {order_id}: {str(e)}")
    
    async def get_fsm_state(self, order_id: int) -> Optional[OrderFSMKioskRuntime]:
        """Get current FSM runtime state for an order."""
        return self.db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.order_id == order_id
        ).first()
    
    async def get_valid_events(self, order_id: int) -> List[Event]:
        """Get list of valid events for current order state."""
        fsm_runtime = await self.get_fsm_state(order_id)
        if not fsm_runtime:
            return []
        
        from .fsm_spec import valid_events
        return valid_events(fsm_runtime.fsm_kiosk_state)
    
    async def is_retry_allowed_for_order(self, order_id: int) -> bool:
        """Check if retry is allowed for current order state."""
        fsm_runtime = await self.get_fsm_state(order_id)
        if not fsm_runtime:
            return False
        
        return is_retry_allowed(fsm_runtime.fsm_kiosk_state)
    
    async def _log_transition(
        self,
        order_id: int,
        fsm_runtime_id: uuid.UUID,
        from_state: Optional[State],
        to_state: State,
        trigger_event: Optional[Event],
        actor_type: Optional[ActorType] = None,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """Log state transition to OrderLifecycleLog."""
        log_entry = OrderLifecycleLog(
            order_id=order_id,
            order_fsm_kiosk_runtime_id=fsm_runtime_id,
            from_state=from_state,
            to_state=to_state,
            trigger_event=trigger_event,
            actor_type=actor_type,
            actor_id=actor_id,
            comment=comment,
            event_created_at=datetime.utcnow()
        )
        self.db.add(log_entry)
    
    async def _log_invalid_transition(
        self,
        order_id: int,
        fsm_runtime_id: uuid.UUID,
        current_state: State,
        invalid_event: Event,
        actor_type: Optional[ActorType],
        actor_id: Optional[str]
    ):
        """Log invalid transition attempt."""
        log_entry = OrderLifecycleLog(
            order_id=order_id,
            order_fsm_kiosk_runtime_id=fsm_runtime_id,
            from_state=current_state,
            to_state=current_state,  # No state change
            trigger_event=invalid_event,
            actor_type=actor_type,
            actor_id=actor_id,
            comment=f"Invalid transition: {current_state.value} + {invalid_event.value}",
            event_created_at=datetime.utcnow()
        )
        self.db.add(log_entry)
    
    async def _update_fsm_context(
        self,
        fsm_runtime: OrderFSMKioskRuntime,
        trigger_event: Event,
        event_data: Dict[str, Any]
    ):
        """Update FSM runtime context based on event data."""
        if trigger_event in [Event.PAYMENT_SUCCEEDED, Event.PAYMENT_FAILED]:
            # Update payment context
            fsm_runtime.payment_session_id = event_data.get("session_id")
            fsm_runtime.pos_terminal_id = event_data.get("pos_terminal_id")
            fsm_runtime.payment_attempt_result_code = event_data.get("result_code")
            fsm_runtime.payment_attempt_result_description = event_data.get("result_description")
            fsm_runtime.payment_id_transaction = event_data.get("transaction_id")
            
            if trigger_event == Event.PAYMENT_SUCCEEDED:
                fsm_runtime.payment_attempt_response_at = datetime.utcnow()
        
        elif trigger_event in [Event.FISCALIZATION_SUCCEEDED, Event.FISCALIZATION_FAILED]:
            # Update fiscal context
            fsm_runtime.fiscal_session_id = event_data.get("session_id")
            fsm_runtime.fiscal_device_id = event_data.get("fiscal_device_id")
            fsm_runtime.fiscal_attempt_result_code = event_data.get("result_code")
            fsm_runtime.fiscal_attempt_result_description = event_data.get("result_description")
            fsm_runtime.fiscal_id_transaction = event_data.get("transaction_id")
            
            if trigger_event == Event.FISCALIZATION_SUCCEEDED:
                fsm_runtime.fiscal_attempt_response_at = datetime.utcnow()
    
    async def _setup_state_timer(self, order_id: int, state: State, kiosk_username: str):
        """Set up timeout timer for a state if applicable."""
        timeout_seconds = state_timeout(state)
        if not timeout_seconds:
            return
        
        async def timeout_handler():
            await asyncio.sleep(timeout_seconds)
            # Trigger timeout event based on state
            if state == State.AWAITING_PAYMENT:
                await self.transition_state(
                    order_id=order_id,
                    trigger_event=Event.INACTIVITY_TIMEOUT,
                    kiosk_username=kiosk_username,
                    actor_type=ActorType.SYSTEM,
                    comment=f"Timeout after {timeout_seconds}s in {state.value}"
                )
            elif state == State.AWAITING_KDS:
                await self.transition_state(
                    order_id=order_id,
                    trigger_event=Event.KDS_ERROR_OR_NO_RESPONSE,
                    kiosk_username=kiosk_username,
                    actor_type=ActorType.SYSTEM,
                    comment=f"KDS timeout after {timeout_seconds}s"
                )
        
        # Store timer task for potential cancellation
        timer_task = asyncio.create_task(timeout_handler())
        self._active_timers[order_id] = timer_task
    
    async def _cancel_timer(self, order_id: int):
        """Cancel any active timer for an order."""
        if order_id in self._active_timers:
            timer_task = self._active_timers.pop(order_id)
            if not timer_task.done():
                timer_task.cancel()
                try:
                    await timer_task
                except asyncio.CancelledError:
                    pass
    
    async def cleanup_order_timers(self, order_id: int):
        """Clean up all timers for an order (call when order is completed/cancelled)."""
        await self._cancel_timer(order_id)
    
    async def recover_incomplete_fsm_states(self, kiosk_username: str):
        """
        Recovery method to handle FSM states that were interrupted by system restart.
        Should be called on application startup.
        """
        incomplete_fsms = self.db.query(OrderFSMKioskRuntime).filter(
            OrderFSMKioskRuntime.fsm_kiosk_state.notin_([
                State.SENT_TO_KDS,
                State.SENT_TO_KDS_FAILED,
                State.CANCELED_BY_USER,
                State.CANCELED_BY_TIMEOUT,
                State.UNSUCCESSFUL_PAYMENT,
                State.PRINTING_FAILED,
                State.UNSUCCESSFUL_FISCALIZATION
            ])
        ).all()
        
        for fsm_runtime in incomplete_fsms:
            # Log recovery attempt
            await self._log_transition(
                order_id=fsm_runtime.order_id,
                fsm_runtime_id=fsm_runtime.order_fsm_kiosk_runtime_id,
                from_state=fsm_runtime.fsm_kiosk_state,
                to_state=fsm_runtime.fsm_kiosk_state,
                trigger_event=None,
                actor_type=ActorType.SYSTEM,
                comment="FSM recovery on system restart"
            )
            
            # Restart timers for non-terminal states
            if not is_terminal(fsm_runtime.fsm_kiosk_state):
                await self._setup_state_timer(
                    fsm_runtime.order_id,
                    fsm_runtime.fsm_kiosk_state,
                    kiosk_username
                )
        
        self.db.commit()


# Global orchestrator instance (will be initialized with DB session)
_orchestrator: Optional[FSMOrchestrator] = None


def get_fsm_orchestrator(db_session: Session) -> FSMOrchestrator:
    """Get or create FSM orchestrator instance."""
    return FSMOrchestrator(db_session)


async def start_order_fsm(order_id: int, kiosk_username: str, db_session: Session) -> OrderFSMKioskRuntime:
    """
    Start FSM for a new order.
    This is the entry point called after order creation.
    """
    orchestrator = get_fsm_orchestrator(db_session)
    return await orchestrator.initialize_fsm(order_id, kiosk_username)


async def process_fsm_event(
    order_id: int,
    event: Event,
    kiosk_username: str,
    db_session: Session,
    actor_type: Optional[ActorType] = None,
    actor_id: Optional[str] = None,
    comment: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Process an FSM event for an order.
    This is the main entry point for external systems to trigger state changes.
    """
    orchestrator = get_fsm_orchestrator(db_session)
    return await orchestrator.transition_state(
        order_id=order_id,
        trigger_event=event,
        kiosk_username=kiosk_username,
        actor_type=actor_type,
        actor_id=actor_id,
        comment=comment,
        event_data=event_data
    )


async def get_order_fsm_state(order_id: int, db_session: Session) -> Optional[OrderFSMKioskRuntime]:
    """Get current FSM state for an order."""
    orchestrator = get_fsm_orchestrator(db_session)
    return await orchestrator.get_fsm_state(order_id)


async def get_order_valid_events(order_id: int, db_session: Session) -> List[Event]:
    """Get valid events for current order state."""
    orchestrator = get_fsm_orchestrator(db_session)
    return await orchestrator.get_valid_events(order_id)