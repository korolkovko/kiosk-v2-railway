// File: src/SSESubscription/useSSEOrderUpdates.ts
//
// Purpose:
// React hook for managing SSE-based real-time order status updates.
// Follows the same pattern as existing useSSEItemUpdates.ts.
// Updates OrderContext directly - no separate order status service needed.

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent } from './sseService'
import type { FSMEventHistoryEntry } from '../models/domain/order'
import { OrderStatus, FSMState, FSMEvent } from '../models/domain/order'

export interface SSEConnectionStatus {
  connected: boolean
  reconnecting: boolean
}

export interface OrderUpdateData {
  order_id: number
  status?: OrderStatus
  fsm_state?: FSMState
  fsm_event_to_add?: FSMEventHistoryEntry
  pickup_number?: string
  pin_code?: string
  total_amount_gross?: number
  currency?: string
  // Timestamps
  order_time?: Date
  updated_at?: Date
}

export interface UseSSEOrderUpdatesProps {
  currentKioskUsername: string  // Current kiosk username for filtering events
  onOrderUpdate: (updatedOrder: OrderUpdateData) => void
  onConnectionStatusChange?: (status: SSEConnectionStatus) => void
}

/**
 * Hook for managing SSE-based order status updates
 *
 * Updates OrderContext directly with FSM events and status changes.
 * No separate order status service - OrderContext is single source of truth.
 *
 * Features:
 * - Handles ORDER_STATUS_CHANGED events
 * - Handles ORDER_EVENT_TRIGGERED events (FSM events)
 * - Filters events by kiosk_username (only processes events for THIS kiosk)
 * - Updates fsm_event_history array in OrderContext
 *
 * Pattern:
 * Follows the same filtering approach as useSSEServiceMode:
 * - Backend broadcasts to ALL kiosks via 'kiosk_broadcast' channel
 * - Frontend filters by comparing event.kiosk_username with current kiosk
 * - Ensures each kiosk only sees its own orders
 */
export function useSSEOrderUpdates({
  currentKioskUsername,
  onOrderUpdate,
  onConnectionStatusChange
}: UseSSEOrderUpdatesProps) {

  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    const eventData = event as any

    // Handle ORDER_STATUS_CHANGED events
    if (eventData.event_type === 'ORDER_STATUS_CHANGED' && eventData.order_id) {
      console.log('📡 ORDER_STATUS_CHANGED SSE:', eventData)

      // IMPORTANT: Filter by kiosk_username - only process events for THIS kiosk
      if (eventData.kiosk_username !== currentKioskUsername) {
        console.log(`⏭️ Ignoring order status event for '${eventData.kiosk_username}' (this kiosk is '${currentKioskUsername}')`)
        return
      }

      console.log(`✅ Processing order status event for this kiosk: '${currentKioskUsername}', order: ${eventData.order_id}`)

      const orderUpdate: OrderUpdateData = {
        order_id: eventData.order_id,
        status: eventData.status as OrderStatus,
        updated_at: new Date()
      }

      onOrderUpdate(orderUpdate)
    }

    // Handle ORDER_EVENT_TRIGGERED events
    else if (eventData.event_type === 'ORDER_EVENT_TRIGGERED' && eventData.order_id) {
      console.log('📡 ORDER_EVENT_TRIGGERED SSE:', eventData)

      // IMPORTANT: Filter by kiosk_username - only process events for THIS kiosk
      if (eventData.kiosk_username !== currentKioskUsername) {
        console.log(`⏭️ Ignoring order event for '${eventData.kiosk_username}' (this kiosk is '${currentKioskUsername}')`)
        return
      }

      console.log(`✅ Processing order event for this kiosk: '${currentKioskUsername}', order: ${eventData.order_id}, event: ${eventData.fsm_event}`)

      const orderUpdate: OrderUpdateData = {
        order_id: eventData.order_id,
        fsm_state: eventData.fsm_state as FSMState,
        updated_at: new Date(),
        // Add FSM event to history
        fsm_event_to_add: {
          event: eventData.fsm_event as FSMEvent,
          fsm_state_after: eventData.fsm_state,
          timestamp: new Date(),
          actor_type: eventData.actor_type
        }
      }

      onOrderUpdate(orderUpdate)
    }
  }, [currentKioskUsername, onOrderUpdate])

  const handleConnectionStatus = useCallback((connected: boolean) => {
    if (onConnectionStatusChange) {
      onConnectionStatusChange({
        connected,
        reconnecting: !connected && sseService.isConnected()
      })
    }
  }, [onConnectionStatusChange])

  useEffect(() => {
    // NOTE: Connection lifecycle is managed by AuthContext (login/init/logout)
    // This hook only subscribes to events - no connect() call needed here

    // Register handlers for order-related SSE events
    sseService.onEvent('ORDER_STATUS_CHANGED', handleSSEEvent)
    sseService.onEvent('ORDER_EVENT_TRIGGERED', handleSSEEvent)

    // Connection status monitoring (reuses existing SSE service)
    sseService.onConnectionStatus(handleConnectionStatus)

    // Cleanup function
    return () => {
      // Note: We don't disconnect the SSE service here since it's shared with Items
    }
  }, [handleSSEEvent, handleConnectionStatus])

  return {
    isConnected: sseService.isConnected(),
    disconnect: () => {
      console.log('🔌 Order SSE disconnect requested')
      // Note: This affects the shared SSE connection
      sseService.disconnect()
    },
    reconnect: () => {
      console.log('🔗 Order SSE reconnect requested')
      sseService.connect()
    }
  }
}

