// EmergencyModeEventBridge.tsx
//
// Purpose:
// High-level invisible component that bridges SSE emergency mode events to UI actions.
// - Monitors emergency mode state changes via useSSEEmergency()
// - On activation: clears cart and resets navigation (same as service mode)
// - On deactivation: navigates to /main where screensaver will show
// Rationale: Emergency mode means backend is down for extended period (30+ seconds minimum)
//            By the time it activates, session is abandoned - clean state immediately
//
// Flow:
// 1. Backend down → Emergency activates → Clear cart + reset nav
// 2. Backend up → Emergency deactivates → Navigate to /main → Screensaver shows
// 3. User dismisses screensaver → MainScreen resets navigation to promoted category
//
// Notes:
// - Same pattern as ServiceModeEventBridge but simpler (no pending logic, no media)
// - Emergency overlay blocks all input automatically (z-index: 30000)

import { FunctionComponent, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSSEEmergency } from '../SSESubscription/useSSEEmergency'
import { useNavigationStore } from '../stores/navigationStore'
import { useCartActions } from '../stores/cartStore'

const EmergencyModeEventBridge: FunctionComponent = () => {
  const navigate = useNavigate()
  const { isEmergencyMode } = useSSEEmergency()

  // Cart actions
  const { clearCart } = useCartActions()

  // Navigation state
  const {
    resetNavigation,
    setNavigationMode,
    setActiveCategory
  } = useNavigationStore()

  // Track previous emergency mode state to detect activation/deactivation
  const prevEmergencyModeRef = useRef<boolean>(isEmergencyMode)

  useEffect(() => {
    const wasEmergency = prevEmergencyModeRef.current
    const isNowEmergency = isEmergencyMode

    // Detect emergency mode ACTIVATION (was false, now true)
    if (!wasEmergency && isNowEmergency) {
      console.log('🚨 EmergencyModeEventBridge: Emergency mode ACTIVATED - cleaning state')

      // Clean everything: cart + UI selection/navigation (same as service mode activation)
      try {
        clearCart()
      } catch (e) {
        console.warn('EmergencyModeEventBridge: clearCart failed (continuing):', e)
      }

      // Reset navigation to initial state
      try {
        resetNavigation()
        setNavigationMode('categories')
        setActiveCategory(null)
      } catch (e) {
        console.warn('EmergencyModeEventBridge: navigation reset failed (continuing):', e)
      }

      // Note: No navigation here - user stays on current page with overlay shown
      // EmergencyOverlay automatically blocks all input
    }

    // Detect emergency mode DEACTIVATION (was true, now false)
    if (wasEmergency && !isNowEmergency) {
      console.log('✅ EmergencyModeEventBridge: Emergency mode DEACTIVATED - navigating to main')

      // Navigate to main; MainScreen shows screensaver on mount (useScreenSaver(true))
      // When user dismisses screensaver, MainScreen will reset to first category (promoted)
      navigate('/main', { replace: true })

      // Note: Cart is already empty (cleared on activation)
      // Navigation will be reset to promoted category when user dismisses screensaver
    }

    // Update ref for next comparison
    prevEmergencyModeRef.current = isNowEmergency
  }, [isEmergencyMode, clearCart, resetNavigation, setNavigationMode, setActiveCategory, navigate])

  return null
}

export default EmergencyModeEventBridge
