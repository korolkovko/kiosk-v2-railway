// File: src/hooks/useOrderProcessingLifecycle.ts
//
// Purpose:
// Custom hook for managing order processing lifecycle in kiosk.
// Extracts order processing logic from MainScreen to reduce complexity.
// Handles order placement, SSE updates, and completion flow.

import { useState, useCallback } from 'react'
import { useOrder } from '../contexts/OrderContext'
import { useAuth } from '../contexts/AuthContext'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { useSSEOrderUpdates, type OrderUpdateData } from '../SSESubscription/useSSEOrderUpdates'
import { orderPlacementService } from '../services/orderPlacement.service'
import { orderProcessingLifecycleService } from '../services/orderProcessingLifecycle.service'
import { OrderStatus } from '../models/domain/order'
import type { CartItem } from '../models/domain/cart'
import type { NavigationMode } from '../stores/navigationStore'

export interface OrderProcessingCallbacks {
  clearCart: () => void
  clearCurrentOrder: () => void
  setActiveCategory: (category: string) => void
  setNavigationMode: (mode: NavigationMode) => void
  showScreenSaver: () => void
  navigateBackFromOrderProcessing: () => void
  navigateToOrderProcessing: () => void
  setOrderInProgress: (inProgress: boolean) => void
}

export interface UseOrderProcessingLifecycleResult {
  // State
  isPlacingOrder: boolean
  processingOrderId: number | null
  processingOrderPickupNumber: string | null
  processingOrderPinCode: string | null
  
  // Actions
  handlePlaceOrder: (cartItems: CartItem[], cartVM: any) => Promise<void>
  handleOrderUpdate: (orderUpdate: OrderUpdateData) => void
  handleOrderProcessingComplete: () => void
  handleOrderProcessingError: (error: string) => void
}

/**
 * useOrderProcessingLifecycle
 * 
 * Manages complete order processing workflow:
 * - Order placement when "9" button pressed
 * - SSE order status updates
 * - Order completion handling with 4-second delay
 * - Error handling and cleanup
 */
export function useOrderProcessingLifecycle(
  callbacks: OrderProcessingCallbacks
): UseOrderProcessingLifecycleResult {

  const { currentOrder, updateOrderStatus } = useOrder()
  const { user } = useAuth()
  const { categories } = useCategoriesContext()

  // Get promoted category name from first category
  const promotedCategoryName = categories.length > 0 ? categories[0].name : 'promoted'

  // Order placement state
  const [isPlacingOrder, setIsPlacingOrder] = useState(false)
  
  // Order processing state (independent of OrderContext)
  const [processingOrderId, setProcessingOrderId] = useState<number | null>(null)
  const [processingOrderPickupNumber, setProcessingOrderPickupNumber] = useState<string | null>(null)
  const [processingOrderPinCode, setProcessingOrderPinCode] = useState<string | null>(null)

  // Handle order status updates from SSE
  const handleOrderUpdate = useCallback((orderUpdate: OrderUpdateData) => {
    // Delegate to lifecycle service for processing
    const isTerminalState = orderProcessingLifecycleService.handleOrderUpdateDuringProcessing(
      orderUpdate,
      currentOrder,
      updateOrderStatus
    )

    // Store pickup details for processing screen if completed
    if (orderUpdate.status === OrderStatus.COMPLETED && currentOrder) {
      setProcessingOrderPickupNumber(currentOrder.pickup_number)
      setProcessingOrderPinCode(currentOrder.pin_code)
    }

    // Note: Cleanup is handled by OrderProcessingStatusesHandle component after customer sees completion
  }, [currentOrder, updateOrderStatus])

  // Set up SSE listener for order updates - only process events for THIS kiosk
  useSSEOrderUpdates({
    currentKioskUsername: user?.username || '',
    onOrderUpdate: handleOrderUpdate
  })

  // Handle order placement (triggered by "9" key/button)
  const handlePlaceOrder = useCallback(async (cartItems: CartItem[], cartVM: any) => {
    if (cartItems.length === 0 || isPlacingOrder) {
      return
    }

    // Delegate to order processing lifecycle service
    await orderProcessingLifecycleService.startOrderProcessing(
      cartItems,
      cartVM,
      orderPlacementService,
      callbacks,
      {
        setProcessingOrderId,
        setProcessingOrderPickupNumber,
        setProcessingOrderPinCode,
        setIsPlacingOrder,
        setOrderInProgress: callbacks.setOrderInProgress,
        updateOrderStatus
      }
    )
  }, [isPlacingOrder, callbacks, updateOrderStatus])

  // Handle order processing completion (called after countdown finishes)
  const handleOrderProcessingComplete = useCallback(() => {
    console.log('📦 Order processing completed in lifecycle hook, performing cleanup')

    // Clear processing state
    setProcessingOrderId(null)
    setProcessingOrderPickupNumber(null)
    setProcessingOrderPinCode(null)

    // Delegate cleanup to lifecycle service
    orderProcessingLifecycleService.handleOrderProcessingCompletion(
      currentOrder,
      [], // cartItems will be provided by caller
      callbacks,
      promotedCategoryName,
      {
        setProcessingOrderId,
        setProcessingOrderPickupNumber,
        setProcessingOrderPinCode
      }
    )
  }, [currentOrder, callbacks, promotedCategoryName])

  // Handle order processing error
  const handleOrderProcessingError = useCallback((error: string) => {
    console.error('❌ Order processing error in lifecycle hook:', error)

    // Clear processing state
    setProcessingOrderId(null)
    setProcessingOrderPickupNumber(null)
    setProcessingOrderPinCode(null)

    // Delegate error handling to lifecycle service
    orderProcessingLifecycleService.handleOrderProcessingError(
      error,
      currentOrder,
      callbacks,
      promotedCategoryName,
      {
        setProcessingOrderId,
        setProcessingOrderPickupNumber,
        setProcessingOrderPinCode
      }
    )
  }, [currentOrder, callbacks, promotedCategoryName])

  return {
    // State
    isPlacingOrder,
    processingOrderId,
    processingOrderPickupNumber,
    processingOrderPinCode,
    
    // Actions
    handlePlaceOrder,
    handleOrderUpdate,
    handleOrderProcessingComplete,
    handleOrderProcessingError
  }
}