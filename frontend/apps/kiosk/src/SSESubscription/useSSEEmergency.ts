// useSSEEmergency.ts
//
// Purpose:
// React hook to subscribe to SSE emergency mode state changes.
// Returns whether emergency overlay should be shown (backend connection lost).
//
// Behavior:
// - Subscribes to sseService.onEmergencyMode() on mount
// - Updates local state when emergency mode activates/deactivates
// - Emergency mode = true: Max reconnection attempts reached, show overlay
// - Emergency mode = false: Connection restored, hide overlay
//
// Integration:
// - Use in App.tsx to control EmergencyOverlay visibility
// - Component will auto-show after ~1 minute of backend downtime
// - Component will auto-hide when backend connection restored

import { useEffect, useState } from 'react'
import { sseService } from './sseService'

/**
 * useSSEEmergency
 *
 * Subscribes to SSE emergency mode state and returns current status.
 *
 * @returns {Object} Emergency mode state
 * @returns {boolean} isEmergencyMode - true when overlay should be shown
 *
 * @example
 * ```tsx
 * function App() {
 *   const { isEmergencyMode } = useSSEEmergency()
 *
 *   return (
 *     <>
 *       <Routes>...</Routes>
 *       <EmergencyOverlay isVisible={isEmergencyMode} />
 *     </>
 *   )
 * }
 * ```
 */
export function useSSEEmergency() {
  const [isEmergencyMode, setIsEmergencyMode] = useState<boolean>(
    sseService.getEmergencyMode()
  )

  useEffect(() => {
    // Subscribe to emergency mode changes
    const handleEmergencyModeChange = (isActive: boolean) => {
      console.log(`🚨 useSSEEmergency: Emergency mode ${isActive ? 'ACTIVATED' : 'DEACTIVATED'}`)
      setIsEmergencyMode(isActive)
    }

    sseService.onEmergencyMode(handleEmergencyModeChange)

    // No cleanup needed - subscription persists like other SSE event handlers
    // The sseService is a singleton that lives for the entire app lifetime
    return () => {
      // Intentionally left blank - emergency handlers persist globally
    }
  }, [])

  return {
    isEmergencyMode
  }
}
