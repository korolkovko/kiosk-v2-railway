# OrderLogic.py
# Business logic for Order creation and FSM initialization
# NOTE: This layer manages order creation transaction and hands off to FSM orchestrator
# Follows Option 1: Simple OrderLogic - create order, initialize FSM, hand off to orchestrator
# All money calculations use integer kopecks for consistency with payment/fiscal integrations

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List
import asyncio

from ..models.OrderPydanticModels import OrderCreateRequest, OrderResponse, OrderCommandRequest, OrderCommandResponse
from ..services.OrderDBCRUD import order_db_crud
from ..services.OrderItemDBCRUD import order_item_db_crud
from ..services.OrderFSMKioskRuntimeDBCRUD import order_fsm_kiosk_runtime_db_crud
from ..services.ItemLiveStockReplenishmentDBCRUD import item_live_stock_replenishment_db_crud
from ..orchestrator.fsm_orchestrator import start_order_fsm, process_fsm_event
from ..orchestrator.fsm_spec import Event
from ..database.models import ActorType, OrderStatus
from sqlalchemy.exc import SQLAlchemyError


class OrderLogic:
    """Business logic for Order creation and FSM initialization"""

    async def create_order(self, db: Session, order_data: OrderCreateRequest,
                          kiosk_username: str, created_by_user_id: int) -> dict:
        """
        Simple order creation logic:
        1. Validate items and calculate totals
        2. Create Order + OrderItems in single transaction
        3. Initialize FSM runtime
        4. Hand off to FSM orchestrator (fire-and-forget)
        5. Return basic order info immediately
        
        This method handles ONLY order creation and FSM initialization.
        All subsequent FSM transitions are handled by FSM orchestrator.
        """
        try:
            # Step 1: Validate items and calculate totals
            total_net, total_vat, total_gross = await self._validate_and_calculate_totals(db, order_data.items)
            
            # Step 2: Validate optional references
            if order_data.customer_id:
                if not order_db_crud.validate_customer_exists(db, order_data.customer_id):
                    raise HTTPException(status_code=400, detail=f"Customer {order_data.customer_id} not found")
            
            if order_data.session_id:
                if not order_db_crud.validate_session_exists(db, str(order_data.session_id)):
                    raise HTTPException(status_code=400, detail=f"Session {order_data.session_id} not found")
            
            # Step 3: Generate pickup identifiers
            pickup_number = order_db_crud.generate_pickup_number(db)
            pin_code = order_db_crud.generate_pin_code(db)
            
            # Step 4: Create Order in database
            order = order_db_crud.create_order(
                db=db,
                order_data=order_data,
                total_net_kopecks=total_net,
                total_vat_kopecks=total_vat,
                total_gross_kopecks=total_gross,
                pickup_number=pickup_number,
                pin_code=pin_code
            )
            
            # Step 5: Create OrderItems
            for item_request in order_data.items:
                item_live = order_db_crud.get_item_live_by_id(db, item_request.item_id)
                if not item_live:
                    raise HTTPException(status_code=400, detail=f"Item {item_request.item_id} not found")
                
                order_db_crud.create_order_item(db, order.order_id, item_request, item_live)
            
            # Step 6: Initialize FSM runtime
            fsm_runtime = await start_order_fsm(order.order_id, kiosk_username, db)

            # Step 7: Commit transaction (Order + OrderItems + FSM runtime created)
            db.commit()

            # Step 8: FSM is now in INIT state
            # The FSM state handler or orchestration layer should pick up from here
            # and trigger the appropriate external service calls (fiscalization, payment, etc.)

            # Step 9: Return complete response with all financial fields and FSM state
            return {
                "order_id": order.order_id,
                "status": order.status.value,
                "pickup_number": pickup_number,
                "pin_code": pin_code,
                "total_amount_net_kopecks": total_net,
                "total_amount_vat_kopecks": total_vat,
                "total_amount_gross_kopecks": total_gross,
                "currency": order.currency,
                "fsm_state": fsm_runtime.fsm_kiosk_state.value if fsm_runtime else "INIT",
                "payment_status": "AWAITING",  # Initial payment status
                "order_time": order.order_time.isoformat()
            }

        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as db_err:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def get_order_by_id(self, db: Session, order_id: int) -> dict:
        """Get basic order info by ID."""
        order = order_db_crud.get_order_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "pickup_number": order.pickup_number,
            "pin_code": order.pin_code,
            "total_amount_gross_kopecks": order.total_amount_gross_kopecks,
            "currency": order.currency,
            "order_time": order.order_time.isoformat()
        }

    async def process_order_command(self, db: Session, order_id: int, 
                                   command: OrderCommandRequest, kiosk_username: str) -> OrderCommandResponse:
        """
        Process order command (retry payment, cancel, etc.).
        This method validates the command and hands off to FSM orchestrator.
        """
        try:
            # Validate order exists
            order = order_db_crud.get_order_by_id(db, order_id)
            if not order:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            
            # Map command action to FSM event
            event_mapping = {
                "RETRY_PAYMENT": Event.PAYMENT_FAILED,  # Will trigger retry logic in FSM
                "CANCEL_ORDER": Event.USER_CANCELED,
                "RETRY_FISCALIZATION": Event.FISCALIZATION_FAILED,
                "RETRY_PRINTING": Event.PRINTING_FAILED_OR_TIMEOUT
            }
            
            if command.action not in event_mapping:
                raise HTTPException(status_code=400, detail=f"Unknown command action: {command.action}")
            
            # Hand off to FSM orchestrator
            fsm_event = event_mapping[command.action]
            success = await process_fsm_event(
                order_id=order_id,
                event=fsm_event,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.CUSTOMER,
                comment=f"Command: {command.action}",
                event_data=command.parameters
            )
            
            if success:
                # Get updated order state
                fsm_runtime = order_fsm_kiosk_runtime_db_crud.get_fsm_runtime_by_order_id(db, order_id)
                current_state = fsm_runtime.fsm_kiosk_state.value if fsm_runtime else "UNKNOWN"
                
                return OrderCommandResponse(
                    ack=True,
                    state=current_state,
                    message=f"Command {command.action} processed successfully",
                    operation_id=command.operation_id
                )
            else:
                return OrderCommandResponse(
                    ack=False,
                    message=f"Command {command.action} could not be processed",
                    operation_id=command.operation_id
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Command processing error: {str(e)}")

    async def _validate_and_calculate_totals(self, db: Session, items: List) -> tuple[int, int, int]:
        """Validate items and calculate order totals in kopecks."""
        total_net_kopecks = 0
        total_vat_kopecks = 0
        total_gross_kopecks = 0
        
        for item_request in items:
            # Validate item exists, is active, and is not archived
            item_live = order_db_crud.get_item_live_by_id(db, item_request.item_id)
            if not item_live:
                raise HTTPException(status_code=400, detail=f"Item {item_request.item_id} not found")
            
            if not item_live.is_active:
                raise HTTPException(status_code=400, detail=f"Item {item_request.item_id} is not active")
            
            if item_live.is_archived:
                raise HTTPException(status_code=400, detail=f"Item {item_request.item_id} is archived and cannot be ordered")
            
            # Check stock availability
            if item_live.availability and item_live.availability.stock_quantity < item_request.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for item {item_request.item_id}. Available: {item_live.availability.stock_quantity}, Requested: {item_request.quantity}"
                )
            
            # Calculate line totals in kopecks (integer arithmetic)
            line_net_kopecks = item_live.price_net_kopecks * item_request.quantity
            line_vat_kopecks = item_live.vat_amount_kopecks * item_request.quantity
            line_gross_kopecks = item_live.price_gross_kopecks * item_request.quantity
            
            total_net_kopecks += line_net_kopecks
            total_vat_kopecks += line_vat_kopecks
            total_gross_kopecks += line_gross_kopecks
        
        return total_net_kopecks, total_vat_kopecks, total_gross_kopecks


# Global logic instance
order_logic = OrderLogic()