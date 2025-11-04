// File: src/contexts/OrderContext.tsx
//
// Purpose:
// Order context for managing order status tracking with SSE integration.
// Provides order state management and real-time status updates.
// Follows same pattern as existing AuthContext and ItemsContext.

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { Order } from '../models/domain/order'
import { OrderStatus, FSMState } from '../models/domain/order'
import type { OrderVM } from '../models/view/order.vm'

interface OrderContextType {
  // Current order state
  currentOrder: Order | null
  currentOrderVM: OrderVM | null
  
  // Order history (for future extension)
  recentOrders: Order[]
  
  // Order operations
  createOrder: (orderData: Partial<Order>) => Promise<void>
  updateOrderStatus: (orderNumber: string, updates: Partial<Order>) => void
  clearCurrentOrder: () => void
  
  // Order lifecycle
  markOrderAsCompleted: (orderNumber: string) => void
  cancelOrder: (orderNumber: string) => void
  
  // SSE integration (minimal foundation)
  isSSEConnected: boolean
  connectToOrderUpdates: (orderNumber: string) => void
  disconnectFromOrderUpdates: () => void
  
  // UI state
  isLoading: boolean
  lastError: string | null
  
  // Memory management (for future extension)
  clearOrderHistory: () => void
  getOrderByNumber: (orderNumber: string) => Order | null
}

const OrderContext = createContext<OrderContextType | undefined>(undefined)

