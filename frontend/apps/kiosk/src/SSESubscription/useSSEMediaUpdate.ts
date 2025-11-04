// useSSEMediaUpdate.ts
//
// Purpose:
// React hook to listen for media update SSE events and delegate media update
// handling to provided callback. Keeps SSE running globally; this hook only wires the event.
//
// Integration:
// - Use in MediaUpdateEventBridge component at a high level (e.g., under App providers)
// - The callback should handle silent media downloads and cache updates
// - Do not pause/disconnect other SSE streams; all updates continue under the hood

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent, type MediaUpdateEvent } from './sseService'

export interface UseSSEMediaUpdateProps {
  /**
   * Called when media update arrives
   * @param mediaType The type of media to update (item, category_open, etc.)
   * @param identifier The identifier for the media (item_id, category name, etc.)
   */
  onMediaUpdate: (mediaType: string, identifier: string) => void
}

export function useSSEMediaUpdate({ onMediaUpdate }: UseSSEMediaUpdateProps) {
  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    if (event.event_type !== 'MEDIA_UPDATE') return

    const mediaEvent = event as MediaUpdateEvent
    console.log('📦 MEDIA_UPDATE SSE:', mediaEvent)

    // media_type and media_path are optional in SSE event
    if (mediaEvent.media_type && mediaEvent.media_path) {
      onMediaUpdate(mediaEvent.media_type, mediaEvent.media_path)
    }
  }, [onMediaUpdate])

  useEffect(() => {
    // NOTE: Connection lifecycle is managed by AuthContext (login/init/logout)
    // This hook only subscribes to events - no connect() call needed here

    // Register only the media update event
    sseService.onEvent('MEDIA_UPDATE', handleSSEEvent)

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
