// ServiceModeEventBridge.tsx
//
// Purpose:
// High-level invisible component that bridges SSE service mode events to UI actions.
// - Listens to KIOSK_SERVICE_MODE_CHANGED via [TypeScript.useSSEServiceMode()](frontend/apps/kiosk/src/SSESubscription/useSSEServiceMode.ts:1)
// - On activation: clears UI state, ensures media cached, navigates to /service-mode, blocks input
// - If activation arrives while on /order-handling page, defers via pending flag until customer leaves
// - Checks BOTH location.pathname AND navigationMode to ensure safety during order processing
// - On deactivation: navigates to /main, where MainScreen shows screensaver on mount (useScreenSaver(true))
// Notes:
// - Keeps SSE connections and contexts alive; only user input is blocked during service mode

import { FunctionComponent, useCallback, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useSSEServiceMode } from '../SSESubscription/useSSEServiceMode'
import { mediaCacheService } from '../services/mediaCache.service'
import { useServiceModeStore } from '../stores/ServiceModeStore'
import { useNavigationStore } from '../stores/navigationStore'
import { useCartActions } from '../stores/cartStore'
import { useAuth } from '../contexts/AuthContext'

const ServiceModeEventBridge: FunctionComponent = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  // Cart actions
  const { clearCart } = useCartActions()

  // Navigation state
  const {
    navigationMode,
    resetNavigation,
    setNavigationMode,
    setActiveCategory
  } = useNavigationStore()

  // Service mode store
  const {
    isPendingActivation,
    pictureName,
    activate,
    deactivate,
    setPendingActivation,
    clearPendingActivation
  } = useServiceModeStore()

  const performActivation = useCallback(async (name: string | null) => {
    // Clean everything: cart + UI selection/navigation
    try {
      clearCart()
    } catch (e) {
      console.warn('ServiceModeEventBridge: clearCart failed (continuing):', e)
    }

    // Reset navigation to initial state and select default mode
    try {
      resetNavigation()
      setNavigationMode('categories')
      setActiveCategory(null)
    } catch (e) {
      console.warn('ServiceModeEventBridge: navigation reset failed (continuing):', e)
    }

    // Ensure media cached on-demand if a name provided
    if (name) {
      try {
        await mediaCacheService.ensureServiceModeMediaCached(name)
      } catch (e) {
        console.warn(`ServiceModeEventBridge: ensureServiceModeMediaCached("${name}") failed, will show fallback text`, e)
      }
    }

    // Activate UI and navigate
    activate(name)
    navigate('/service-mode', { replace: true })
    clearPendingActivation()
  }, [activate, clearCart, clearPendingActivation, navigate, resetNavigation, setActiveCategory, setNavigationMode])

  // When SSE says activate
  const onActivate = useCallback((name: string | null) => {
    // If on order handling page OR in order_processing mode, defer until customer leaves
    if (location.pathname === '/order-handling' || navigationMode === 'order_processing') {
      setPendingActivation(name)
      return
    }
    // Immediate activation
    void performActivation(name)
  }, [location.pathname, navigationMode, performActivation, setPendingActivation])

  // When SSE says deactivate
  const onDeactivate = useCallback(() => {
    deactivate()
    // Navigate to main; MainScreen shows screensaver on mount (useScreenSaver(true))
    // When user dismisses screensaver, MainScreen will reset to first category (promoted)
    navigate('/main', { replace: true })

    // Note: Cart is already empty (cleared on activation, can't be modified during service mode)
    // Navigation will be reset to promoted category when user dismisses screensaver
  }, [deactivate, navigate])

  // Wire SSE - only process events for THIS kiosk
  useSSEServiceMode({
    currentKioskUsername: user?.username || '',
    onActivate,
    onDeactivate
  })

  // If we had a pending activation and order processing has finished (navigated away),
  // perform activation now using the stored pictureName.
  useEffect(() => {
    if (
      isPendingActivation &&
      navigationMode !== 'order_processing' &&
      location.pathname !== '/order-handling'
    ) {
      void performActivation(pictureName ?? null)
    }
  }, [isPendingActivation, navigationMode, location.pathname, performActivation, pictureName])

  return null
}

export default ServiceModeEventBridge