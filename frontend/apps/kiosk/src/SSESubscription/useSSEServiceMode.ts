// useSSEServiceMode.ts
//
// Purpose:
// React hook to listen for kiosk service mode SSE events and delegate activation/deactivation
// handling to provided callbacks. Keeps SSE running globally; this hook only wires the event.
//
// Integration:
// - Place a small "EventBridge" component at a high level (e.g., under App providers)
//   that uses this hook and performs UI navigation, cart clearing, and overlay control.
// - Do not pause/disconnect other SSE streams; business updates continue under the hood.

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent, type KioskServiceModeChangedEvent } from './sseService'

export interface UseSSEServiceModeProps {
  /**
   * Current kiosk username to filter events
   */
  currentKioskUsername: string

  /**
   * Called when service mode activation arrives (only for this kiosk)
   * @param pictureName The logical media name or null if no media provided
   */
  onActivate: (pictureName: string | null) => void

  /**
   * Called when service mode deactivation arrives (only for this kiosk)
   */
  onDeactivate: () => void
}

export function useSSEServiceMode({ currentKioskUsername, onActivate, onDeactivate }: UseSSEServiceModeProps) {
  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    if (event.event_type !== 'KIOSK_SERVICE_MODE_CHANGED') return

    const smEvent = event as KioskServiceModeChangedEvent
    console.log('📡 KIOSK_SERVICE_MODE_CHANGED SSE:', smEvent)

    // IMPORTANT: Filter by kiosk_username - only process events for THIS kiosk
    if (smEvent.kiosk_username !== currentKioskUsername) {
      console.log(`⏭️ Ignoring service mode event for '${smEvent.kiosk_username}' (this kiosk is '${currentKioskUsername}')`)
      return
    }

    console.log(`✅ Processing service mode event for this kiosk: '${currentKioskUsername}'`)

    if (smEvent.is_service_mode) {
      onActivate(smEvent.service_picture_name ?? null)
    } else {
      onDeactivate()
    }
  }, [currentKioskUsername, onActivate, onDeactivate])

  useEffect(() => {
    // NOTE: Connection lifecycle is managed by AuthContext (login/init/logout)
    // This hook only subscribes to events - no connect() call needed here

    // Register only the service mode event
    sseService.onEvent('KIOSK_SERVICE_MODE_CHANGED', handleSSEEvent)

    // No teardown: the shared sseService persists across components
    return () => {
      // Intentionally left blank
    }
  }, [handleSSEEvent])

  return {
    isConnected: sseService.isConnected(),
    reconnect: () => sseService.connect(),
    disconnect: () => sseService.disconnect()
  }
}