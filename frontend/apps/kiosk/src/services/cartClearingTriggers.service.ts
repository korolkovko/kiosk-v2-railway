// File: src/services/cartClearingTriggers.service.ts
//
// Purpose:
// Minimal foundation service for cart clearing triggers.
// Provides structure for future implementation of idle timeout, order completion triggers.
// Clean interface for automated cart management and customer session handling.

import type { Cart } from '../models/domain/cart'
import type { Order } from '../models/domain/order'
import { OrderStatus, FSMState } from '../models/domain/order'

/**
 * Cart clearing trigger types
 */
export enum CartClearingTrigger {
  MANUAL_CLEAR = 'MANUAL_CLEAR',
  ORDER_COMPLETED = 'ORDER_COMPLETED',
  IDLE_TIMEOUT = 'IDLE_TIMEOUT',
  SESSION_ENDED = 'SESSION_ENDED',
  KIOSK_RESET = 'KIOSK_RESET',
  ERROR_RECOVERY = 'ERROR_RECOVERY',
  ADMIN_OVERRIDE = 'ADMIN_OVERRIDE'
}

/**
 * Cart clearing configuration
 */
export interface CartClearingConfig {
  enable_auto_clear_on_order_completion: boolean
  order_completion_clear_delay_seconds: number
  enable_idle_timeout_clear: boolean
  idle_timeout_seconds: number
  enable_session_end_clear: boolean
  enable_error_recovery_clear: boolean
  clear_confirmation_required: boolean
}

/**
 * Default cart clearing configuration
 */
export const DEFAULT_CART_CLEARING_CONFIG: CartClearingConfig = {
  enable_auto_clear_on_order_completion: false, // Disabled - cart is cleared immediately during order processing cleanup, 30s delayed timer was causing cart to be cleared for next customer
  order_completion_clear_delay_seconds: 30, // 30 seconds after order completion (not used when disabled)
  enable_idle_timeout_clear: false, // Disabled for now
  idle_timeout_seconds: 300, // 5 minutes
  enable_session_end_clear: true,
  enable_error_recovery_clear: true,
  clear_confirmation_required: false // No confirmation needed for kiosk
}

/**
 * Cart clearing event data
 */
export interface CartClearingEvent {
  trigger: CartClearingTrigger
  cart_before_clear: Cart | null
  order_context?: Order
  timestamp: Date
  reason: string
  metadata?: Record<string, any>
}

/**
 * Cart clearing event handler type
 */
export type CartClearingEventHandler = (event: CartClearingEvent) => void

/**
 * Cart Clearing Triggers Service
 * 
 * MINIMAL FOUNDATION IMPLEMENTATION
 * This service provides the structure for future cart clearing automation:
 * - Order completion triggers
 * - Idle timeout detection
 * - Session management integration
 * - Error recovery clearing
 * 
 * Currently implements basic event tracking and configuration.
 * Full automation will be added when needed.
 */
export class CartClearingTriggersService {
  private config: CartClearingConfig
  private eventHandlers: Set<CartClearingEventHandler>
  private activeTimers: Map<string, number>
  // NOTE: Activity tracking for future use. Current idle detection handled by useInactivityDetection hook
  private lastActivity: Date

  constructor(config: Partial<CartClearingConfig> = {}) {
    this.config = { ...DEFAULT_CART_CLEARING_CONFIG, ...config }
    this.eventHandlers = new Set()
    this.activeTimers = new Map()
    this.lastActivity = new Date()
  }

  /**
   * Register event handler for cart clearing events
   */
  onCartClearingEvent(handler: CartClearingEventHandler): () => void {
    this.eventHandlers.add(handler)
    
    // Return unsubscribe function
    return () => {
      this.eventHandlers.delete(handler)
    }
  }

