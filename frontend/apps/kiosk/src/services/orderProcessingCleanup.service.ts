// orderProcessingCleanup.service.ts
// Centralized service for order processing cleanup operations
// Provides reusable cleanup methods for consistent behavior across components
// Uses OrderContext directly - no separate order status service needed

import { CartClearingHelpers } from './cartClearingTriggers.service';
import { OrderStatus, type Order } from '../models/domain/order';
import type { CartItem } from '../models/domain/cart';
import type { NavigationMode } from '../stores/navigationStore';

export interface OrderProcessingCleanupOptions {
  clearCart?: boolean;
  clearOrder?: boolean;
  unregisterOrderTracking?: boolean;
  resetNavigation?: boolean;
  showScreenSaver?: boolean;
}

export class OrderProcessingCleanupService {
  
  /**
   * Complete cleanup after order processing completion or error
   * Centralizes all cleanup logic in one reusable method
   * @param promotedCategoryName - Name of the promoted category from categories[0].name
   */
  static performCompleteCleanup(
    currentOrder: Order | null,
    cartItems: CartItem[],
    callbacks: {
      clearCart: () => void;
      clearCurrentOrder: () => void;
      setActiveCategory: (category: string) => void;
      setNavigationMode: (mode: NavigationMode) => void;
      showScreenSaver: () => void;
      navigateBackFromOrderProcessing?: () => void;
    },
    promotedCategoryName: string,
    options: OrderProcessingCleanupOptions = {}
  ) {
    const {
      clearCart = true,
      clearOrder = true,
      unregisterOrderTracking = true,
      resetNavigation = true,
      showScreenSaver = true
    } = options;

    console.log('🧹 OrderProcessingCleanup: Starting complete cleanup', {
      orderId: currentOrder?.order_id,
      clearCart,
      clearOrder,
      unregisterOrderTracking,
      resetNavigation,
      showScreenSaver
    });

    try {
      // Handle order completion with cart clearing service
      if (currentOrder && clearCart) {
        const orderForClearing = {
          ...currentOrder,
          status: currentOrder.status,
          updated_at: new Date()
        };

        const cartForClearing = {
          items: cartItems,
          created_at: new Date(),
          updated_at: new Date()
        };

        CartClearingHelpers.handleOrderCompletion(orderForClearing, cartForClearing);
      }

      // Order tracking cleanup is handled by OrderContext.clearCurrentOrder()
      if (currentOrder && unregisterOrderTracking) {
        console.log('📝 OrderProcessingCleanup: Order tracking cleanup handled by OrderContext for', currentOrder.order_id);
      }

      // Clear cart
      if (clearCart) {
        callbacks.clearCart();
        console.log('🛒 OrderProcessingCleanup: Cart cleared');
      }

      // Clear current order
      if (clearOrder) {
        callbacks.clearCurrentOrder();
        console.log('📦 OrderProcessingCleanup: Current order cleared');
      }

      // Exit order processing mode if active
      if (callbacks.navigateBackFromOrderProcessing) {
        callbacks.navigateBackFromOrderProcessing();
        console.log('🔙 OrderProcessingCleanup: Exited order processing mode');
      }

      // Reset navigation to initial state
      if (resetNavigation) {
        callbacks.setActiveCategory(promotedCategoryName);
        callbacks.setNavigationMode('categories');
        console.log('🔄 OrderProcessingCleanup: Navigation reset to initial state');
      }

      // Show screensaver
      if (showScreenSaver) {
        callbacks.showScreenSaver();
        console.log('🖥️ OrderProcessingCleanup: Screensaver shown');
      }

      console.log('✅ OrderProcessingCleanup: Complete cleanup finished successfully');

    } catch (error) {
      console.error('❌ OrderProcessingCleanup: Error during cleanup:', error);
      // Still try to show screensaver even if cleanup fails
      if (showScreenSaver) {
        callbacks.showScreenSaver();
      }
    }
  }

  /**
   * Quick cleanup for error scenarios
   * Minimal cleanup when order processing fails
   * @param promotedCategoryName - Name of the promoted category from categories[0].name
   */
  static performErrorCleanup(
    currentOrder: Order | null,
    callbacks: {
      clearCart: () => void;
      clearCurrentOrder: () => void;
      setActiveCategory: (category: string) => void;
      setNavigationMode: (mode: NavigationMode) => void;
      navigateBackFromOrderProcessing?: () => void;
      showScreenSaver: () => void;
    },
    promotedCategoryName: string
  ) {
    console.log('🚨 OrderProcessingCleanup: Performing error cleanup for order', currentOrder?.order_id);

    try {
      // Clear cart to remove failed order items
      callbacks.clearCart();
      console.log('🛒 OrderProcessingCleanup: Cart cleared after error');

      // Clear current order to allow new orders
      callbacks.clearCurrentOrder();
      console.log('📦 OrderProcessingCleanup: Current order cleared after error');

      // Exit order processing mode
      if (callbacks.navigateBackFromOrderProcessing) {
        callbacks.navigateBackFromOrderProcessing();
      }

      // Reset navigation to initial state
      callbacks.setActiveCategory(promotedCategoryName);
      callbacks.setNavigationMode('categories');
      console.log('🔄 OrderProcessingCleanup: Navigation reset to initial state');

      // Show screensaver immediately
      callbacks.showScreenSaver();

      console.log('✅ OrderProcessingCleanup: Error cleanup completed');

    } catch (error) {
      console.error('❌ OrderProcessingCleanup: Error during error cleanup:', error);
      // Force screensaver as last resort
      callbacks.showScreenSaver();
    }
  }

  /**
   * Cleanup for timeout scenarios
   * Handles cleanup when processing times out
   * @param promotedCategoryName - Name of the promoted category from categories[0].name
   */
  static performTimeoutCleanup(
    currentOrder: Order | null,
    cartItems: CartItem[],
    callbacks: {
      clearCart: () => void;
      clearCurrentOrder: () => void;
      setActiveCategory: (category: string) => void;
      setNavigationMode: (mode: NavigationMode) => void;
      showScreenSaver: () => void;
      navigateBackFromOrderProcessing?: () => void;
    },
    promotedCategoryName: string
  ) {
    console.log('⏰ OrderProcessingCleanup: Performing timeout cleanup for order', currentOrder?.order_id);

    // Use complete cleanup for timeout scenarios
    this.performCompleteCleanup(currentOrder, cartItems, callbacks, promotedCategoryName, {
      clearCart: true,
      clearOrder: true,
      unregisterOrderTracking: true,
      resetNavigation: true,
      showScreenSaver: true
    });
  }

  /**
   * Check if cleanup is needed based on order status
   */
  static shouldPerformCleanup(orderStatus: OrderStatus): boolean {
    return [
      OrderStatus.COMPLETED,
      OrderStatus.FAILED,
      OrderStatus.CANCELLED
    ].includes(orderStatus);
  }
}

// Export singleton instance
export const orderProcessingCleanupService = OrderProcessingCleanupService;