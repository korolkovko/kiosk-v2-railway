// File: src/services/cartLifecycleManagement.service.ts
//
// Purpose:
// Minimal foundation service for cart lifecycle management.
// Provides structure for future implementation of idle timeout, order completion triggers.
// Clean interface for cart clearing and session management.

import type { Cart } from '../models/domain/cart'

/**
 * Cart lifecycle events enum
 */
export enum CartLifecycleEvent {
  CART_CREATED = 'CART_CREATED',
  CART_UPDATED = 'CART_UPDATED',
  CART_CLEARED = 'CART_CLEARED',
  ORDER_PLACED = 'ORDER_PLACED',
  ORDER_COMPLETED = 'ORDER_COMPLETED',
  IDLE_TIMEOUT = 'IDLE_TIMEOUT',
  SESSION_ENDED = 'SESSION_ENDED'
}

/**
 * Cart lifecycle configuration
 */
export interface CartLifecycleConfig {
  idle_timeout_seconds: number
  auto_clear_after_order: boolean
  auto_clear_delay_seconds: number
  max_cart_age_seconds: number
  enable_idle_detection: boolean
}

/**
 * Default cart lifecycle configuration
 */
export const DEFAULT_CART_LIFECYCLE_CONFIG: CartLifecycleConfig = {
  idle_timeout_seconds: 300, // 5 minutes
  auto_clear_after_order: true,
  auto_clear_delay_seconds: 30, // 30 seconds after order completion
  max_cart_age_seconds: 1800, // 30 minutes
  enable_idle_detection: false // Disabled for now
}

/**
 * Cart lifecycle state
 */
export interface CartLifecycleState {
  last_activity_timestamp: Date
  idle_timer_id: number | null
  auto_clear_timer_id: number | null
  is_idle: boolean
  lifecycle_events: CartLifecycleEvent[]
}

/**
 * Cart lifecycle event handler type
 */
export type CartLifecycleEventHandler = (
  event: CartLifecycleEvent,
  cart: Cart | null,
  metadata?: Record<string, any>
) => void

/**
 * Cart Lifecycle Management Service
 * 
 * MINIMAL FOUNDATION IMPLEMENTATION
 * This service provides the structure for future cart lifecycle features:
 * - Idle timeout detection
 * - Auto-clear after order completion
 * - Session management
 * - Cart age tracking
 * 
 * Currently implements basic event tracking and configuration.
 * Full implementation will be added when needed.
 */
export class CartLifecycleManagementService {
  private config: CartLifecycleConfig
  private state: CartLifecycleState
  private eventHandlers: Set<CartLifecycleEventHandler>

  constructor(config: Partial<CartLifecycleConfig> = {}) {
    this.config = { ...DEFAULT_CART_LIFECYCLE_CONFIG, ...config }
    this.state = {
      last_activity_timestamp: new Date(),
      idle_timer_id: null,
      auto_clear_timer_id: null,
      is_idle: false,
      lifecycle_events: []
    }
    this.eventHandlers = new Set()
  }

  /**
   * Register event handler for cart lifecycle events
   */
  onLifecycleEvent(handler: CartLifecycleEventHandler): () => void {
    this.eventHandlers.add(handler)
    
    // Return unsubscribe function
    return () => {
      this.eventHandlers.delete(handler)
    }
  }

  /**
   * Emit lifecycle event to all registered handlers
   */
  private emitEvent(
    event: CartLifecycleEvent,
    cart: Cart | null = null,
    metadata: Record<string, any> = {}
  ): void {
    console.log(`🔄 Cart Lifecycle Event: ${event}`, { cart, metadata })
    
    // Track event in state
    this.state.lifecycle_events.push(event)
    
    // Keep only last 50 events to prevent memory bloat
    if (this.state.lifecycle_events.length > 50) {
      this.state.lifecycle_events = this.state.lifecycle_events.slice(-50)
    }
    
    // Notify all handlers
    this.eventHandlers.forEach(handler => {
      try {
        handler(event, cart, metadata)
      } catch (error) {
        console.error('Cart lifecycle event handler error:', error)
      }
    })
  }

  /**
   * Record cart activity (updates last activity timestamp)
   */
  recordActivity(): void {
    this.state.last_activity_timestamp = new Date()
    this.state.is_idle = false
    
    // TODO: Reset idle timer when implemented
    console.log('📝 Cart activity recorded')
  }

  /**
   * Handle cart creation
   */
  onCartCreated(cart: Cart): void {
    this.recordActivity()
    this.emitEvent(CartLifecycleEvent.CART_CREATED, cart)
  }

