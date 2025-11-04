// orderProcessingLifecycle.service.ts
// Service for managing complete order processing lifecycle
// Handles SSE events, status updates, cleanup, and navigation
// Uses OrderContext directly - no separate order status service needed

import { CartClearingHelpers } from './cartClearingTriggers.service';
import { orderProcessingCleanupService } from './orderProcessingCleanup.service';
import { OrderStatus, type Order } from '../models/domain/order';
import type { CartItem } from '../models/domain/cart';
import type { OrderUpdateData } from '../SSESubscription/useSSEOrderUpdates';
import type { NavigationMode } from '../stores/navigationStore';

export interface OrderProcessingCallbacks {
  clearCart: () => void;
  clearCurrentOrder: () => void;
  setActiveCategory: (category: string) => void;
  setNavigationMode: (mode: NavigationMode) => void;
  showScreenSaver: () => void;
  navigateBackFromOrderProcessing: () => void;
  navigateToOrderProcessing: () => void;
}

export interface OrderProcessingState {
  processingOrderId: number | null;
  processingOrderPickupNumber: string | null;
  processingOrderPinCode: string | null;
}

export class OrderProcessingLifecycleService {
  
  /**
   * Start order processing workflow
   * Called when "9" button is pressed
   */
  static async startOrderProcessing(
    cartItems: CartItem[],
    cartVM: any,
    orderPlacementService: any,
    callbacks: OrderProcessingCallbacks,
    setState: {
      setProcessingOrderId: (id: number | null) => void;
      setProcessingOrderPickupNumber: (number: string | null) => void;
      setProcessingOrderPinCode: (code: string | null) => void;
      setIsPlacingOrder: (loading: boolean) => void;
      setOrderInProgress: (inProgress: boolean) => void;
      updateOrderStatus: (orderId: string, order: any) => void;
    }
  ): Promise<void> {
    
    if (cartItems.length === 0) {
      console.warn('🛒 Cannot start order processing: cart is empty');
      return;
    }

    setState.setIsPlacingOrder(true);
    setState.setOrderInProgress(true);

    try {
      console.log('📤 OrderProcessingLifecycle: Starting order processing with', cartItems.length, 'items');

      // Validate cart VM
      if (!cartVM || !cartVM.items || cartVM.items.length === 0) {
        throw new Error('Cart view model not available or empty');
      }

      // Place order
      const order = await orderPlacementService.placeOrder(cartVM.items);
      console.log('✅ OrderProcessingLifecycle: Order placed successfully:', order);

      // Store processing order details
      setState.setProcessingOrderId(order.order_id);
      setState.setProcessingOrderPickupNumber(order.pickup_number);
      setState.setProcessingOrderPinCode(order.pin_code);

      // Update order context FIRST before switching navigation
      setState.updateOrderStatus(order.order_id.toString(), order);
      console.log('📝 OrderProcessingLifecycle: Order set in OrderContext for tracking:', order.order_id);

      // Switch to order processing mode AFTER order is set in context
      callbacks.navigateToOrderProcessing();

    } catch (error: any) {
      console.error('❌ OrderProcessingLifecycle: Order placement failed:', error);

      // Return to previous navigation mode on error
      callbacks.navigateBackFromOrderProcessing();

      // Show error to user
      alert(`Order placement failed: ${error.message}`);
    } finally {
      setState.setIsPlacingOrder(false);
      setState.setOrderInProgress(false);
    }
  }

  /**
   * Handle order processing completion
   * Called when countdown finishes after successful completion
   */
  static handleOrderProcessingCompletion(
    currentOrder: Order | null,
    cartItems: CartItem[],
    callbacks: OrderProcessingCallbacks,
    promotedCategoryName: string,
    setState: {
      setProcessingOrderId: (id: number | null) => void;
      setProcessingOrderPickupNumber: (number: string | null) => void;
      setProcessingOrderPinCode: (code: string | null) => void;
    }
  ): void {
    console.log('📦 OrderProcessingLifecycle: Handling order completion');

    // Use centralized cleanup service
    orderProcessingCleanupService.performCompleteCleanup(
      currentOrder,
      cartItems,
      callbacks,
      promotedCategoryName
    );
    
    // Clear processing state
    setState.setProcessingOrderId(null);
    setState.setProcessingOrderPickupNumber(null);
    setState.setProcessingOrderPinCode(null);
  }

