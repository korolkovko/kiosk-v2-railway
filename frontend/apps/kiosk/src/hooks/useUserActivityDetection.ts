// File: src/hooks/useUserActivityDetection.ts
//
// Purpose:
// User activity detection hook that tracks user interactions to determine
// when it's safe to perform background operations like token refresh.
// Prevents disrupting user experience during active interactions.

import { useEffect, useRef, useCallback, useState } from 'react'

interface UseUserActivityDetectionOptions {
  /**
   * Time in milliseconds to consider user inactive after last interaction
   * Default: 30 seconds
   */
  inactivityThreshold?: number
  
  /**
   * Events to track for user activity
   * Default: ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
   */
  eventsToTrack?: string[]
  
  /**
   * Enable debug logging
   */
  debug?: boolean
}

interface UserActivityState {
  isActive: boolean
  lastActivityTime: number
  isOrderInProgress: boolean
}

/**
 * useUserActivityDetection
 * 
 * Tracks user activity to determine when it's safe to perform background operations.
 * Monitors mouse movements, clicks, keyboard input, and other interactions.
 * Also tracks critical operations like order placement.
 * 
 * @param options Configuration options for activity detection
 * @returns Object with activity state and control functions
 */
export function useUserActivityDetection(options: UseUserActivityDetectionOptions = {}) {
  const {
    inactivityThreshold = 30 * 1000, // 30 seconds
    eventsToTrack = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'],
    debug = false
  } = options

  const [activityState, setActivityState] = useState<UserActivityState>({
    isActive: false,
    lastActivityTime: Date.now(),
    isOrderInProgress: false
  })

  const lastActivityRef = useRef<number>(Date.now())
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null)
  const eventListenersAttachedRef = useRef<boolean>(false)

  const log = useCallback((message: string, ...args: any[]) => {
    if (debug) {
      console.log(`[useUserActivityDetection] ${message}`, ...args)
    }
  }, [debug])

  /**
   * Handle user activity events
   */
  const handleUserActivity = useCallback(() => {
    const now = Date.now()
    lastActivityRef.current = now
    
    setActivityState(prev => {
      if (!prev.isActive) {
        log('User became active')
      }
      return {
        ...prev,
        isActive: true,
        lastActivityTime: now
      }
    })

    // Clear existing inactivity timer
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current)
    }

    // Set new inactivity timer
    inactivityTimerRef.current = setTimeout(() => {
      log('User became inactive')
      setActivityState(prev => ({
        ...prev,
        isActive: false
      }))
    }, inactivityThreshold)
  }, [inactivityThreshold, log])

  /**
   * Mark order as in progress (critical operation)
   */
  const setOrderInProgress = useCallback((inProgress: boolean) => {
    log(`Order ${inProgress ? 'started' : 'completed'}`)
    setActivityState(prev => ({
      ...prev,
      isOrderInProgress: inProgress
    }))
  }, [log])

  /**
   * Check if user is currently active
   */
  const isUserActive = useCallback(() => {
    return activityState.isActive
  }, [activityState.isActive])

  /**
   * Check if critical operation is in progress
   */
  const isCriticalOperationInProgress = useCallback(() => {
    return activityState.isOrderInProgress
  }, [activityState.isOrderInProgress])

  /**
   * Get time since last activity in milliseconds
   */
  const getTimeSinceLastActivity = useCallback(() => {
    return Date.now() - activityState.lastActivityTime
  }, [activityState.lastActivityTime])

  /**
   * Manually trigger activity (useful for programmatic interactions)
   */
  const triggerActivity = useCallback(() => {
    handleUserActivity()
  }, [handleUserActivity])

  /**
   * Attach event listeners for activity detection
   */
  const attachEventListeners = useCallback(() => {
    if (eventListenersAttachedRef.current) {
      log('Event listeners already attached, skipping')
      return
    }

    log('Attaching activity event listeners')
    
    eventsToTrack.forEach(eventType => {
      document.addEventListener(eventType, handleUserActivity, { passive: true })
    })
    
    eventListenersAttachedRef.current = true
  }, [eventsToTrack, handleUserActivity, log])

  /**
   * Remove event listeners
   */
  const removeEventListeners = useCallback(() => {
    if (!eventListenersAttachedRef.current) {
      return
    }

    log('Removing activity event listeners')
    
    eventsToTrack.forEach(eventType => {
      document.removeEventListener(eventType, handleUserActivity)
    })
    
    eventListenersAttachedRef.current = false
  }, [eventsToTrack, handleUserActivity, log])

  // Set up event listeners on mount, clean up on unmount
  useEffect(() => {
    attachEventListeners()
    
    // Initial activity trigger
    handleUserActivity()
    
    return () => {
      removeEventListeners()
      
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current)
      }
    }
  }, []) // Empty dependency array to prevent re-initialization

  return {
    // State
    isActive: activityState.isActive,
    lastActivityTime: activityState.lastActivityTime,
    isOrderInProgress: activityState.isOrderInProgress,
    
    // Functions for external use (e.g., with proactive token refresh)
    isUserActive,
    isCriticalOperationInProgress,
    getTimeSinceLastActivity,
    
    // Control functions
    setOrderInProgress,
    triggerActivity,
    
    // Event listener management
    attachEventListeners,
    removeEventListeners
  }
}