/**
 * Helper function to parse order status from SSE event
 * TODO: Implement when backend order event structure is defined
 */
export function parseOrderStatusFromSSEEvent(event: any): OrderUpdateData | null {
  try {
    // TODO: Implement actual parsing logic based on backend event structure
    console.log('🔍 Parsing order status from SSE event:', event)
    
    return {
      order_id: event.order_id || 0,
      updated_at: new Date()
    }
  } catch (error) {
    console.error('❌ Failed to parse order SSE event:', error)
    return null
  }
}

/**
 * Helper function to validate order update data
 */
export function validateOrderUpdateData(data: OrderUpdateData): boolean {
  if (!data.order_id || data.order_id <= 0) {
    console.warn('⚠️ Invalid order update data: missing or invalid order_id')
    return false
  }
  
  return true
}

/**
 * Helper function to format order update for logging
 */
export function formatOrderUpdateForLogging(data: OrderUpdateData): string {
  const updates = []

  if (data.status) updates.push(`status: ${data.status}`)
  if (data.fsm_state) updates.push(`fsm: ${data.fsm_state}`)
  if (data.fsm_event_to_add) updates.push(`event: ${data.fsm_event_to_add.event}`)

  return `Order ${data.order_id} - ${updates.join(', ')}`
}

/**
 * Constants for order SSE event types (for future backend implementation)
 */
export const ORDER_SSE_EVENT_TYPES = {
  ORDER_STATUS_CHANGED: 'ORDER_STATUS_CHANGED',
  ORDER_PAYMENT_STATUS_CHANGED: 'ORDER_PAYMENT_STATUS_CHANGED',
  ORDER_FSM_STATE_CHANGED: 'ORDER_FSM_STATE_CHANGED',
  ORDER_COMPLETED: 'ORDER_COMPLETED',
  ORDER_FAILED: 'ORDER_FAILED',
  ORDER_CANCELLED: 'ORDER_CANCELLED',
  ORDER_PICKUP_READY: 'ORDER_PICKUP_READY'
} as const

export type OrderSSEEventType = typeof ORDER_SSE_EVENT_TYPES[keyof typeof ORDER_SSE_EVENT_TYPES]