// useSSEMenuUpdates.ts
//
// Purpose:
// React hook to listen for menu activation SSE events and delegate menu change
// handling to provided callback. Keeps SSE running globally; this hook only wires the event.
//
// Integration:
// - Use in an EventBridge component at a high level (e.g., under App providers)
// - The callback should handle media downloads, store updates, and UI navigation
// - Do not pause/disconnect other SSE streams; all updates continue under the hood

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent, type MenuActivatedEvent } from './sseService'

export interface UseSSEMenuUpdatesProps {
  /**
   * Called when menu activation arrives
   * @param menuId The ID of the activated menu
   * @param menuName The name of the activated menu
   */
  onMenuActivated: (menuId: number, menuName: string) => void
}

export function useSSEMenuUpdates({ onMenuActivated }: UseSSEMenuUpdatesProps) {
  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    if (event.event_type !== 'MENU_ACTIVATED') return

    const menuEvent = event as MenuActivatedEvent
    console.log('📡 MENU_ACTIVATED SSE:', menuEvent)

    // menu_id and menu_name are optional in SSE event
    if (menuEvent.menu_id !== undefined && menuEvent.menu_name !== undefined) {
      onMenuActivated(menuEvent.menu_id, menuEvent.menu_name)
    }
  }, [onMenuActivated])

  useEffect(() => {
    // NOTE: Connection lifecycle is managed by AuthContext (login/init/logout)
    // This hook only subscribes to events - no connect() call needed here

    // Register only the menu activated event
    sseService.onEvent('MENU_ACTIVATED', handleSSEEvent)

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