  /**
   * Handle order processing error
   * Called when any processing step fails
   */
  static handleOrderProcessingError(
    error: string,
    currentOrder: Order | null,
    callbacks: OrderProcessingCallbacks,
    promotedCategoryName: string,
    setState: {
      setProcessingOrderId: (id: number | null) => void;
      setProcessingOrderPickupNumber: (number: string | null) => void;
      setProcessingOrderPinCode: (code: string | null) => void;
    }
  ): void {
    console.error('❌ OrderProcessingLifecycle: Processing error:', error);

    // Use centralized error cleanup after delay to show error message
    setTimeout(() => {
      orderProcessingCleanupService.performErrorCleanup(
        currentOrder,
        {
          clearCart: callbacks.clearCart,
          clearCurrentOrder: callbacks.clearCurrentOrder,
          setActiveCategory: callbacks.setActiveCategory,
          setNavigationMode: callbacks.setNavigationMode,
          navigateBackFromOrderProcessing: callbacks.navigateBackFromOrderProcessing,
          showScreenSaver: callbacks.showScreenSaver
        },
        promotedCategoryName
      );

      // Clear processing state
      setState.setProcessingOrderId(null);
      setState.setProcessingOrderPickupNumber(null);
      setState.setProcessingOrderPinCode(null);
    }, 4000); // 4 seconds to show error message
  }

  /**
   * Handle order processing timeout
   * Called when processing takes longer than expected
   */
  static handleOrderProcessingTimeout(
    currentOrder: Order | null,
    cartItems: CartItem[],
    callbacks: OrderProcessingCallbacks,
    promotedCategoryName: string,
    setState: {
      setProcessingOrderId: (id: number | null) => void;
      setProcessingOrderPickupNumber: (number: string | null) => void;
      setProcessingOrderPinCode: (code: string | null) => void;
    }
  ): void {
    console.warn('⏰ OrderProcessingLifecycle: Processing timeout');

    // Use centralized timeout cleanup
    orderProcessingCleanupService.performTimeoutCleanup(
      currentOrder,
      cartItems,
      callbacks,
      promotedCategoryName
    );
    
    // Clear processing state
    setState.setProcessingOrderId(null);
    setState.setProcessingOrderPickupNumber(null);
    setState.setProcessingOrderPinCode(null);
  }

  /**
   * Handle SSE order updates during processing
   * Processes order status changes and determines if cleanup is needed
   */
  static handleOrderUpdateDuringProcessing(
    orderUpdate: OrderUpdateData,
    currentOrder: Order | null,
    updateOrderStatus: (orderId: string, updates: any) => void
  ): boolean {
    // Handle case where we have an existing order and the IDs match
    if (currentOrder && currentOrder.order_id === orderUpdate.order_id) {
      const updates: Partial<Order> = {
        status: orderUpdate.status,
        fsm_state: orderUpdate.fsm_state
      };

      // Append FSM event to history if present
      if (orderUpdate.fsm_event_to_add) {
        updates.fsm_event_history = [
          ...(currentOrder.fsm_event_history || []),
          orderUpdate.fsm_event_to_add
        ];
      }

      updateOrderStatus(orderUpdate.order_id.toString(), updates as any);

      // Return true if order reached terminal state (but don't cleanup immediately)
      return orderUpdate.status === OrderStatus.COMPLETED ||
             orderUpdate.status === OrderStatus.FAILED ||
             orderUpdate.status === OrderStatus.CANCELLED;
    }

    // Handle case where we don't have a current order but we're receiving updates
    // This can happen if the order was created but not yet set in context
    if (!currentOrder && orderUpdate.order_id) {
      const updates: Partial<Order> = {
        order_id: orderUpdate.order_id,
        status: orderUpdate.status,
        fsm_state: orderUpdate.fsm_state
      };

      // Add FSM event to history if present
      if (orderUpdate.fsm_event_to_add) {
        updates.fsm_event_history = [orderUpdate.fsm_event_to_add];
      }

      updateOrderStatus(orderUpdate.order_id.toString(), updates as any);

      // Return true if order reached terminal state
      return orderUpdate.status === OrderStatus.COMPLETED ||
             orderUpdate.status === OrderStatus.FAILED ||
             orderUpdate.status === OrderStatus.CANCELLED;
    }

    return false;
  }

  /**
   * Get processing timeout for current step
   * Based on server timeout configuration
   */
  static getProcessingTimeout(processingStep: string): number {
    const timeouts = {
      'fiscalization': 30000,  // 30 seconds
      'payment': 180000,       // 180 seconds (3 minutes)
      'printing': 60000,       // 60 seconds
      'transmission': 20000    // 20 seconds
    };

    return timeouts[processingStep as keyof typeof timeouts] || 30000;
  }
}

// Export singleton instance
export const orderProcessingLifecycleService = OrderProcessingLifecycleService;