  /**
   * Emit cart clearing event to all registered handlers
   */
  private emitClearingEvent(
    trigger: CartClearingTrigger,
    cart: Cart | null,
    reason: string,
    order?: Order,
    metadata: Record<string, any> = {}
  ): void {
    const event: CartClearingEvent = {
      trigger,
      cart_before_clear: cart,
      order_context: order,
      timestamp: new Date(),
      reason,
      metadata
    }

    console.log(`🧹 Cart Clearing Event: ${trigger}`, { reason, metadata })
    
    // Notify all handlers
    this.eventHandlers.forEach(handler => {
      try {
        handler(event)
      } catch (error) {
        console.error('Cart clearing event handler error:', error)
      }
    })
  }

  /**
   * Record user activity (resets idle timer)
   */
  recordActivity(): void {
    this.lastActivity = new Date()

    // NOTE: Idle timer management handled by useInactivityDetection hook
    // This method kept for compatibility with existing callers
  }

  /**
   * Handle order completion trigger
   */
  onOrderCompleted(_order: Order, _cart: Cart | null): void {
    // Auto-clear disabled - cart cleanup handled by orderProcessingCleanup.service.ts
    // which immediately clears cart during order completion flow
    console.log('📝 Order completed but auto-clear disabled (cleanup handled by orderProcessingCleanup.service.ts)')

    // NOTE: If delayed cart clearing after order completion is needed in future:
    // 1. Set enable_auto_clear_on_order_completion = true in config
    // 2. Implement timer scheduling logic here
    // 3. Ensure coordination with orderProcessingCleanup.service.ts to avoid double-clearing
  }

  /**
   * Handle idle timeout trigger
   */
  onIdleTimeout(cart: Cart | null): void {
    if (!this.config.enable_idle_timeout_clear) {
      return
    }

    this.emitClearingEvent(
      CartClearingTrigger.IDLE_TIMEOUT,
      cart,
      `Kiosk idle for ${this.config.idle_timeout_seconds} seconds`,
      undefined,
      { idle_seconds: this.config.idle_timeout_seconds }
    )
  }

  /**
   * Handle session end trigger
   */
  onSessionEnded(cart: Cart | null): void {
    if (!this.config.enable_session_end_clear) {
      return
    }

    this.clearAllTimers()
    this.emitClearingEvent(
      CartClearingTrigger.SESSION_ENDED,
      cart,
      'User session ended'
    )
  }

  /**
   * Handle manual clear trigger
   */
  onManualClear(cart: Cart | null, reason: string = 'User requested'): void {
    this.clearAllTimers()
    this.emitClearingEvent(
      CartClearingTrigger.MANUAL_CLEAR,
      cart,
      reason
    )
  }

  /**
   * Handle error recovery clear trigger
   */
  onErrorRecovery(cart: Cart | null, error: string): void {
    if (!this.config.enable_error_recovery_clear) {
      return
    }

    this.clearAllTimers()
    this.emitClearingEvent(
      CartClearingTrigger.ERROR_RECOVERY,
      cart,
      `Error recovery: ${error}`,
      undefined,
      { error_message: error }
    )
  }

  /**
   * Handle kiosk reset trigger
   */
  onKioskReset(cart: Cart | null): void {
    this.clearAllTimers()
    this.emitClearingEvent(
      CartClearingTrigger.KIOSK_RESET,
      cart,
      'Kiosk system reset'
    )
  }

  /**
   * Handle admin override trigger
   */
  onAdminOverride(cart: Cart | null, adminReason: string): void {
    this.clearAllTimers()
    this.emitClearingEvent(
      CartClearingTrigger.ADMIN_OVERRIDE,
      cart,
      `Admin override: ${adminReason}`,
      undefined,
      { admin_action: true }
    )
  }


  /**
   * Clear all active timers
   */
  private clearAllTimers(): void {
    this.activeTimers.forEach((timerId, timerName) => {
      window.clearTimeout(timerId)
      console.log(`⏰ Cleared timer: ${timerName}`)
    })
    this.activeTimers.clear()
  }

