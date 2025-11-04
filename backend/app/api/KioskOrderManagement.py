# KioskOrderManagement.py
# FastAPI endpoints for Kiosk Order Management with proper kiosk authentication
# Provides dedicated API routes for kiosk order operations

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database.connection import get_db
from ..database.models import User
from ..models.OrderPydanticModels import OrderCreateRequest, OrderCommandRequest, OrderCommandResponse
from ..logic.OrderLogic import order_logic
from ..auth.kiosk_dependencies import (
    get_current_kiosk_user,
    get_current_kiosk_username
)


router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Order Management"]
)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_request: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username)
):
    """
    Create new order for kiosk user
    
    This endpoint creates a new order with items, initializes FSM runtime,
    and hands off to FSM orchestrator for payment processing.
    Only authenticated kiosk users with proper role can create orders.
    
    Args:
        order_request: Order creation request with items
        db: Database session
        current_user: Current authenticated kiosk user (must have kiosk role)
        kiosk_username: Kiosk username for EventBus routing
        
    Returns:
        Dictionary with basic order info (order_id, status, pickup_number, pin_code)
        
    Raises:
        HTTPException: If validation fails or order creation fails
    """
    try:
        order_response = await order_logic.create_order(
            db=db,
            order_data=order_request,
            kiosk_username=kiosk_username,
            created_by_user_id=current_user.user_id
        )
        
        return {
            "success": True,
            "order": order_response,
            "message": "Order created successfully",
            "listen": "/api/kiosk/events"  # SSE endpoint for order updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(e)}"
        )


@router.get("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username)
):
    """
    Get order details by ID
    
    Returns basic order information for the specified order.
    Only authenticated kiosk users with proper role can access order details.
    
    Args:
        order_id: Order ID to retrieve
        db: Database session
        current_user: Current authenticated kiosk user (must have kiosk role)
        kiosk_username: Kiosk username for context
        
    Returns:
        Dictionary with basic order info
        
    Raises:
        HTTPException: If order not found or access denied
    """
    try:
        order_response = await order_logic.get_order_by_id(db, order_id)
        
        return {
            "success": True,
            "order": order_response,
            "message": "Order retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order retrieval failed: {str(e)}"
        )


@router.post("/orders/{order_id}/commands", response_model=OrderCommandResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_order_command(
    order_id: int,
    command_request: OrderCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username)
):
    """
    Process order command (retry payment, cancel, etc.)
    
    This endpoint processes user commands for existing orders and hands off
    to FSM orchestrator for state transition handling.
    Only authenticated kiosk users with proper role can send commands.
    
    Supported commands:
    - RETRY_PAYMENT: Retry failed payment
    - CHANGE_CARD: Change payment card
    - CANCEL_ORDER: Cancel the order
    - RETRY_FISCALIZATION: Retry fiscal processing
    - RETRY_PRINTING: Retry receipt printing
    - ACCEPT_ALTERNATIVE_RECEIPT: Accept QR code instead of printed receipt
    - DECLINE_ALTERNATIVE_RECEIPT: Decline alternative receipt option
    
    Args:
        order_id: Order ID to send command to
        command_request: Command details (action, operation_id, parameters)
        db: Database session
        current_user: Current authenticated kiosk user (must have kiosk role)
        kiosk_username: Kiosk username for EventBus routing
        
    Returns:
        OrderCommandResponse with command acknowledgment and state info
        
    Raises:
        HTTPException: If command validation fails or processing fails
    """
    try:
        command_response = await order_logic.process_order_command(
            db=db,
            order_id=order_id,
            command=command_request,
            kiosk_username=kiosk_username
        )
        
        return command_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command processing failed: {str(e)}"
        )


@router.get("/orders/status/{order_status}", status_code=status.HTTP_200_OK)
async def list_orders_by_status(
    order_status: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username)
):
    """
    List orders by status for current kiosk
    
    Returns orders filtered by status for monitoring purposes.
    Only authenticated kiosk users with proper role can list orders.
    
    Args:
        order_status: Order status to filter by (PENDING, COMPLETED, FAILED, CANCELLED)
        limit: Maximum number of orders to return (default: 50)
        offset: Number of orders to skip (default: 0)
        db: Database session
        current_user: Current authenticated kiosk user (must have kiosk role)
        kiosk_username: Kiosk username for context
        
    Returns:
        Dictionary with filtered list of orders and pagination info
    """
    try:
        from ..services.OrderDBCRUD import order_db_crud
        from ..database.models import OrderStatus
        
        # Validate status
        try:
            status_enum = OrderStatus(order_status.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order status: {order_status}"
            )
        
        orders = order_db_crud.get_orders_by_status(db, status_enum, limit, offset)
        total_count = order_db_crud.get_order_count_by_status(db, status_enum)
        
        order_list = []
        for order in orders:
            order_list.append({
                "order_id": order.order_id,
                "status": order.status.value,
                "pickup_number": order.pickup_number,
                "total_amount_gross_kopecks": order.total_amount_gross_kopecks,
                "order_time": order.order_time.isoformat()
            })
        
        return {
            "success": True,
            "orders": order_list,
            "total_count": total_count,
            "page": (offset // limit) + 1,
            "page_size": limit,
            "filter": {"status": order_status.upper()},
            "message": f"Orders with status {order_status.upper()} retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order listing failed: {str(e)}"
        )