// EmergencyOverlay.tsx
//
// Purpose:
// Fullscreen overlay that appears when SSE connection cannot be established (emergency mode).
// Blocks ALL user interactions and displays an emergency message or picture from IndexedDB.
//
// Behavior:
// - Triggered when max SSE reconnection attempts reached (after ~1 minute of backend downtime)
// - Shows "emergency" picture from cache if available (loaded from IndexedDB)
// - Falls back to text message "Something went wrong" if no picture cached
// - Blocks all keyboard and mouse input (like ServiceModeOverlay)
// - SSE continues background polling (60s intervals) under the hood
// - Auto-dismisses when connection restored
//
// Integration:
// - Mount in App.tsx at root level (above all routes)
// - Uses useSSEEmergency hook to track emergency mode state
// - Picture key: "emergency" (stored in IndexedDB service mode table)

import { FunctionComponent, useEffect, useRef, useState } from 'react'
import { mediaCacheService } from '../services/mediaCache.service'

export type EmergencyOverlayProps = {
  isVisible: boolean
  className?: string
}

/**
 * EmergencyOverlay
 * - Fullscreen overlay blocking all user input when backend connection lost
 * - Displays emergency picture from cache or fallback text
 * - Captures focus and prevents all key/mouse events (like ServiceModeOverlay)
 * - Auto-hides when SSE connection restored
 */
const EmergencyOverlay: FunctionComponent<EmergencyOverlayProps> = ({
  isVisible,
  className = ''
}) => {
  const overlayRef = useRef<HTMLDivElement>(null)
  const [mediaUrl, setMediaUrl] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // Load emergency picture from IndexedDB cache
  useEffect(() => {
    if (!isVisible) return

    let blobUrl: string | null = null
    let cancelled = false

    const loadEmergencyPicture = async () => {
      setIsLoading(true)
      setMediaUrl(null)
      setMediaType(null)

      try {
        // Try to load "emergency" picture from service mode cache
        const entry = await mediaCacheService.getServiceModeMediaEntry('emergency')
        if (cancelled) return

        if (entry) {
          console.log('🚨 EmergencyOverlay: Loaded emergency picture from cache')
          blobUrl = URL.createObjectURL(entry.blob)
          setMediaUrl(blobUrl)
          setMediaType(entry.type)
        } else {
          console.log('🚨 EmergencyOverlay: No emergency picture in cache, using fallback text')
          setMediaUrl(null)
          setMediaType(null)
        }
      } catch (error) {
        console.error('🚨 EmergencyOverlay: Failed to load emergency picture:', error)
        setMediaUrl(null)
        setMediaType(null)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadEmergencyPicture()

    return () => {
      cancelled = true
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl)
      }
    }
  }, [isVisible])

  // Focus overlay when it becomes visible
  useEffect(() => {
    if (isVisible && overlayRef.current) {
      overlayRef.current.focus()
    }
  }, [isVisible])

  // Block all keyboard and mouse events when visible
  useEffect(() => {
    if (!isVisible) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent any key interaction
      e.preventDefault()
      e.stopPropagation()
    }

    const handlePointerEvent = (e: Event) => {
      // Prevent any mouse/touch interaction
      e.preventDefault()
      e.stopPropagation()
    }

    // Capture at the window level as an additional safety net
    window.addEventListener('keydown', handleKeyDown, { capture: true })
    window.addEventListener('keypress', handleKeyDown, { capture: true })
    window.addEventListener('keyup', handleKeyDown, { capture: true })
    window.addEventListener('pointerdown', handlePointerEvent, { capture: true })
    window.addEventListener('pointerup', handlePointerEvent, { capture: true })
    window.addEventListener('click', handlePointerEvent, { capture: true })
    window.addEventListener('mousedown', handlePointerEvent, { capture: true })
    window.addEventListener('mouseup', handlePointerEvent, { capture: true })
    window.addEventListener('touchstart', handlePointerEvent, { capture: true })
    window.addEventListener('touchend', handlePointerEvent, { capture: true })

    return () => {
      window.removeEventListener('keydown', handleKeyDown, { capture: true } as any)
      window.removeEventListener('keypress', handleKeyDown, { capture: true } as any)
      window.removeEventListener('keyup', handleKeyDown, { capture: true } as any)
      window.removeEventListener('pointerdown', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('pointerup', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('click', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('mousedown', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('mouseup', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('touchstart', handlePointerEvent, { capture: true } as any)
      window.removeEventListener('touchend', handlePointerEvent, { capture: true } as any)
    }
  }, [isVisible])

  if (!isVisible) return null

  return (
    <div
      ref={overlayRef}
      // High z-index overlay that covers the entire viewport
      className={`fixed inset-0 z-[30000] bg-black cursor-not-allowed ${className}`}
      tabIndex={0}
      // As a second layer of defense, also cancel events at element level
      onKeyDown={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onKeyUp={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onKeyPress={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onPointerDown={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onPointerUp={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
      }}
    >
      {/* Media content or fallback text */}
      <div className="w-full h-full flex items-center justify-center">
        {isLoading ? (
          // Loading state
          <div className="text-[2rem] font-mono text-[#c0c0c0]">Loading…</div>
        ) : mediaUrl && mediaType === 'video' ? (
          // Video emergency picture
          <video
            className="w-full h-full object-cover"
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
          >
            <source src={mediaUrl} type="video/mp4" />
            Emergency mode
          </video>
        ) : mediaUrl && mediaType === 'image' ? (
          // Image emergency picture
          <img
            className="w-full h-full object-cover"
            alt="Emergency mode"
            src={mediaUrl}
          />
        ) : (
          // Fallback text when no emergency picture available
          <div className="text-center px-8">
            <div className="text-[4rem] font-mono text-[#ff6b6b] uppercase tracking-wide mb-4">
              Something went wrong
            </div>
            <div className="text-[2rem] font-mono text-[#c0c0c0]">
              Please try again later
            </div>
          </div>
        )}
      </div>

      {/* Debug indicator (bottom-right corner) */}
      <div className="absolute bottom-4 right-4 px-3 py-1 rounded bg-[rgba(0,0,0,0.6)] text-white text-sm select-none pointer-events-none">
        Emergency mode • Reconnecting…
      </div>
    </div>
  )
}

export default EmergencyOverlay
