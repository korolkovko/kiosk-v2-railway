// ServiceModeOverlay.tsx
//
// Purpose:
// Fullscreen overlay that blocks ALL user interactions (keyboard and mouse) while visible.
// Under-the-hood operations (SSE updates, contexts, timers) continue normally.
// This overlay should be mounted on the Service Mode page and any time service mode is active.

import { FunctionComponent, useEffect, useRef } from 'react'

export type ServiceModeOverlayProps = {
  isVisible: boolean
  className?: string
}

/**
 * ServiceModeOverlay
 * - Captures focus on mount and prevents all key presses (preventDefault + stopPropagation)
 * - Blocks all pointer/mouse events by overlaying a high z-index element
 * - Does not disrupt background app logic or SSE; only user input is blocked
 */
const ServiceModeOverlay: FunctionComponent<ServiceModeOverlayProps> = ({
  isVisible,
  className = ''
}) => {
  const overlayRef = useRef<HTMLDivElement>(null)

  // Focus overlay when it becomes visible
  useEffect(() => {
    if (isVisible && overlayRef.current) {
      overlayRef.current.focus()
    }
  }, [isVisible])

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
      // High z-index overlay that covers the entire viewport and captures inputs
      className={`fixed inset-0 z-[20000] bg-transparent cursor-not-allowed ${className}`}
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
      {/* Optional: subtle indicator */}
      <div className="absolute bottom-4 right-4 px-3 py-1 rounded bg-[rgba(0,0,0,0.6)] text-white text-sm select-none pointer-events-none">
        Service mode active
      </div>
    </div>
  )
}

export default ServiceModeOverlay