  /**
   * Cancel specific clearing trigger
   */
  cancelClearingTrigger(triggerType: string): void {
    const timerId = this.activeTimers.get(triggerType)
    if (timerId) {
      window.clearTimeout(timerId)
      this.activeTimers.delete(triggerType)
      console.log(`❌ Cancelled clearing trigger: ${triggerType}`)
    }
  }

  /**
   * Get time since last activity in seconds
   */
  getTimeSinceLastActivity(): number {
    return Math.floor((new Date().getTime() - this.lastActivity.getTime()) / 1000)
  }

  /**
   * Check if cart should be cleared based on current conditions
   */
  shouldClearCart(_cart: Cart | null, order?: Order): {
    should_clear: boolean
    trigger: CartClearingTrigger | null
    reason: string
  } {
    // Check order completion
    if (order && this.isOrderReadyForCartClear(order)) {
      return {
        should_clear: this.config.enable_auto_clear_on_order_completion,
        trigger: CartClearingTrigger.ORDER_COMPLETED,
        reason: `Order ${order.order_id} is completed and ready for pickup`
      }
    }

    // Check idle timeout
    if (this.config.enable_idle_timeout_clear) {
      const idleSeconds = this.getTimeSinceLastActivity()
      if (idleSeconds >= this.config.idle_timeout_seconds) {
        return {
          should_clear: true,
          trigger: CartClearingTrigger.IDLE_TIMEOUT,
          reason: `Kiosk idle for ${idleSeconds} seconds`
        }
      }
    }

    return {
      should_clear: false,
      trigger: null,
      reason: 'No clearing conditions met'
    }
  }

  /**
   * Check if order is ready for cart clearing
   */
  private isOrderReadyForCartClear(order: Order): boolean {
    return order.status === OrderStatus.COMPLETED ||
           order.fsm_state === FSMState.SENT_TO_KDS
  }

  /**
   * Get clearing configuration
   */
  getConfig(): CartClearingConfig {
    return { ...this.config }
  }

  /**
   * Update clearing configuration
   */
  updateConfig(newConfig: Partial<CartClearingConfig>): void {
    this.config = { ...this.config, ...newConfig }
    console.log('⚙️ Cart clearing config updated:', this.config)
  }

  /**
   * Get active timers info
   */
  getActiveTimers(): { name: string; timer_id: number }[] {
    return Array.from(this.activeTimers.entries()).map(([name, timer_id]) => ({
      name,
      timer_id
    }))
  }

  /**
   * Reset service state
   */
  reset(): void {
    this.clearAllTimers()
    this.lastActivity = new Date()
    console.log('🔄 Cart clearing triggers service reset')
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.clearAllTimers()
    this.eventHandlers.clear()
    console.log('🧹 Cart clearing triggers service destroyed')
  }
}

/**
 * Global cart clearing triggers service instance
 */
export const cartClearingTriggersService = new CartClearingTriggersService()

/**
 * Convenience functions for common clearing operations
 */
export const CartClearingHelpers = {
  /**
   * Record user activity
   */
  recordActivity: () => {
    cartClearingTriggersService.recordActivity()
  },

  /**
   * Trigger manual cart clear
   */
  triggerManualClear: (cart: Cart | null, reason?: string) => {
    cartClearingTriggersService.onManualClear(cart, reason)
  },

  /**
   * Handle order completion
   */
  handleOrderCompletion: (order: Order, cart: Cart | null) => {
    cartClearingTriggersService.onOrderCompleted(order, cart)
  },

  /**
   * Handle session end
   */
  handleSessionEnd: (cart: Cart | null) => {
    cartClearingTriggersService.onSessionEnded(cart)
  },

  /**
   * Check if cart should be cleared
   */
  checkClearingConditions: (cart: Cart | null, order?: Order) => {
    return cartClearingTriggersService.shouldClearCart(cart, order)
  },

  /**
   * Cancel pending clear operations
   */
  cancelPendingClear: (triggerType: string) => {
    cartClearingTriggersService.cancelClearingTrigger(triggerType)
  }
}