  /**
   * Handle cart update
   */
  onCartUpdated(cart: Cart): void {
    this.recordActivity()
    this.emitEvent(CartLifecycleEvent.CART_UPDATED, cart)
  }

  /**
   * Handle cart clearing
   */
  onCartCleared(reason: string = 'manual'): void {
    this.clearTimers()
    this.emitEvent(CartLifecycleEvent.CART_CLEARED, null, { reason })
  }

  /**
   * Handle order placement
   */
  onOrderPlaced(cart: Cart, orderNumber: string): void {
    this.emitEvent(CartLifecycleEvent.ORDER_PLACED, cart, { orderNumber })
    
    // TODO: Start auto-clear timer if enabled
    if (this.config.auto_clear_after_order) {
      console.log(`⏰ Auto-clear scheduled in ${this.config.auto_clear_delay_seconds} seconds`)
    }
  }

  /**
   * Handle order completion
   */
  onOrderCompleted(orderNumber: string): void {
    this.emitEvent(CartLifecycleEvent.ORDER_COMPLETED, null, { orderNumber })
    
    // TODO: Trigger cart clearing if auto-clear is enabled
    if (this.config.auto_clear_after_order) {
      console.log('🧹 Order completed - cart auto-clear triggered')
    }
  }

  /**
   * Handle idle timeout (foundation for future implementation)
   */
  onIdleTimeout(): void {
    this.state.is_idle = true
    this.emitEvent(CartLifecycleEvent.IDLE_TIMEOUT, null)
    
    // TODO: Implement idle timeout behavior
    console.log('😴 Cart idle timeout detected')
  }

  /**
   * Handle session end
   */
  onSessionEnded(): void {
    this.clearTimers()
    this.emitEvent(CartLifecycleEvent.SESSION_ENDED, null)
  }

  /**
   * Get current lifecycle state
   */
  getLifecycleState(): CartLifecycleState {
    return { ...this.state }
  }

  /**
   * Get lifecycle configuration
   */
  getConfig(): CartLifecycleConfig {
    return { ...this.config }
  }

  /**
   * Update lifecycle configuration
   */
  updateConfig(newConfig: Partial<CartLifecycleConfig>): void {
    this.config = { ...this.config, ...newConfig }
    console.log('⚙️ Cart lifecycle config updated:', this.config)
  }

  /**
   * Check if cart is considered stale
   */
  isCartStale(cart: Cart): boolean {
    const now = new Date()
    const cartAge = (now.getTime() - cart.updated_at.getTime()) / 1000
    return cartAge > this.config.max_cart_age_seconds
  }

  /**
   * Get time since last activity in seconds
   */
  getTimeSinceLastActivity(): number {
    const now = new Date()
    return Math.floor((now.getTime() - this.state.last_activity_timestamp.getTime()) / 1000)
  }

  /**
   * Clear all active timers
   */
  private clearTimers(): void {
    if (this.state.idle_timer_id) {
      window.clearTimeout(this.state.idle_timer_id)
      this.state.idle_timer_id = null
    }
    
    if (this.state.auto_clear_timer_id) {
      window.clearTimeout(this.state.auto_clear_timer_id)
      this.state.auto_clear_timer_id = null
    }
  }

  /**
   * Reset lifecycle state
   */
  reset(): void {
    this.clearTimers()
    this.state = {
      last_activity_timestamp: new Date(),
      idle_timer_id: null,
      auto_clear_timer_id: null,
      is_idle: false,
      lifecycle_events: []
    }
    console.log('🔄 Cart lifecycle state reset')
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.clearTimers()
    this.eventHandlers.clear()
    console.log('🧹 Cart lifecycle service destroyed')
  }
}

/**
 * Global cart lifecycle service instance
 * Can be imported and used across the application
 */
export const cartLifecycleService = new CartLifecycleManagementService()

/**
 * Convenience functions for common lifecycle operations
 */
export const CartLifecycleHelpers = {
  /**
   * Initialize cart lifecycle tracking
   */
  initializeForCart: (cart: Cart) => {
    cartLifecycleService.onCartCreated(cart)
  },

  /**
   * Track cart modification
   */
  trackCartUpdate: (cart: Cart) => {
    cartLifecycleService.onCartUpdated(cart)
  },

  /**
   * Track cart clearing
   */
  trackCartClear: (reason: string = 'manual') => {
    cartLifecycleService.onCartCleared(reason)
  },

  /**
   * Track order placement
   */
  trackOrderPlacement: (cart: Cart, orderNumber: string) => {
    cartLifecycleService.onOrderPlaced(cart, orderNumber)
  },

  /**
   * Track order completion
   */
  trackOrderCompletion: (orderNumber: string) => {
    cartLifecycleService.onOrderCompleted(orderNumber)
  }
}