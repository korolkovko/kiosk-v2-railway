// File: src/services/orderLifecycleManagement.service.ts
//
// Purpose:
// Minimal foundation service for order lifecycle management and memory optimization.
// Provides structure for future implementation of order cleanup, memory management.
// Clean interface for order retention policies and garbage collection.

import type { Order } from '../models/domain/order'
import { OrderStatus, FSMState } from '../models/domain/order'

/**
 * Order lifecycle events enum
 */
export enum OrderLifecycleEvent {
  ORDER_CREATED = 'ORDER_CREATED',
  ORDER_ACTIVATED = 'ORDER_ACTIVATED',
  ORDER_COMPLETED = 'ORDER_COMPLETED',
  ORDER_EXPIRED = 'ORDER_EXPIRED',
  ORDER_ARCHIVED = 'ORDER_ARCHIVED',
  ORDER_PURGED = 'ORDER_PURGED',
  MEMORY_CLEANUP = 'MEMORY_CLEANUP'
}

/**
 * Order lifecycle configuration
 */
export interface OrderLifecycleConfig {
  max_active_orders: number
  max_completed_orders: number
  completed_order_retention_seconds: number
  failed_order_retention_seconds: number
  enable_auto_cleanup: boolean
  cleanup_interval_seconds: number
  enable_memory_monitoring: boolean
  memory_cleanup_threshold_mb: number
}

/**
 * Default order lifecycle configuration
 */
export const DEFAULT_ORDER_LIFECYCLE_CONFIG: OrderLifecycleConfig = {
  max_active_orders: 10,
  max_completed_orders: 50,
  completed_order_retention_seconds: 3600, // 1 hour
  failed_order_retention_seconds: 1800, // 30 minutes
  enable_auto_cleanup: false, // Disabled for now
  cleanup_interval_seconds: 300, // 5 minutes
  enable_memory_monitoring: false, // Disabled for now
  memory_cleanup_threshold_mb: 100
}

/**
 * Order lifecycle state
 */
export interface OrderLifecycleState {
  active_orders_count: number
  completed_orders_count: number
  failed_orders_count: number
  archived_orders_count: number
  last_cleanup_timestamp: Date
  memory_usage_estimate_mb: number
}

/**
 * Order lifecycle event handler type
 */
export type OrderLifecycleEventHandler = (
  event: OrderLifecycleEvent,
  order?: Order,
  metadata?: Record<string, any>
) => void

/**
 * Order Lifecycle Management Service
 * 
 * MINIMAL FOUNDATION IMPLEMENTATION
 * This service provides the structure for future order lifecycle management:
 * - Memory optimization and cleanup
 * - Order retention policies
 * - Automatic archiving and purging
 * - Memory usage monitoring
 * 
 * Currently implements basic tracking and configuration.
 * Full memory management will be added when needed.
 */
export class OrderLifecycleManagementService {
  private config: OrderLifecycleConfig
  private state: OrderLifecycleState
  private eventHandlers: Set<OrderLifecycleEventHandler>
  private cleanupTimer: number | null

  constructor(config: Partial<OrderLifecycleConfig> = {}) {
    this.config = { ...DEFAULT_ORDER_LIFECYCLE_CONFIG, ...config }
    this.state = {
      active_orders_count: 0,
      completed_orders_count: 0,
      failed_orders_count: 0,
      archived_orders_count: 0,
      last_cleanup_timestamp: new Date(),
      memory_usage_estimate_mb: 0
    }
    this.eventHandlers = new Set()
    this.cleanupTimer = null
  }

  /**
   * Register event handler for order lifecycle events
   */
  onLifecycleEvent(handler: OrderLifecycleEventHandler): () => void {
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
    event: OrderLifecycleEvent,
    order?: Order,
    metadata: Record<string, any> = {}
  ): void {
    console.log(`🔄 Order Lifecycle Event: ${event}`, { 
      order: order?.order_id,
      metadata,
      state: this.state 
    })
    
    // Notify all handlers
    this.eventHandlers.forEach(handler => {
      try {
        handler(event, order, metadata)
      } catch (error) {
        console.error('Order lifecycle event handler error:', error)
      }
    })
  }

