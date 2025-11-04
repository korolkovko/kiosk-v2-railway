# OrderInventoryDeductionLogic.py
# Business logic for deducting inventory when orders are completed and sent to KDS successfully
# This utility wrapper uses the existing stock replenishment system with negative quantities

from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from ..models.ItemLiveStockReplenishmentPydanticModel import ItemLiveStockReplenishmentRequest
from ..logic.ItemLiveStockReplenishmentLogic import item_live_stock_replenishment_logic
from ..services.OrderItemDBCRUD import order_item_db_crud
from ..services.OrderDBCRUD import order_db_crud


class OrderInventoryDeductionLogic:
    """
    Business logic for deducting inventory when orders are completed.
    
    This class provides a dedicated wrapper around the existing stock replenishment
    system to handle inventory deduction for completed orders. It processes each
    order item and reduces the available stock quantity using negative replenishment.
    """

    async def decrease_inventory_for_completed_order(
        self,
        db: Session,
        order_id: int,
        changed_by_username: Optional[str] = None
    ) -> bool:
        """
        Decrease inventory for all items in a completed order.
        
        This method processes each item in the order and reduces the stock quantity
        by calling the existing replenishment system with negative quantities.
        Each deduction creates a new record in items_live_stock_replenishment table.
        
        Args:
            db: Database session
            order_id: ID of the completed order
            changed_by_username: Username for audit trail (e.g., 'admin_user', 'KIOSK_AUTO', 'SYSTEM')
            
        Returns:
            bool: True if all inventory deductions succeeded, False otherwise
            
        Raises:
            Exception: If order not found or critical errors occur
        """
        try:
            logger.info(f"Starting inventory deduction for completed order {order_id}")
            
            # Validate order exists
            order = order_db_crud.get_order_by_id(db, order_id)
            if not order:
                logger.error(f"Order {order_id} not found for inventory deduction")
                raise Exception(f"Order {order_id} not found")
            
            # Get all order items
            order_items = order_item_db_crud.get_order_items_by_order_id(db, order_id)
            if not order_items:
                logger.warning(f"No items found for order {order_id} - nothing to deduct")
                return True
            
            # Determine changed_by username
            effective_changed_by_username = self._determine_changed_by_username(
                order, changed_by_username
            )
            
            # Process each order item
            successful_deductions = 0
            total_items = len(order_items)
            
            for order_item in order_items:
                try:
                    # Create deduction request with negative quantity
                    deduction_request = ItemLiveStockReplenishmentRequest(
                        item_id=order_item.item_id,
                        quantity=-order_item.quantity  # Negative for deduction
                    )
                    
                    # Call existing replenishment logic with negative quantity
                    result = await item_live_stock_replenishment_logic.replenish_or_remove(
                        db=db,
                        request=deduction_request,
                        changed_by_username=effective_changed_by_username
                    )
                    
                    logger.info(
                        f"Successfully deducted {order_item.quantity} units of item {order_item.item_id} "
                        f"for order {order_id}. New stock: {result.stock_quantity}"
                    )
                    successful_deductions += 1
                    
                except Exception as item_error:
                    logger.error(
                        f"Failed to deduct inventory for item {order_item.item_id} "
                        f"in order {order_id}: {str(item_error)}"
                    )
                    # Continue processing other items even if one fails
                    continue
            
            # Log summary
            if successful_deductions == total_items:
                logger.info(
                    f"Inventory deduction completed successfully for order {order_id}: "
                    f"{successful_deductions}/{total_items} items processed"
                )
                return True
            else:
                logger.warning(
                    f"Partial inventory deduction for order {order_id}: "
                    f"{successful_deductions}/{total_items} items processed successfully"
                )
                return False
                
        except Exception as e:
            logger.error(f"Critical error during inventory deduction for order {order_id}: {str(e)}")
            raise
    
    def _determine_changed_by_username(
        self,
        order,
        provided_username: Optional[str]
    ) -> str:
        """
        Determine the appropriate username for the changed_by field.
        
        Priority:
        1. Provided username (if given)
        2. KIOSK_AUTO_DEDUCTION (for kiosk-initiated order completions)
        3. SYSTEM (fallback for automated processes)
        
        Args:
            order: Order object
            provided_username: Username provided by caller
            
        Returns:
            str: Username to use for changed_by field
        """
        if provided_username is not None:
            return provided_username
        
        # Determine appropriate automated username based on order context
        if hasattr(order, 'kiosk_id') and order.kiosk_id:
            username = "KIOSK_AUTO_DEDUCTION"
            logger.info(
                f"Using kiosk automated username '{username}' for inventory deduction "
                f"of order {order.order_id} from kiosk {order.kiosk_id}"
            )
        else:
            username = "SYSTEM"
            logger.info(
                f"Using system username '{username}' for inventory deduction "
                f"of order {order.order_id}"
            )
        
        return username


# Global logic instance
order_inventory_deduction_logic = OrderInventoryDeductionLogic()