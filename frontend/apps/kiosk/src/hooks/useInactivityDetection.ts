// File: src/hooks/useInactivityDetection.ts
//
// Purpose:
// Hook for detecting user inactivity on kiosk interface.
// Triggers countdown overlay after idle timeout, resets on activity.
// Used for auto-resetting kiosk to initial state when abandoned.

import { useState, useEffect, useCallback, useRef } from 'react'

interface UseInactivityDetectionOptions {
  idleTimeout?: number // Milliseconds before showing countdown (default: 60000 = 60 sec)
  countdownDuration?: number // Countdown seconds (default: 10)
  onTimeout?: () => void // Callback when countdown reaches 0
  disabled?: boolean // Disable inactivity detection (default: false)
}

interface UseInactivityDetectionResult {
  isInactive: boolean // True when showing countdown overlay
  countdown: number // Current countdown value (10, 9, 8... 0)
  resetActivity: () => void // Manual reset function
}

export function useInactivityDetection(
  options: UseInactivityDetectionOptions = {}
): UseInactivityDetectionResult {
  const {
    idleTimeout = 60000, // 60 seconds
    countdownDuration = 10, // 10 seconds
    onTimeout,
    disabled = false
  } = options

  const [isInactive, setIsInactive] = useState(false)
  const [countdown, setCountdown] = useState(countdownDuration)

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null)
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null)
  const isCountdownActiveRef = useRef(false)
  const generationRef = useRef(0) // increments on resets/clears to invalidate stale timers
  const lastActivityTsRef = useRef<number>(Date.now())

  /**
   * Clear all timers and reset countdown state
   */
  const clearTimers = useCallback(() => {
    // PHASE 3: Uncomment when debugging - used in logs below
    // const prevGen = generationRef.current
    generationRef.current += 1
    // const gen = generationRef.current

    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current)
      idleTimerRef.current = null
      // PHASE 3: Timer management - Uncomment when debugging timer clearing or generation issues
      // console.log(`🧹 Cleared idle timer gen ${gen} (invalidated prev gen ${prevGen})`)
    }
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current)
      countdownTimerRef.current = null
      // PHASE 3: Timer management - Uncomment when debugging countdown timer clearing
      // console.log(`🧹 Cleared countdown timer gen ${gen}`)
    }
    // IMPORTANT: Also reset countdown active flag and hide overlay
    // This ensures clean state when timers are cleared
    if (isCountdownActiveRef.current) {
      isCountdownActiveRef.current = false
      setIsInactive(false)
    }
  }, [])

  /**
   * Start countdown from 10 to 0
   */
  const startCountdown = useCallback(() => {
    const genAtStart = generationRef.current
    // PHASE 4: User action log - Uncomment when debugging inactivity detection behavior
    // console.log(`⏰ Inactivity detected, starting countdown... gen ${genAtStart}`)
    isCountdownActiveRef.current = true
    setIsInactive(true)
    setCountdown(countdownDuration)

    let currentCount = countdownDuration

    countdownTimerRef.current = setInterval(() => {
      // Guard against stale countdown after activity or disable
      if (generationRef.current !== genAtStart) {
        // CRITICAL: NEVER remove - detects stale timer bugs!
        console.log(`⏭️ Ignoring stale countdown tick for gen ${genAtStart}, current gen ${generationRef.current}`)
        if (countdownTimerRef.current) {
          clearInterval(countdownTimerRef.current as any)
          countdownTimerRef.current = null
        }
        return
      }

      currentCount -= 1
      setCountdown(currentCount)

      if (currentCount <= 0) {
        // PHASE 4: User action log - Uncomment when debugging countdown completion
        // console.log('⏰ Countdown finished, executing timeout action')
        isCountdownActiveRef.current = false
        // Invalidate and clear timers before executing timeout action
        clearTimers()

        if (onTimeout) {
          onTimeout()
        }

        // Hide overlay after timeout completes
        setIsInactive(false)
      }
    }, 1000)
  }, [countdownDuration, onTimeout, clearTimers])

  /**
   * Reset idle timer - called on any user activity
   */
  const resetActivity = useCallback(() => {
    // If disabled, clear timers and don't start new ones
    if (disabled) {
      clearTimers()
      return
    }

    lastActivityTsRef.current = Date.now()

    // PHASE 1: Noisy logs - Uncomment only when debugging frequent timer resets
    // if (isCountdownActiveRef.current) {
    //   console.log('✅ Activity detected, canceling countdown at:', new Date().toISOString())
    // } else {
    //   console.log('🔄 Idle timer reset at:', new Date().toISOString())
    // }

    // Invalidate any pending timers and reset state
    clearTimers()

    // Capture generation for this scheduling to ignore stale callbacks
    const genForThisSchedule = generationRef.current

    // Start new idle timer
    idleTimerRef.current = setTimeout(() => {
      if (generationRef.current !== genForThisSchedule) {
        console.log(`⏭️ Ignoring stale idle timeout callback for gen ${genForThisSchedule}, current gen ${generationRef.current}`)
        return
      }
      // PHASE 4: User action log - Uncomment when debugging idle timeout triggers
      // console.log('⏰ Idle timeout reached, starting countdown at:', new Date().toISOString())
      startCountdown()
    }, idleTimeout)

    // PHASE 3: Timer management - Uncomment when debugging timer scheduling
    // console.log(`🕒 Scheduled idle timeout in ${idleTimeout}ms for gen ${genForThisSchedule}`)
  }, [disabled, idleTimeout, startCountdown, clearTimers])

  /**
   * Handle user activity events - use ref to stabilize callback
   */
  const resetActivityRef = useRef(resetActivity)

  // Keep ref in sync with latest resetActivity
  useEffect(() => {
    resetActivityRef.current = resetActivity
  }, [resetActivity])

  // Immediate clear when detection is disabled
  useEffect(() => {
    if (disabled) {
      // PHASE 3: Timer management - Uncomment when debugging disable/enable behavior
      // console.log('🧹 Inactivity detection disabled, clearing timers immediately')
      clearTimers()
    }
  }, [disabled, clearTimers])

  const handleUserActivity = useCallback(() => {
    // PHASE 1: Very noisy - fires on EVERY mouse move! Uncomment only when debugging activity detection issues
    // console.log('🔵 User activity detected at:', new Date().toISOString())

    // If countdown overlay is showing, ignore transient activity to avoid canceling it
    if (isCountdownActiveRef.current) {
      // PHASE 1: Uncomment when debugging countdown cancellation issues
      // console.log('⏭️ Ignoring user activity during active countdown')
      return
    }
    resetActivityRef.current()
  }, []) // Stable callback - no dependencies

  // Start initial timer on mount only; cleanup on unmount
  useEffect(() => {
    if (!disabled) {
      // PHASE 2: Lifecycle log - Uncomment when debugging mount/initialization issues
      // console.log('🚀 Starting initial idle timer on mount')
      resetActivity()
    }

    // Cleanup on unmount - clear all timers
    return () => {
      // PHASE 2: Lifecycle log - Uncomment when debugging unmount/cleanup issues
      // console.log('🧹 Hook unmount, clearing all timers')
      clearTimers()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])  // Intentionally empty - run once on mount, cleanup on unmount only

  // When detection becomes enabled again, start or refresh idle timer
  // Avoid canceling active countdown: check countdown ref and defer to next tick
  useEffect(() => {
    if (disabled) return
    if (isCountdownActiveRef.current) {
      // PHASE 2: Lifecycle log - Uncomment when debugging re-enable edge cases
      // console.log('⏸️ Detection enabled but countdown active; skipping idle timer start')
      return
    }
    if (!isInactive) {
      // PHASE 2: Lifecycle log - Uncomment when debugging enable/disable transitions
      // console.log('🚀 Detection enabled, scheduling idle timer start')
      setTimeout(() => {
        if (!disabled && !isCountdownActiveRef.current) {
          // PHASE 2: Lifecycle log - Uncomment when debugging deferred timer start
          // console.log('🚀 Detection enabled, starting idle timer')
          resetActivityRef.current()
        } else {
          // PHASE 2: Lifecycle log - Uncomment when debugging deferred start cancellation
          // console.log('⏭️ Skipping deferred idle start due to disabled or active countdown')
        }
      }, 0)
    }
  }, [disabled, isInactive])

  // Set up activity listeners - disabled when countdown is showing
  useEffect(() => {
    // Don't listen for activity when countdown overlay is showing
    if (isInactive) {
      // PHASE 2: Lifecycle log - Uncomment when debugging listener attachment issues
      // console.log('⏸️ Activity listeners disabled - countdown is showing')
      return
    }

    // PHASE 1: Noisy - fires on every state change. Uncomment when debugging listener lifecycle
    // console.log('▶️ Activity listeners enabled')

    // Activity event types
    const events = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll']

    // Add listeners
    events.forEach(event => {
      document.addEventListener(event, handleUserActivity)
    })

    // Cleanup
    return () => {
      // PHASE 1: Noisy - fires frequently. Uncomment when debugging cleanup issues
      // console.log('🛑 Cleaning up activity listeners')
      events.forEach(event => {
        document.removeEventListener(event, handleUserActivity)
      })
    }
  }, [handleUserActivity, isInactive])

  return {
    isInactive,
    countdown,
    resetActivity
  }
}