  /**
   * Handle order creation
   */
  onOrderCreated(order: Order): void {
    this.state.active_orders_count++
    this.updateMemoryEstimate()
    this.emitEvent(OrderLifecycleEvent.ORDER_CREATED, order)
    
    // Check if we need cleanup
    this.checkCleanupNeeded()
  }

  /**
   * Handle order activation (when order starts processing)
   */
  onOrderActivated(order: Order): void {
    this.emitEvent(OrderLifecycleEvent.ORDER_ACTIVATED, order)
  }

  /**
   * Handle order completion
   */
  onOrderCompleted(order: Order): void {
    this.state.active_orders_count = Math.max(0, this.state.active_orders_count - 1)
    
    if (this.isOrderSuccessfullyCompleted(order)) {
      this.state.completed_orders_count++
    } else {
      this.state.failed_orders_count++
    }
    
    this.updateMemoryEstimate()
    this.emitEvent(OrderLifecycleEvent.ORDER_COMPLETED, order)
    
    // Schedule cleanup if auto-cleanup is enabled
    if (this.config.enable_auto_cleanup) {
      this.scheduleOrderCleanup(order)
    }
  }

  /**
   * Handle order expiration
   */
  onOrderExpired(order: Order): void {
    this.state.active_orders_count = Math.max(0, this.state.active_orders_count - 1)
    this.state.failed_orders_count++
    this.updateMemoryEstimate()
    this.emitEvent(OrderLifecycleEvent.ORDER_EXPIRED, order)
  }

  /**
   * Archive order (move to long-term storage)
   */
  archiveOrder(order: Order): void {
    if (this.isOrderSuccessfullyCompleted(order)) {
      this.state.completed_orders_count = Math.max(0, this.state.completed_orders_count - 1)
    } else {
      this.state.failed_orders_count = Math.max(0, this.state.failed_orders_count - 1)
    }
    
    this.state.archived_orders_count++
    this.updateMemoryEstimate()
    this.emitEvent(OrderLifecycleEvent.ORDER_ARCHIVED, order)
  }

  /**
   * Purge order (remove completely)
   */
  purgeOrder(order: Order): void {
    // TODO: Implement actual order removal from storage
    this.updateMemoryEstimate()
    this.emitEvent(OrderLifecycleEvent.ORDER_PURGED, order)
  }

  /**
   * Check if cleanup is needed based on limits
   */
  private checkCleanupNeeded(): void {
    const needsCleanup = 
      this.state.active_orders_count > this.config.max_active_orders ||
      this.state.completed_orders_count > this.config.max_completed_orders ||
      (this.config.enable_memory_monitoring && 
       this.state.memory_usage_estimate_mb > this.config.memory_cleanup_threshold_mb)

    if (needsCleanup) {
      console.log('🧹 Order cleanup needed:', this.state)
      this.performCleanup()
    }
  }

  /**
   * Perform memory cleanup
   */
  private performCleanup(): void {
    const beforeState = { ...this.state }
    
    // TODO: Implement actual cleanup logic
    // - Remove expired orders
    // - Archive old completed orders
    // - Purge very old orders
    
    this.state.last_cleanup_timestamp = new Date()
    this.updateMemoryEstimate()
    
    this.emitEvent(OrderLifecycleEvent.MEMORY_CLEANUP, undefined, {
      before_state: beforeState,
      after_state: this.state,
      cleanup_timestamp: this.state.last_cleanup_timestamp
    })
    
    console.log('🧹 Memory cleanup completed:', {
      before: beforeState,
      after: this.state
    })
  }

  /**
   * Schedule order cleanup after retention period
   */
  private scheduleOrderCleanup(order: Order): void {
    const retentionSeconds = this.isOrderSuccessfullyCompleted(order)
      ? this.config.completed_order_retention_seconds
      : this.config.failed_order_retention_seconds

    // TODO: Implement actual scheduling
    console.log(`⏰ Order cleanup scheduled for ${order.order_id} in ${retentionSeconds} seconds`)
  }

  /**
   * Check if order is successfully completed
   */
  private isOrderSuccessfullyCompleted(order: Order): boolean {
    return order.status === OrderStatus.COMPLETED &&
           order.fsm_state === FSMState.SENT_TO_KDS
  }

