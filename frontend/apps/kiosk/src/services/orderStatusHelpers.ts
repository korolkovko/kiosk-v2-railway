// File: src/services/orderStatusHelpers.ts
//
// Purpose:
// Simplified order status helpers that work directly with OrderContext.
// Uses only exact backend FSM states and events - no additional statuses.
// OrderContext is single source of truth for order tracking.

import type { Order } from '../models/domain/order'
import { OrderStatus, FSMState } from '../models/domain/order'

/**
 * Order Status Helpers
 * 
 * Simplified helpers that work directly with OrderContext.
 * Uses only exact backend FSM states and events.
 */
export const OrderStatusHelpers = {
  /**
   * Check if order has failed (any terminal failure state)
   */
  isOrderFailed: (order: Order): boolean => {
    return order.status === OrderStatus.FAILED ||
           order.status === OrderStatus.CANCELLED ||
           order.fsm_state === FSMState.CANCELED_BY_USER ||
           order.fsm_state === FSMState.CANCELED_BY_TIMEOUT ||
           order.fsm_state === FSMState.UNSUCCESSFUL_PAYMENT ||
           order.fsm_state === FSMState.PRINTING_FAILED ||
           order.fsm_state === FSMState.SENT_TO_KDS_FAILED ||
           order.fsm_state === FSMState.UNSUCCESSFUL_FISCALIZATION
  },

  /**
   * Check if order is completed successfully (sent to kitchen)
   */
  isOrderCompleted: (order: Order): boolean => {
    return order.status === OrderStatus.COMPLETED &&
           order.fsm_state === FSMState.SENT_TO_KDS
  },

  /**
   * Get order progress percentage based on exact backend FSM states
   */
  getOrderProgress: (order: Order): number => {
    const progressMap: Record<FSMState, number> = {
      [FSMState.INIT]: 10,
      [FSMState.AWAITING_PAYMENT]: 25,
      [FSMState.AWAITING_PRINTING]: 50,
      [FSMState.AWAITING_KDS]: 75,
      [FSMState.SENT_TO_KDS]: 100,
      
      // Terminal failure states
      [FSMState.CANCELED_BY_USER]: 0,
      [FSMState.CANCELED_BY_TIMEOUT]: 0,
      [FSMState.UNSUCCESSFUL_PAYMENT]: 0,
      [FSMState.PRINTING_FAILED]: 0,
      [FSMState.SENT_TO_KDS_FAILED]: 0,
      [FSMState.UNSUCCESSFUL_FISCALIZATION]: 0
    }
    
    return progressMap[order.fsm_state] || 0
  },

  /**
   * Get human-readable status text based on exact backend states
   */
  getStatusText: (order: Order): string => {
    switch (order.fsm_state) {
      case FSMState.INIT:
        return 'Initializing order...'
      case FSMState.AWAITING_PAYMENT:
        return 'Processing payment...'
      case FSMState.AWAITING_PRINTING:
        return 'Printing receipt...'
      case FSMState.AWAITING_KDS:
        return 'Sending to kitchen...'
      case FSMState.SENT_TO_KDS:
        return 'Order sent to kitchen'
      case FSMState.CANCELED_BY_USER:
        return 'Cancelled by user'
      case FSMState.CANCELED_BY_TIMEOUT:
        return 'Cancelled due to timeout'
      case FSMState.UNSUCCESSFUL_PAYMENT:
        return 'Payment failed'
      case FSMState.PRINTING_FAILED:
        return 'Printing failed'
      case FSMState.SENT_TO_KDS_FAILED:
        return 'Kitchen notification failed'
      case FSMState.UNSUCCESSFUL_FISCALIZATION:
        return 'Fiscalization failed'
      default:
        return 'Processing...'
    }
  },

  /**
   * Check if order should be cleaned up (terminal states)
   */
  shouldCleanupOrder: (order: Order): boolean => {
    return [
      OrderStatus.COMPLETED,
      OrderStatus.FAILED,
      OrderStatus.CANCELLED
    ].includes(order.status) ||
    [
      FSMState.SENT_TO_KDS,
      FSMState.CANCELED_BY_USER,
      FSMState.CANCELED_BY_TIMEOUT,
      FSMState.UNSUCCESSFUL_PAYMENT,
      FSMState.PRINTING_FAILED,
      FSMState.SENT_TO_KDS_FAILED,
      FSMState.UNSUCCESSFUL_FISCALIZATION
    ].includes(order.fsm_state)
  }
}