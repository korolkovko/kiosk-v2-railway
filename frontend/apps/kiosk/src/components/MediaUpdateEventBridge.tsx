// MediaUpdateEventBridge.tsx
//
// Purpose:
// High-level invisible component that bridges SSE media update events to silent background updates.
// - Listens to MEDIA_UPDATE via useSSEMediaUpdate()
// - Silently downloads and caches updated media in background
// - No UI interruption, no loading overlays
// - Tolerates 404s gracefully (file might not exist yet)
// - Works in any kiosk state (main, order-handling, service-mode)
//
// Flow:
// 1. SSE MEDIA_UPDATE event arrives
// 2. Call mediaSilentUpdateService.handleMediaUpdate()
// 3. Service downloads media from storage
// 4. Service updates IndexedDB cache (overwrites existing)
// 5. Next time UI requests this media, it gets fresh version from cache
//
// Notes:
// - Silent operation: no user-visible feedback
// - Defensive: catches and logs errors, never throws
// - 404 tolerance: if media not found, logs warning and continues
// - No state management needed: fire-and-forget updates

import { FunctionComponent, useCallback } from 'react'
import { useSSEMediaUpdate } from '../SSESubscription/useSSEMediaUpdate'
import { mediaSilentUpdateService } from '../services/mediaSilentUpdate.service'

const MediaUpdateEventBridge: FunctionComponent = () => {
  /**
   * Handle media update event from SSE
   * Silently download and cache updated media in background
   */
  const onMediaUpdate = useCallback(async (mediaType: string, identifier: string) => {
    console.log(`📦 Processing media update: ${mediaType} - ${identifier}`)

    try {
      const result = await mediaSilentUpdateService.handleMediaUpdate(mediaType, identifier)

      if (result.success) {
        console.log(`✅ Media update successful: ${mediaType} - ${identifier}`)
      } else {
        // 404 or other error - log and continue
        console.warn(`⚠️ Media update failed: ${mediaType} - ${identifier} - ${result.error}`)
      }
    } catch (error) {
      // Defensive: never throw, just log
      console.error(`❌ Media update error: ${mediaType} - ${identifier}`, error)
    }
  }, [])

  // Wire SSE
  useSSEMediaUpdate({
    onMediaUpdate
  })

  return null
}

export default MediaUpdateEventBridge