  /**
   * Update memory usage estimate
   */
  private updateMemoryEstimate(): void {
    // Rough estimate: each order ~1KB in memory
    const totalOrders = this.state.active_orders_count + 
                       this.state.completed_orders_count + 
                       this.state.failed_orders_count
    
    this.state.memory_usage_estimate_mb = (totalOrders * 1024) / (1024 * 1024) // Convert to MB
  }

  /**
   * Get current lifecycle state
   */
  getLifecycleState(): OrderLifecycleState {
    return { ...this.state }
  }

  /**
   * Get lifecycle configuration
   */
  getConfig(): OrderLifecycleConfig {
    return { ...this.config }
  }

  /**
   * Update lifecycle configuration
   */
  updateConfig(newConfig: Partial<OrderLifecycleConfig>): void {
    this.config = { ...this.config, ...newConfig }
    
    // Restart cleanup timer if interval changed
    if (newConfig.cleanup_interval_seconds && this.config.enable_auto_cleanup) {
      this.startCleanupTimer()
    }
    
    console.log('⚙️ Order lifecycle config updated:', this.config)
  }

  /**
   * Start automatic cleanup timer
   */
  private startCleanupTimer(): void {
    this.stopCleanupTimer()
    
    if (this.config.enable_auto_cleanup) {
      this.cleanupTimer = window.setInterval(() => {
        this.performCleanup()
      }, this.config.cleanup_interval_seconds * 1000)
      
      console.log(`⏰ Cleanup timer started (${this.config.cleanup_interval_seconds}s interval)`)
    }
  }

  /**
   * Stop automatic cleanup timer
   */
  private stopCleanupTimer(): void {
    if (this.cleanupTimer) {
      window.clearInterval(this.cleanupTimer)
      this.cleanupTimer = null
      console.log('⏰ Cleanup timer stopped')
    }
  }

  /**
   * Force immediate cleanup
   */
  forceCleanup(): void {
    console.log('🧹 Force cleanup requested')
    this.performCleanup()
  }

  /**
   * Get memory usage statistics
   */
  getMemoryStats(): {
    estimated_usage_mb: number
    total_orders: number
    active_orders: number
    completed_orders: number
    failed_orders: number
    archived_orders: number
  } {
    return {
      estimated_usage_mb: this.state.memory_usage_estimate_mb,
      total_orders: this.state.active_orders_count + 
                   this.state.completed_orders_count + 
                   this.state.failed_orders_count + 
                   this.state.archived_orders_count,
      active_orders: this.state.active_orders_count,
      completed_orders: this.state.completed_orders_count,
      failed_orders: this.state.failed_orders_count,
      archived_orders: this.state.archived_orders_count
    }
  }

  /**
   * Reset lifecycle state
   */
  reset(): void {
    this.stopCleanupTimer()
    this.state = {
      active_orders_count: 0,
      completed_orders_count: 0,
      failed_orders_count: 0,
      archived_orders_count: 0,
      last_cleanup_timestamp: new Date(),
      memory_usage_estimate_mb: 0
    }
    console.log('🔄 Order lifecycle state reset')
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopCleanupTimer()
    this.eventHandlers.clear()
    console.log('🧹 Order lifecycle service destroyed')
  }
}

/**
 * Global order lifecycle service instance
 */
export const orderLifecycleService = new OrderLifecycleManagementService()

/**
 * Convenience functions for common lifecycle operations
 */
export const OrderLifecycleHelpers = {
  /**
   * Track order creation
   */
  trackOrderCreation: (order: Order) => {
    orderLifecycleService.onOrderCreated(order)
  },

  /**
   * Track order completion
   */
  trackOrderCompletion: (order: Order) => {
    orderLifecycleService.onOrderCompleted(order)
  },

  /**
   * Get memory usage summary
   */
  getMemorySummary: () => {
    return orderLifecycleService.getMemoryStats()
  },

  /**
   * Force cleanup if needed
   */
  cleanupIfNeeded: () => {
    const stats = orderLifecycleService.getMemoryStats()
    const config = orderLifecycleService.getConfig()
    
    if (stats.total_orders > config.max_active_orders + config.max_completed_orders) {
      orderLifecycleService.forceCleanup()
    }
  }
}