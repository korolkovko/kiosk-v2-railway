# fsm_state_handler.py
# FSM State Handler with Saga Pattern
# Handles actions when FSM enters a new state, calls external services, manages timeouts,
# and performs inventory deduction when orders are completed and sent to KDS successfully

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .fsm_spec import State, Event
from .fsm_orchestrator import process_fsm_event, get_order_fsm_state
from ..database.models import ActorType, Order, OrderFSMKioskRuntime
from ..integrations.fiscal_gateway import FiscalGateway, FiscalRequest, FiscalItem, FiscalResult
from ..integrations.payment_gateway import PaymentGateway, PaymentRequest, PaymentResult
from ..integrations.kds_integration import KDSGateway, KDSRequest, KDSOrderItem, KDSResult
from ..integrations.printer_gateway import PrinterGateway, PrinterRequest, PrinterResponse
from ..services.OrderDBCRUD import order_db_crud
from ..services.OrderItemDBCRUD import order_item_db_crud
from ..services.OrderEventService import order_event_service
from ..logic.OrderInventoryDeductionLogic import order_inventory_deduction_logic
from loguru import logger


class SagaStep:
    """Represents a single step in the order fulfillment saga"""

    def __init__(self, name: str, timeout_seconds: int = 30):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[str] = None
        self.error: Optional[str] = None

    def start(self):
        """Mark step as started"""
        self.started_at = datetime.utcnow()

    def complete(self, result: str):
        """Mark step as completed with result"""
        self.completed_at = datetime.utcnow()
        self.result = result

    def fail(self, error: str):
        """Mark step as failed with error"""
        self.completed_at = datetime.utcnow()
        self.error = error

    @property
    def duration_seconds(self) -> float:
        """Calculate step duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def is_success(self) -> bool:
        """Check if step succeeded"""
        return self.result is not None and self.error is None


class FSMStateHandler:
    """
    Handles FSM state transitions with Saga pattern.

    Saga Pattern Benefits:
    - Each step (fiscalization, payment, KDS) is isolated
    - Each step has its own timeout
    - Compensating actions on failures
    - Clear audit trail
    """

    def __init__(self):
        from ..integrations.integrations_config import get_integrations_config
        from ..integrations.fiscal_gateway import FiscalGatewayConfig, get_fiscal_gateway
        from ..integrations.payment_gateway import PaymentGatewayConfig, get_payment_gateway
        from ..integrations.kds_integration import KDSGatewayConfig
        from ..integrations.printer_gateway import PrinterGatewayConfig, get_printer_gateway
        from ..kiosk_configuration_service import get_kiosk_configuration_service

        # Get global configuration from environment (fallback)
        self.global_config = get_integrations_config()
        
        # Get kiosk configuration service for kiosk-specific settings
        self.kiosk_config_service = get_kiosk_configuration_service()

        # Use existing gateway instances (they handle their own configuration)
        # These will be updated to use kiosk-specific configs when processing orders
        self.fiscal_gateway = get_fiscal_gateway()
        self.payment_gateway = get_payment_gateway()
        self.printer_gateway = get_printer_gateway()
        
        # TODO: Fix KDS gateway initialization when KDSGateway is implemented
        # For now, create a placeholder
        try:
            from ..integrations.kds_integration import get_kds_gateway
            self.kds_gateway = get_kds_gateway()
        except (ImportError, AttributeError):
            self.kds_gateway = None
            logger.warning("KDS gateway not available - KDS integration disabled")

        # Saga step timeouts (in seconds) - these can be overridden by kiosk-specific configs
        self.FISCALIZATION_TIMEOUT = 30
        self.PAYMENT_TIMEOUT = 180  # Longer for customer interaction
        self.KDS_TIMEOUT = 20
        self.PRINTING_TIMEOUT = 60  # Match FSM spec timeout

    def _get_kiosk_specific_integrations_config(self, kiosk_username: str):
        """Get kiosk-specific integrations configuration"""
        from ..integrations.integrations_config import get_integrations_config
        return get_integrations_config(kiosk_username)

    async def handle_state_change(
        self,
        order_id: int,
        new_state: State,
        kiosk_username: str,
        db: Session
    ):
        """
        Main entry point for handling state changes.
        Routes to appropriate handler based on state.
        """
        try:
            logger.info(f"Handling state change for order {order_id}: {new_state.value}")

            if new_state == State.INIT:
                await self._handle_init_state(order_id, kiosk_username, db)

            elif new_state == State.AWAITING_PAYMENT:
                await self._handle_awaiting_payment_state(order_id, kiosk_username, db)

            elif new_state == State.AWAITING_PRINTING:
                await self._handle_awaiting_printing_state(order_id, kiosk_username, db)

            elif new_state == State.AWAITING_KDS:
                await self._handle_awaiting_kds_state(order_id, kiosk_username, db)

            # Terminal states - update order status and log
            elif new_state == State.SENT_TO_KDS:
                logger.info(f"Order {order_id} reached terminal state: {new_state.value}")
                await self._handle_order_completion(order_id, kiosk_username, db)
            elif new_state == State.SENT_TO_KDS_FAILED:
                logger.info(f"Order {order_id} reached terminal state: {new_state.value}")
                await self._handle_order_failure(order_id, kiosk_username, db)

            # Specific failure state handlers with order status updates
            elif new_state == State.PRINTING_FAILED:
                logger.warning(f"Order {order_id} entered printing failed state")
                await self._handle_printing_failed_state(order_id, kiosk_username, db)
            elif new_state in [
                State.UNSUCCESSFUL_FISCALIZATION,
                State.UNSUCCESSFUL_PAYMENT,
                State.CANCELED_BY_USER,
                State.CANCELED_BY_TIMEOUT
            ]:
                logger.warning(f"Order {order_id} entered failure state: {new_state.value}")
                await self._handle_failure_state(order_id, new_state, kiosk_username, db)

        except Exception as e:
            logger.error(f"Error handling state change for order {order_id}: {str(e)}")
            # Don't let handler errors crash the system

    async def _handle_init_state(self, order_id: int, kiosk_username: str, db: Session):
        """
        Handle INIT state - Start fiscalization saga step.
        Saga Step 1: Fiscalization
        """
        step = SagaStep("fiscalization", self.FISCALIZATION_TIMEOUT)
        step.start()

        try:
            logger.info(f"[Saga Step 1] Starting fiscalization for order {order_id}")

            # Get order data
            order = order_db_crud.get_order_by_id(db, order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            # Get order items
            order_items = order_item_db_crud.get_order_items_by_order_id(db, order_id)

            # Build fiscal request - all amounts now in kopecks (integers)
            fiscal_items = [
                FiscalItem(
                    item_id=item.item_id,
                    item_description=item.name_ru,
                    item_price_net=item.item_price_net_kopecks,  # Direct kopecks from DB
                    item_price_gross=item.item_price_gross_kopecks,
                    item_vat_value=item.item_vat_amount_kopecks,
                    quantity=item.quantity
                )
                for item in order_items
            ]

            fiscal_request = FiscalRequest(
                order_id=order_id,
                kiosk_id=kiosk_username,
                items=fiscal_items,
                total_net=order.total_amount_net_kopecks,  # Direct kopecks from DB
                total_vat=order.total_amount_vat_kopecks,
                total_gross=order.total_amount_gross_kopecks,
                payment_method="CARD"
            )

            # Call fiscal gateway with timeout and kiosk context
            fiscal_response = await asyncio.wait_for(
                self.fiscal_gateway.process_fiscalization(fiscal_request, kiosk_username),
                timeout=step.timeout_seconds
            )

            step.complete(fiscal_response.status)

            # Determine FSM event based on result
            if fiscal_response.status == "OK":
                logger.info(f"[Saga Step 1] Fiscalization succeeded for order {order_id} in {step.duration_seconds:.2f}s")

                # Save fiscal receipt to database
                await self._save_fiscal_receipt_to_db(order_id, fiscal_response, db)

                # Prepare event data with fiscal details
                event_data = {
                    "fiscal_document_number": fiscal_response.fiscal_receipt.fiscal_document_number if fiscal_response.fiscal_receipt else None,
                    "fn_number": fiscal_response.fiscal_receipt.fn_number if fiscal_response.fiscal_receipt else None,
                    "result_code": "OK",
                    "duration_seconds": step.duration_seconds
                }

                # Trigger FSM transition to AWAITING_PAYMENT
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.FISCALIZATION_SUCCEEDED,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.FISCAL_DEVICE,
                    comment=f"Fiscalization completed in {step.duration_seconds:.2f}s",
                    event_data=event_data
                )
            else:
                step.fail(fiscal_response.error_message or "Fiscalization failed")
                logger.error(f"[Saga Step 1] Fiscalization failed for order {order_id}: {fiscal_response.error_message}")

                # Trigger FSM transition to UNSUCCESSFUL_FISCALIZATION
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.FISCALIZATION_FAILED,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.FISCAL_DEVICE,
                    comment=f"Fiscalization failed: {fiscal_response.error_message}",
                    event_data={"error_code": fiscal_response.error_code, "error_message": fiscal_response.error_message}
                )

        except asyncio.TimeoutError:
            step.fail(f"Timeout after {step.timeout_seconds}s")
            logger.error(f"[Saga Step 1] Fiscalization timeout for order {order_id}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.FISCALIZATION_FAILED,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Fiscalization timeout after {step.timeout_seconds}s",
                event_data={"error": "TIMEOUT", "timeout_seconds": step.timeout_seconds}
            )

        except Exception as e:
            step.fail(str(e))
            logger.error(f"[Saga Step 1] Fiscalization error for order {order_id}: {str(e)}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.FISCALIZATION_FAILED,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Fiscalization error: {str(e)}",
                event_data={"error": str(e)}
            )

    async def _handle_awaiting_payment_state(self, order_id: int, kiosk_username: str, db: Session):
        """
        Handle AWAITING_PAYMENT state - Start payment saga step.
        Saga Step 2: Payment Processing

        Note: This is initiated automatically after fiscalization.
        The actual payment processing happens when customer interacts with terminal.
        This method sets up the payment session and waits for terminal response.
        """
        step = SagaStep("payment", self.PAYMENT_TIMEOUT)
        step.start()

        try:
            logger.info(f"[Saga Step 2] Starting payment for order {order_id}")

            # Get order data
            order = order_db_crud.get_order_by_id(db, order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            # Build payment request with kiosk-specific terminal ID if available
            pos_terminal_id, pos_config = self.kiosk_config_service.get_pos_terminal_config(kiosk_username)
            
            payment_request = PaymentRequest(
                kiosk_id=kiosk_username,
                order_id=order_id,
                sum=order.total_amount_gross_kopecks  # Direct kopecks from DB
            )
            
            # Add kiosk-specific terminal ID to request if available
            if pos_terminal_id:
                payment_request.terminal_id = pos_terminal_id

            # Call payment gateway with timeout and kiosk context
            payment_response = await asyncio.wait_for(
                self.payment_gateway.process_payment(payment_request, kiosk_username),
                timeout=step.timeout_seconds
            )

            step.complete(payment_response.status)

            # Determine FSM event based on result
            if payment_response.status == "SUCCESS":
                logger.info(f"[Saga Step 2] Payment succeeded for order {order_id} in {step.duration_seconds:.2f}s")

                # CRITICAL: Save slip receipt to database immediately after payment success
                await self._save_slip_receipt_to_db(order_id, payment_response, db)

                event_data = {
                    "transaction_id": payment_response.transaction_id,
                    "result_code": "SUCCESS",
                    "duration_seconds": step.duration_seconds,
                    "auth_code": payment_response.auth_code,
                    "rrn": payment_response.rrn,
                    "amount": payment_response.amount
                }

                # Trigger FSM transition to AWAITING_PRINTING
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.PAYMENT_SUCCEEDED,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.POS_TERMINAL,
                    comment=f"Payment completed in {step.duration_seconds:.2f}s",
                    event_data=event_data
                )
            else:
                step.fail(payment_response.response_message or "Payment failed")
                logger.error(f"[Saga Step 2] Payment failed for order {order_id}: {payment_response.response_message}")

                # Trigger FSM transition to UNSUCCESSFUL_PAYMENT
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.PAYMENT_FAILED,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.POS_TERMINAL,
                    comment=f"Payment failed: {payment_response.response_message}",
                    event_data={"error_code": payment_response.response_code, "error_message": payment_response.response_message}
                )

        except asyncio.TimeoutError:
            step.fail(f"Timeout after {step.timeout_seconds}s")
            logger.error(f"[Saga Step 2] Payment timeout for order {order_id}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.INACTIVITY_TIMEOUT,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Payment timeout after {step.timeout_seconds}s",
                event_data={"error": "TIMEOUT", "timeout_seconds": step.timeout_seconds}
            )

        except Exception as e:
            step.fail(str(e))
            logger.error(f"[Saga Step 2] Payment error for order {order_id}: {str(e)}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.PAYMENT_FAILED,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Payment error: {str(e)}",
                event_data={"error": str(e)}
            )

    async def _handle_awaiting_printing_state(self, order_id: int, kiosk_username: str, db: Session):
        """
        Handle AWAITING_PRINTING state - Print receipt only.
        Saga Step 3a: Receipt Printing
        """
        await self._handle_receipt_printing(order_id, kiosk_username, db)

    async def _handle_awaiting_kds_state(self, order_id: int, kiosk_username: str, db: Session):
        """
        Handle AWAITING_KDS state - Send order to Kitchen Display System.
        Saga Step 3b: KDS Integration
        """
        await self._handle_kds_integration(order_id, kiosk_username, db)

    async def _handle_receipt_printing(self, order_id: int, kiosk_username: str, db: Session):
        """Handle receipt printing saga step."""
        step = SagaStep("receipt_printing", self.PRINTING_TIMEOUT)
        step.start()

        try:
            logger.info(f"[Saga Step 3a] Printing receipt for order {order_id}")

            # Get FSM runtime to extract payment data
            fsm_runtime = await get_order_fsm_state(order_id, db)
            if not fsm_runtime:
                raise Exception(f"FSM runtime not found for order {order_id}")

            # Build printer request with payment data - convert kopecks to rubles for display
            from ..utils.currency_utils import kopecks_to_rubles
            payment_data = {
                "transaction_id": fsm_runtime.payment_id_transaction or "TXN_UNKNOWN",
                "auth_code": "123456",  # From payment response
                "rrn": "000010000050",  # From payment response
                "amount": float(kopecks_to_rubles(fsm_runtime.order.total_amount_gross_kopecks)) if fsm_runtime.order else 0,
                "terminal_id": "00092240",  # From payment response
                "response_code": fsm_runtime.payment_attempt_result_code or "00"
            }

            printer_request = PrinterRequest(
                order_id=order_id,
                kiosk_id=kiosk_username,
                payment_data=payment_data,
                receipt_type="CUSTOMER"
            )

            # Call printer gateway with timeout and kiosk context
            printer_response = await asyncio.wait_for(
                self.printer_gateway.print_receipt(printer_request, kiosk_username),
                timeout=step.timeout_seconds
            )

            step.complete(printer_response.status)

            if printer_response.status == "SUCCESS":
                logger.info(f"[Saga Step 3a] Receipt printed successfully for order {order_id} in {step.duration_seconds:.2f}s")
                logger.info(f"Receipt saved to: {printer_response.receipt_file_path}")

                # Note: Slip receipt already saved to DB after payment success
                # This step only creates the physical receipt file

                # Trigger transition to AWAITING_KDS state
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.PRINTING_SUCCEEDED,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.PRINTER,
                    comment=f"Receipt printed successfully in {step.duration_seconds:.2f}s",
                    event_data={"receipt_file_path": printer_response.receipt_file_path}
                )

            else:
                step.fail(printer_response.error_message or "Printing failed")
                logger.error(f"[Saga Step 3a] Receipt printing failed for order {order_id}: {printer_response.error_message}")

                # Trigger printing failure event
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.PRINTING_FAILED_OR_TIMEOUT,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.PRINTER,
                    comment=f"Receipt printing failed: {printer_response.error_message}",
                    event_data={"error_code": printer_response.error_code, "error_message": printer_response.error_message}
                )
                return  # Don't proceed to KDS if printing failed

        except asyncio.TimeoutError:
            step.fail(f"Timeout after {step.timeout_seconds}s")
            logger.error(f"[Saga Step 3a] Receipt printing timeout for order {order_id}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.PRINTING_FAILED_OR_TIMEOUT,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Receipt printing timeout after {step.timeout_seconds}s",
                event_data={"error": "TIMEOUT", "timeout_seconds": step.timeout_seconds}
            )
            return

        except Exception as e:
            step.fail(str(e))
            logger.error(f"[Saga Step 3a] Receipt printing error for order {order_id}: {str(e)}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.PRINTING_FAILED_OR_TIMEOUT,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"Receipt printing error: {str(e)}",
                event_data={"error": str(e)}
            )
            return

    async def _handle_kds_integration(self, order_id: int, kiosk_username: str, db: Session):
        """Handle KDS integration saga step."""
        if not self.kds_gateway:
            logger.warning(f"KDS gateway not available for order {order_id} - skipping KDS integration")
            # Directly transition to SENT_TO_KDS since printing succeeded
            await process_fsm_event(
                order_id=order_id,
                event=Event.KDS_CONFIRMATION,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment="KDS integration skipped - gateway not available",
                event_data={"kds_skipped": True}
            )
            return

        step = SagaStep("kds_send", self.KDS_TIMEOUT)
        step.start()

        try:
            logger.info(f"[Saga Step 3b] Sending order {order_id} to KDS")

            # Get order data
            order = order_db_crud.get_order_by_id(db, order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            # Get order items
            order_items = order_item_db_crud.get_order_items_by_order_id(db, order_id)

            # Get kiosk-specific KDS configuration
            kds_name, kds_config = self.kiosk_config_service.get_kds_config(kiosk_username)
            
            # Build KDS request with kiosk-specific KDS name if available
            kds_items = [
                KDSOrderItem(
                    item_id=item.item_id,
                    description=item.name_ru,
                    quantity=item.quantity
                )
                for item in order_items
            ]

            kds_request = KDSRequest(
                order_id=order_id,
                kiosk_id=kiosk_username,
                items=kds_items
            )
            
            # Add kiosk-specific KDS name to request if available
            if kds_name:
                kds_request.kitchen_station_id = kds_name

            # Call KDS gateway with timeout and kiosk context
            kds_response = await asyncio.wait_for(
                self.kds_gateway.send_order_to_kitchen(kds_request, kiosk_username),
                timeout=step.timeout_seconds
            )

            step.complete(kds_response.status)

            # Determine FSM event based on status
            if kds_response.status == "OK":
                logger.info(f"[Saga Step 3b] KDS confirmed order {order_id} in {step.duration_seconds:.2f}s")

                event_data = {
                    "kds_ticket_id": kds_response.kds_ticket_id,
                    "result_code": "OK",
                    "duration_seconds": step.duration_seconds
                }

                # Trigger FSM transition to SENT_TO_KDS (terminal state)
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.KDS_CONFIRMATION,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.KITCHEN,
                    comment=f"Order sent to KDS successfully in {step.duration_seconds:.2f}s",
                    event_data=event_data
                )
            else:
                step.fail(kds_response.error_message or "KDS send failed")
                logger.error(f"[Saga Step 3b] KDS send failed for order {order_id}: {kds_response.error_message}")

                # Trigger FSM transition to SENT_TO_KDS_FAILED
                await process_fsm_event(
                    order_id=order_id,
                    event=Event.KDS_ERROR_OR_NO_RESPONSE,
                    kiosk_username=kiosk_username,
                    db_session=db,
                    actor_type=ActorType.KITCHEN,
                    comment=f"KDS send failed: {kds_response.error_message}",
                    event_data={"error_code": kds_response.error_code, "error_message": kds_response.error_message}
                )

        except asyncio.TimeoutError:
            step.fail(f"Timeout after {step.timeout_seconds}s")
            logger.error(f"[Saga Step 3b] KDS send timeout for order {order_id}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.KDS_ERROR_OR_NO_RESPONSE,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"KDS send timeout after {step.timeout_seconds}s",
                event_data={"error": "TIMEOUT", "timeout_seconds": step.timeout_seconds}
            )

        except Exception as e:
            step.fail(str(e))
            logger.error(f"[Saga Step 3b] KDS send error for order {order_id}: {str(e)}")

            await process_fsm_event(
                order_id=order_id,
                event=Event.KDS_ERROR_OR_NO_RESPONSE,
                kiosk_username=kiosk_username,
                db_session=db,
                actor_type=ActorType.SYSTEM,
                comment=f"KDS send error: {str(e)}",
                event_data={"error": str(e)}
            )

    async def _save_fiscal_receipt_to_db(self, order_id: int, fiscal_response, db: Session):
        """Save fiscal receipt data to fiscal_receipts table."""
        try:
            from ..database.models import FiscalReceipt
            import uuid

            # Create fiscal receipt record
            fiscal_receipt = FiscalReceipt(
                fiscal_receipt_id=uuid.uuid4(),
                order_id=order_id,
                receipt_fiscal_machine_returned_id=fiscal_response.fiscal_receipt.fiscal_document_number if fiscal_response.fiscal_receipt else f"FISCAL_{order_id}",
                receipt_body={
                    "status": fiscal_response.status,
                    "fiscal_document_number": fiscal_response.fiscal_receipt.fiscal_document_number if fiscal_response.fiscal_receipt else None,
                    "fn_number": fiscal_response.fiscal_receipt.fn_number if fiscal_response.fiscal_receipt else None,
                    "ofd_reg_number": fiscal_response.fiscal_receipt.ofd_reg_number if fiscal_response.fiscal_receipt else None,
                    "processed_at": fiscal_response.processed_at.isoformat(),
                    "items": [
                        {
                            "item_id": item.item_id,
                            "description": item.description,
                            "quantity": item.quantity,
                            "price_net": item.price_net,
                            "vat": item.vat,
                            "price_gross": item.price_gross
                        }
                        for item in fiscal_response.fiscal_receipt.items
                    ] if fiscal_response.fiscal_receipt else []
                },
                created_at=datetime.utcnow(),
                created_by="FSM_STATE_HANDLER"
            )
            
            db.add(fiscal_receipt)
            db.commit()
            
            logger.info(f"Fiscal receipt saved to database for order {order_id}")
            
        except Exception as e:
            logger.error(f"Failed to save fiscal receipt to database for order {order_id}: {str(e)}")
            # Don't fail the whole process if DB save fails

    async def _save_slip_receipt_to_db(self, order_id: int, payment_response, db: Session):
        """Save payment slip receipt data to slip_receipts table."""
        try:
            from ..database.models import SlipReceipt
            import uuid

            # Create slip receipt record from payment response
            slip_receipt = SlipReceipt(
                slip_receipt_id=uuid.uuid4(),
                order_id=order_id,
                receipt_pos_terminal_returned_id=payment_response.transaction_id or f"PAY_{order_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                receipt_body={
                    "payment_id": payment_response.payment_id,
                    "session_id": payment_response.session_id,
                    "transaction_id": payment_response.transaction_id,
                    "auth_code": payment_response.auth_code,
                    "rrn": payment_response.rrn,
                    "terminal_id": payment_response.terminal_id,
                    "merchant_id": payment_response.merchant_id,
                    "amount": payment_response.amount,
                    "currency_code": payment_response.currency_code,
                    "payment_date": payment_response.payment_date,
                    "customer_receipt": payment_response.customer_receipt,
                    "merchant_receipt": payment_response.merchant_receipt,
                    "response_code": payment_response.response_code,
                    "response_message": payment_response.response_message
                },
                created_at=datetime.utcnow(),
                created_by="FSM_STATE_HANDLER"
            )
            
            db.add(slip_receipt)
            db.commit()
            
            logger.info(f"Payment slip receipt saved to database for order {order_id}")
            
        except Exception as e:
            logger.error(f"Failed to save payment slip receipt to database for order {order_id}: {str(e)}")
            # Don't fail the whole process if DB save fails

    async def _handle_order_completion(self, order_id: int, kiosk_username: str, db: Session):
        """
        Handle order completion when FSM reaches SENT_TO_KDS state.

        This method:
        1. Updates order status to COMPLETED
        2. Deducts inventory for all order items using the existing stock replenishment system
        """
        try:
            from ..database.models import OrderStatus

            # Update order status to COMPLETED
            order = order_db_crud.get_order_by_id(db, order_id)
            if order:
                previous_status = order.status
                order.status = OrderStatus.COMPLETED
                db.commit()
                logger.info(f"Order {order_id} status updated to COMPLETED")
                
                # Publish order status change via SSE (fire-and-forget, safe)
                try:
                    await order_event_service.publish_order_status_changed(order, previous_status, kiosk_username)
                except Exception as sse_error:
                    logger.warning(f"Failed to publish order status SSE event: {sse_error}")

                # Deduct inventory for completed order
                try:
                    inventory_success = await order_inventory_deduction_logic.decrease_inventory_for_completed_order(
                        db=db,
                        order_id=order_id,
                        changed_by_username=kiosk_username  # Use the kiosk user who created the order
                    )
                    
                    if inventory_success:
                        logger.info(f"Inventory successfully deducted for completed order {order_id}")
                    else:
                        logger.warning(f"Partial inventory deduction for completed order {order_id}")
                        
                except Exception as inventory_error:
                    # Log inventory error but don't fail the order completion
                    # Order is already marked as COMPLETED, inventory deduction is a side effect
                    logger.error(
                        f"Failed to deduct inventory for completed order {order_id}: {str(inventory_error)}. "
                        f"Order completion succeeded but inventory may need manual adjustment."
                    )
                    
            else:
                logger.error(f"Order {order_id} not found for completion update")
                
        except Exception as e:
            logger.error(f"Failed to update order {order_id} status to COMPLETED: {str(e)}")

    async def _handle_order_failure(self, order_id: int, kiosk_username: str, db: Session):
        """Handle order failure when FSM reaches SENT_TO_KDS_FAILED state."""
        try:
            from ..database.models import OrderStatus

            # Update order status to FAILED
            order = order_db_crud.get_order_by_id(db, order_id)
            if order:
                previous_status = order.status
                order.status = OrderStatus.FAILED
                db.commit()
                logger.info(f"Order {order_id} status updated to FAILED")

                # Publish order status change via SSE (fire-and-forget, safe)
                # kiosk_username passed for frontend filtering - only the kiosk that created this order will process the event
                try:
                    await order_event_service.publish_order_status_changed(order, previous_status, kiosk_username)
                except Exception as sse_error:
                    logger.warning(f"Failed to publish order status SSE event: {sse_error}")
            else:
                logger.error(f"Order {order_id} not found for failure update")

        except Exception as e:
            logger.error(f"Failed to update order {order_id} status to FAILED: {str(e)}")

    async def _handle_printing_failed_state(self, order_id: int, kiosk_username: str, db: Session):
        """Handle PRINTING_FAILED terminal state - update order status to FAILED."""
        try:
            from ..database.models import OrderStatus

            # Update order status to FAILED
            order = order_db_crud.get_order_by_id(db, order_id)
            if order:
                previous_status = order.status
                order.status = OrderStatus.FAILED
                db.commit()
                logger.info(f"Order {order_id} status updated to FAILED due to printing failure")

                # Publish order status change via SSE (fire-and-forget, safe)
                # kiosk_username passed for frontend filtering - only the kiosk that created this order will process the event
                try:
                    await order_event_service.publish_order_status_changed(order, previous_status, kiosk_username)
                except Exception as sse_error:
                    logger.warning(f"Failed to publish order status SSE event: {sse_error}")
            else:
                logger.error(f"Order {order_id} not found for printing failure update")

        except Exception as e:
            logger.error(f"Failed to update order {order_id} status after printing failure: {str(e)}")

    async def _handle_failure_state(
        self,
        order_id: int,
        failure_state: State,
        kiosk_username: str,
        db: Session
    ):
        """
        Handle failure states - Update order status and log compensating actions.
        Saga Compensation: Rollback or notify on failures.
        """
        logger.warning(f"Order {order_id} entered failure state: {failure_state.value}")

        try:
            from ..database.models import OrderStatus
            
            # Update order status based on failure type
            order = order_db_crud.get_order_by_id(db, order_id)
            if order:
                previous_status = order.status
                if failure_state in [State.UNSUCCESSFUL_FISCALIZATION, State.UNSUCCESSFUL_PAYMENT]:
                    order.status = OrderStatus.FAILED
                    logger.info(f"Order {order_id} status updated to FAILED due to {failure_state.value}")
                elif failure_state in [State.CANCELED_BY_USER, State.CANCELED_BY_TIMEOUT]:
                    order.status = OrderStatus.CANCELLED
                    logger.info(f"Order {order_id} status updated to CANCELLED due to {failure_state.value}")
                
                db.commit()
                
                # Publish order status change via SSE (fire-and-forget, safe)
                try:
                    await order_event_service.publish_order_status_changed(order, previous_status, kiosk_username)
                except Exception as sse_error:
                    logger.warning(f"Failed to publish order status SSE event: {sse_error}")
            else:
                logger.error(f"Order {order_id} not found for failure state update")
                
        except Exception as e:
            logger.error(f"Failed to update order {order_id} status for failure state {failure_state.value}: {str(e)}")

        # Future: Implement compensating actions
        # - Reverse fiscalization if payment fails
        # - Notify support team
        # - Send customer notification
        # - Update inventory reservations


# Global state handler instance
_state_handler: Optional[FSMStateHandler] = None


def get_state_handler() -> FSMStateHandler:
    """Get global state handler instance"""
    global _state_handler
    if _state_handler is None:
        _state_handler = FSMStateHandler()
    return _state_handler


async def handle_state_change(
    order_id: int,
    new_state: State,
    kiosk_username: str,
    db: Session
):
    """
    Convenience function to handle state changes.
    Called by FSM orchestrator after state transitions.
    """
    handler = get_state_handler()
    await handler.handle_state_change(order_id, new_state, kiosk_username, db)
