// File: src/hooks/useKioskCleanup.ts
//
// Purpose:
// Custom hook for centralized kiosk cleanup operations.
// Extracts cleanup logic from MainScreen to reduce complexity.
// Handles cart clearing, order cleanup, navigation reset, and screensaver.

import { useCallback } from 'react'
import { useOrder } from '../contexts/OrderContext'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { CartClearingHelpers } from '../services/cartClearingTriggers.service'
import { OrderStatus } from '../models/domain/order'
import type { CartItem } from '../models/domain/cart'
import type { NavigationMode } from '../stores/navigationStore'

export interface KioskCleanupCallbacks {
  clearCart: () => void
  clearCurrentOrder: () => void
  setActiveCategory: (category: string) => void
  setNavigationMode: (mode: NavigationMode) => void
  showScreenSaver: () => void
  navigateBackFromOrderProcessing: () => void
}

export interface UseKioskCleanupResult {
  resetToScreensaver: () => void
  handleInactivityTimeout: () => void
  handleInactivityReset: () => void
  handleOrderProcessingComplete: (cartItems: CartItem[]) => void
}

/**
 * useKioskCleanup
 * 
 * Centralizes all kiosk cleanup operations:
 * - Reset to screensaver (manual/inactivity)
 * - Order completion cleanup with 4-second delay
 * - Cart and order state cleanup
 * - Navigation state reset
 */
export function useKioskCleanup(
  callbacks: KioskCleanupCallbacks,
  resetActivity: () => void
): UseKioskCleanupResult {

  const { currentOrder } = useOrder()
  const { categories } = useCategoriesContext()

  // Shared cleanup logic for resetting to screensaver
  const resetToScreensaver = useCallback(() => {
    callbacks.clearCart()

    // Clear current order (if exists) - OrderContext handles cleanup
    if (currentOrder) {
      callbacks.clearCurrentOrder()
    }

    // Exit order processing mode if active
    callbacks.navigateBackFromOrderProcessing()

    // Reset to first category (promoted category) if categories are loaded
    if (categories.length > 0) {
      callbacks.setActiveCategory(categories[0].name)
    }
    callbacks.setNavigationMode('categories')
    callbacks.showScreenSaver()
  }, [callbacks, currentOrder, categories])

  // Handle inactivity timeout - reset to initial state, clear cart, and show screensaver
  const handleInactivityTimeout = useCallback(() => {
    // PHASE 4: User action log - Uncomment when debugging inactivity timeout behavior
    // console.log('🔄 Inactivity timeout reached, resetting to initial state')
    resetToScreensaver()
  }, [resetToScreensaver])

  // Handle Enter key during inactivity - immediate reset to screensaver
  const handleInactivityReset = useCallback(() => {
    // PHASE 4: User action log - Uncomment when debugging Enter key during countdown
    // console.log('⏩ User pressed Enter during inactivity, resetting immediately to screensaver')

    // IMPORTANT: Perform cleanup and navigation reset FIRST
    // This ensures state is properly reset before canceling countdown
    resetToScreensaver()

    // Then reset activity to cancel inactivity countdown/overlay
    // Order matters: navigation state must be set before dismissing overlay
    resetActivity()
  }, [resetToScreensaver, resetActivity])

  // Handle order processing completion (called after countdown finishes)
  const handleOrderProcessingComplete = useCallback((cartItems: CartItem[]) => {
    // PHASE 4: User action log - Uncomment when debugging order processing completion
    // console.log('📦 Order processing completed, performing cleanup and returning to screensaver')

    // Now perform the cleanup that was delayed
    if (currentOrder) {
      const orderForClearing = {
        ...currentOrder,
        status: OrderStatus.COMPLETED,
        updated_at: new Date()
      }

      // Create proper Cart object for clearing service
      const cartForClearing = {
        items: cartItems,
        created_at: new Date(),
        updated_at: new Date()
      }

      CartClearingHelpers.handleOrderCompletion(orderForClearing, cartForClearing)
    }

    // Clear cart and order
    callbacks.clearCart()
    callbacks.clearCurrentOrder()
    
    // Return to screensaver
    resetToScreensaver()
  }, [currentOrder, callbacks, resetToScreensaver])

  return {
    resetToScreensaver,
    handleInactivityTimeout,
    handleInactivityReset,
    handleOrderProcessingComplete
  }
}