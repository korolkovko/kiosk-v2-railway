// MenuRefreshEventBridge.tsx
//
// Purpose:
// High-level invisible component that bridges SSE menu activation events to UI actions.
// Mirrors the login flow for menu changes (same steps, minus initial cache clearing).
//
// Flow (similar to Login.tsx):
// 0. Clear cart (items from old menu are no longer valid)
// 1. Fetch menu structure (getAllMenuItemsForPreload)
// 2. Download new media incrementally (downloadAllMedia - skips already cached)
// 3. Refetch categories (fetchCategories - categories come from active menu)
// 4. Refetch items (refetchItems - items come from active menu)
// 5. Navigate to /main (unless on service mode page)
//
// Protection:
// - If menu activation arrives while on /order-handling page, it's deferred (pending flag)
// - Checks BOTH location.pathname AND navigationMode to ensure safety
// - Pending activation is performed when user leaves /order-handling page
// - This prevents:
//   * Loading overlay from appearing on top of order handling page
//   * Cart clearing during payment/receipt display
//   * Navigation away from order handling before customer finishes
// - Ensures graceful completion of order placement before menu change
//
// Behavior:
// - If on /service-mode page: download silently in background, no UI changes
// - If on any other page: show loading overlay, download, navigate to /main
// - If order processing active: defer activation until order completes

import { FunctionComponent, useCallback, useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useSSEMenuUpdates } from '../SSESubscription/useSSEMenuUpdates'
import { useSSEEmergency } from '../SSESubscription/useSSEEmergency'
import { menuRefreshService } from '../services/menuRefresh.service'
import { useItems } from '../contexts/ItemsContext'
import { useCategories } from '../contexts/CategoriesContext'
import { useCartActions } from '../stores/cartStore'
import { useNavigationStore } from '../stores/navigationStore'
import MediaLoadingProgress from './MediaLoadingProgress'
import type { DownloadProgress } from '../services/mediaCache.service'

const MenuRefreshEventBridge: FunctionComponent = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { refetch: refetchItems } = useItems()
  const { fetchCategories } = useCategories()
  const { clearCart } = useCartActions()
  const { navigationMode } = useNavigationStore()

  // Loading state
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null)

  // Pending menu activation state (when order processing is active)
  const [pendingMenuActivation, setPendingMenuActivation] = useState<{
    menuId: number
    menuName: string
  } | null>(null)

  // Perform the actual menu activation (download media, refetch data, navigate)
  const performMenuActivation = useCallback(async (menuId: number, menuName: string) => {
    console.log(`📋 Performing menu activation: ${menuName} (ID: ${menuId})`)

    const isOnServiceModePage = location.pathname === '/service-mode'

    // Clear cart - items from old menu are no longer valid
    try {
      console.log('🧹 Clearing cart (menu changed)...')
      clearCart()
    } catch (e) {
      console.warn('MenuRefreshEventBridge: clearCart failed (continuing):', e)
    }

    // Show loading overlay only if NOT on service mode page
    if (!isOnServiceModePage) {
      setIsRefreshing(true)
    }

    try {
      // Download new media incrementally
      const result = await menuRefreshService.handleMenuActivation(
        menuId,
        menuName,
        (progress) => {
          if (!isOnServiceModePage) {
            setDownloadProgress(progress)
          }
        }
      )

      if (!result.success) {
        console.error('❌ Menu refresh failed:', result.error)
        // TODO: Show error notification to user
        return
      }

      // Refresh categories context (categories come from active menu)
      console.log('🔄 Refreshing categories context...')
      await fetchCategories()

      // Refresh items context (items come from active menu)
      console.log('🔄 Refreshing items context...')
      await refetchItems()

      // Navigate to main page only if NOT on service mode page
      if (!isOnServiceModePage) {
        console.log('🔄 Navigating to main page...')
        navigate('/main', { replace: true })
      } else {
        console.log('🛠️ Silent refresh complete (service mode active)')
      }

      // Clear pending activation after successful completion
      setPendingMenuActivation(null)

    } catch (error) {
      console.error('❌ Menu refresh error:', error)
      // TODO: Show error notification to user
    } finally {
      setIsRefreshing(false)
      setDownloadProgress(null)
    }
  }, [location.pathname, navigate, refetchItems, fetchCategories, clearCart])

  // When SSE menu activation arrives, check if we can activate immediately
  const onMenuActivated = useCallback((menuId: number, menuName: string) => {
    console.log(`📋 Menu activation received: ${menuName} (ID: ${menuId})`)

    // If on order handling page OR in order_processing mode, defer until customer leaves
    if (location.pathname === '/order-handling' || navigationMode === 'order_processing') {
      console.log('⏸️ Order handling in progress, deferring menu activation...')
      setPendingMenuActivation({ menuId, menuName })
      return
    }

    // Immediate activation
    void performMenuActivation(menuId, menuName)
  }, [location.pathname, navigationMode, performMenuActivation])

  // Wire SSE menu updates
  useSSEMenuUpdates({
    onMenuActivated
  })

  // Listen to SSE connection restoration (exiting emergency mode)
  // When backend comes back online after extended downtime, re-fetch all data
  const { isEmergencyMode } = useSSEEmergency()
  const wasInEmergencyModeRef = useRef(false)

  // Detect when we exit emergency mode (connection restored after outage)
  useEffect(() => {
    // If we were in emergency mode and now we're not, connection was restored
    if (wasInEmergencyModeRef.current && !isEmergencyMode) {
      console.log('🔄 MenuRefreshEventBridge: Connection restored from emergency mode, refetching all data...')

      // Auto-refetch categories and items when server comes back
      const refetchData = async () => {
        try {
          console.log('🔄 Refreshing categories after connection restoration...')
          await fetchCategories()

          console.log('🔄 Refreshing items after connection restoration...')
          await refetchItems()

          console.log('✅ Data refresh complete - categories and items restored')
        } catch (error) {
          console.error('❌ Failed to refresh data after connection restoration:', error)
        }
      }

      void refetchData()
    }

    // Update the ref for next check
    wasInEmergencyModeRef.current = isEmergencyMode
  }, [isEmergencyMode, fetchCategories, refetchItems])

  // If we had a pending menu activation and order processing has finished, perform it now
  // But only if we're NOT on the order handling page anymore (route has changed)
  useEffect(() => {
    if (
      pendingMenuActivation &&
      navigationMode !== 'order_processing' &&
      location.pathname !== '/order-handling'
    ) {
      console.log('✅ Order processing finished and left order handling page, performing pending menu activation...')
      void performMenuActivation(pendingMenuActivation.menuId, pendingMenuActivation.menuName)
    }
  }, [pendingMenuActivation, navigationMode, location.pathname, performMenuActivation])

  // Render loading overlay if refreshing
  if (isRefreshing && downloadProgress) {
    return (
      <MediaLoadingProgress
        current={downloadProgress.current}
        total={downloadProgress.total}
        currentItem={downloadProgress.currentItem}
        quotaUsed={downloadProgress.quotaUsed}
        quotaAvailable={downloadProgress.quotaAvailable}
      />
    )
  }

  return null
}

export default MenuRefreshEventBridge