export const OrderProvider = ({ children }: { children: ReactNode }) => {
  // Order state
  const [currentOrder, setCurrentOrder] = useState<Order | null>(null)
  const [currentOrderVM, setCurrentOrderVM] = useState<OrderVM | null>(null)
  const [recentOrders, setRecentOrders] = useState<Order[]>([])
  
  // SSE state (minimal foundation)
  const [isSSEConnected, setIsSSEConnected] = useState(false)
  
  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [lastError, setLastError] = useState<string | null>(null)

  /**
   * Create new order (placeholder for future API integration)
   */
  const createOrder = useCallback(async (orderData: Partial<Order>) => {
    setIsLoading(true)
    setLastError(null)
    
    try {
      // TODO: Integrate with order creation API
      // For now, create a mock order structure
      const newOrder: Order = {
        order_id: orderData.order_id || Date.now(),
        pickup_number: orderData.pickup_number || `P${Math.floor(Math.random() * 1000)}`,
        pin_code: orderData.pin_code || `${Math.floor(Math.random() * 10000)}`.padStart(4, '0'),
        status: orderData.status || OrderStatus.PENDING,
        fsm_state: orderData.fsm_state || FSMState.INIT,
        fsm_event_history: orderData.fsm_event_history || [],
        total_amount_net: orderData.total_amount_net || 0,
        total_amount_vat: orderData.total_amount_vat || 0,
        total_amount_gross: orderData.total_amount_gross || 0,
        currency: orderData.currency || 'RUB',
        order_time: orderData.order_time || new Date(),
        created_at: new Date(),
        updated_at: new Date(),
        ...orderData
      }
      
      setCurrentOrder(newOrder)
      
      // TODO: Generate OrderVM from domain model
      // This will be implemented when we create the order view model service
      console.log('Order created:', newOrder)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create order'
      setLastError(errorMessage)
      console.error('Order creation failed:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Update order status (for SSE updates and initial order creation)
   */
  const updateOrderStatus = useCallback((orderNumber: string, updates: Partial<Order>) => {
    setCurrentOrder(prevOrder => {
      // If no previous order exists and updates contain a complete order, set it as current order
      if (!prevOrder && updates.order_id && updates.order_id.toString() === orderNumber) {
        const newOrder: Order = {
          order_id: updates.order_id,
          pickup_number: updates.pickup_number || '',
          pin_code: updates.pin_code || '',
          status: updates.status || OrderStatus.PENDING,
          fsm_state: updates.fsm_state || FSMState.INIT,
          fsm_event_history: updates.fsm_event_history || [],
          total_amount_net: updates.total_amount_net || 0,
          total_amount_vat: updates.total_amount_vat || 0,
          total_amount_gross: updates.total_amount_gross || 0,
          currency: updates.currency || 'RUB',
          order_time: updates.order_time || new Date(),
          created_at: updates.created_at || new Date(),
          updated_at: new Date(),
          ...updates
        } as Order;
        
        console.log('📦 OrderContext: Setting initial order:', newOrder);
        return newOrder;
      }
      
      // If previous order exists and IDs match, update it
      if (prevOrder && prevOrder.order_id.toString() === orderNumber) {
        const updatedOrder: Order = {
          ...prevOrder,
          ...updates,
          updated_at: new Date()
        }

        return updatedOrder;
      }

      // If order IDs don't match, don't update
      return prevOrder;
    })
    
    // Update recent orders if needed
    setRecentOrders(prevOrders =>
      prevOrders.map(order =>
        order.order_id.toString() === orderNumber
          ? { ...order, ...updates, updated_at: new Date() }
          : order
      )
    )
  }, [])

  /**
   * Disconnect from order SSE updates
   */
  const disconnectFromOrderUpdates = useCallback(() => {
    // TODO: Implement SSE disconnection
    console.log('Disconnecting from order updates')
    setIsSSEConnected(false)
  }, [])

  /**
   * Clear current order
   */
  const clearCurrentOrder = useCallback(() => {
    if (currentOrder) {
      // Move to recent orders before clearing
      setRecentOrders(prev => [currentOrder, ...prev.slice(0, 9)]) // Keep last 10 orders
    }

    setCurrentOrder(null)
    setCurrentOrderVM(null)
    setLastError(null)

    // Disconnect from SSE updates
    disconnectFromOrderUpdates()
  }, [currentOrder, disconnectFromOrderUpdates])

  /**
   * Mark order as completed
   */
  const markOrderAsCompleted = useCallback((orderNumber: string) => {
    updateOrderStatus(orderNumber, {
      status: OrderStatus.COMPLETED,
      fsm_state: FSMState.SENT_TO_KDS
    })
    
    // Clear current order after a delay (for future implementation)
    setTimeout(() => {
      if (currentOrder?.order_id.toString() === orderNumber) {
        clearCurrentOrder()
      }
    }, 5000) // 5 second delay to show completion status
  }, [currentOrder, updateOrderStatus, clearCurrentOrder])

  /**
   * Cancel order
   */
  const cancelOrder = useCallback((orderNumber: string) => {
    updateOrderStatus(orderNumber, {
      status: OrderStatus.CANCELLED
    })
  }, [updateOrderStatus])

  /**
   * Connect to order SSE updates (minimal foundation)
   */
  const connectToOrderUpdates = useCallback((orderNumber: string) => {
    // TODO: Implement SSE connection for order updates
    // This will follow the same pattern as existing Items SSE
    console.log(`Connecting to order updates for: ${orderNumber}`)
    setIsSSEConnected(true)
  }, [])

  /**
   * Clear order history (memory management)
   */
  const clearOrderHistory = useCallback(() => {
    setRecentOrders([])
  }, [])

  /**
   * Get order by number
   */
  const getOrderByNumber = useCallback((orderNumber: string): Order | null => {
    if (currentOrder?.order_id.toString() === orderNumber) {
      return currentOrder
    }
    
    return recentOrders.find(order => order.order_id.toString() === orderNumber) || null
  }, [currentOrder, recentOrders])

  const contextValue: OrderContextType = {
    // Current order state
    currentOrder,
    currentOrderVM,
    recentOrders,
    
    // Order operations
    createOrder,
    updateOrderStatus,
    clearCurrentOrder,
    
    // Order lifecycle
    markOrderAsCompleted,
    cancelOrder,
    
    // SSE integration
    isSSEConnected,
    connectToOrderUpdates,
    disconnectFromOrderUpdates,
    
    // UI state
    isLoading,
    lastError,
    
    // Memory management
    clearOrderHistory,
    getOrderByNumber
  }

  return (
    <OrderContext.Provider value={contextValue}>
      {children}
    </OrderContext.Provider>
  )
}

export const useOrder = (): OrderContextType => {
  const context = useContext(OrderContext)
  if (!context) {
    throw new Error('useOrder must be used within OrderProvider')
  }
  return context
}

// Convenience hooks for specific order operations
export const useCurrentOrder = () => {
  const { currentOrder, currentOrderVM } = useOrder()
  return { currentOrder, currentOrderVM }
}

export const useOrderActions = () => {
  const { 
    createOrder, 
    updateOrderStatus, 
    clearCurrentOrder, 
    markOrderAsCompleted, 
    cancelOrder 
  } = useOrder()
  
  return {
    createOrder,
    updateOrderStatus,
    clearCurrentOrder,
    markOrderAsCompleted,
    cancelOrder
  }
}

export const useOrderSSE = () => {
  const { 
    isSSEConnected, 
    connectToOrderUpdates, 
    disconnectFromOrderUpdates 
  } = useOrder()
  
  return {
    isSSEConnected,
    connectToOrderUpdates,
    disconnectFromOrderUpdates
  }
}