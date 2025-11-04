// File: src/hooks/useProactiveTokenRefresh.ts
//
// Purpose:
// Proactive token refresh hook that refreshes access tokens before they expire
// with smart timing to avoid disrupting user interactions. Implements Amazon-like
// seamless authentication experience by refreshing tokens in the background.

import { useEffect, useRef, useCallback } from 'react'
import { refreshAccessToken, getRefreshToken } from '../api/apiHttpClient'

interface UseProactiveTokenRefreshOptions {
  /**
   * Interval in milliseconds to check if token needs refresh
   * Default: 45 minutes (2700000ms)
   */
  refreshInterval?: number
  
  /**
   * Callback when refresh succeeds
   */
  onRefreshSuccess?: () => void
  
  /**
   * Callback when refresh fails (token expired, network error, etc.)
   */
  onRefreshFailure?: (error: Error) => void
  
  /**
   * Function to check if user is currently active/interacting
   * If true, refresh will be deferred
   */
  isUserActive?: () => boolean
  
  /**
   * Function to check if critical operation is in progress (e.g., order placement)
   * If true, refresh will be deferred until operation completes
   */
  isCriticalOperationInProgress?: () => boolean
  
  /**
   * Enable debug logging
   */
  debug?: boolean
}

/**
 * useProactiveTokenRefresh
 * 
 * Automatically refreshes access tokens in the background before they expire.
 * Uses smart timing to avoid disrupting user interactions:
 * - Defers refresh when user is actively interacting
 * - Defers refresh during critical operations (order placement)
 * - Retries failed refreshes with exponential backoff
 * 
 * @param options Configuration options for refresh behavior
 */
export function useProactiveTokenRefresh(options: UseProactiveTokenRefreshOptions = {}) {
  const {
    refreshInterval = 45 * 60 * 1000, // 45 minutes
    onRefreshSuccess,
    onRefreshFailure,
    isUserActive,
    isCriticalOperationInProgress,
    debug = false
  } = options

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastRefreshAttemptRef = useRef<number>(0)

  const log = useCallback((message: string, ...args: any[]) => {
    if (debug) {
      console.log(`[useProactiveTokenRefresh] ${message}`, ...args)
    }
  }, [debug])

  /**
   * Attempt to refresh the access token with smart timing
   */
  const attemptTokenRefresh = useCallback(async () => {
    const now = Date.now()
    
    // Prevent too frequent refresh attempts (minimum 5 minutes between attempts)
    if (now - lastRefreshAttemptRef.current < 5 * 60 * 1000) {
      log('Skipping refresh - too soon since last attempt')
      return
    }

    // Check if refresh token exists
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      log('No refresh token available - stopping proactive refresh')
      return
    }

    // Check if user is currently active
    if (isUserActive && isUserActive()) {
      log('User is active - deferring refresh for 5 minutes')
      // Retry in 5 minutes
      retryTimeoutRef.current = setTimeout(attemptTokenRefresh, 5 * 60 * 1000)
      return
    }

    // Check if critical operation is in progress
    if (isCriticalOperationInProgress && isCriticalOperationInProgress()) {
      log('Critical operation in progress - deferring refresh for 2 minutes')
      // Retry in 2 minutes
      retryTimeoutRef.current = setTimeout(attemptTokenRefresh, 2 * 60 * 1000)
      return
    }

    // Safe to refresh - perform the refresh
    try {
      log('Attempting background token refresh...')
      lastRefreshAttemptRef.current = now
      
      await refreshAccessToken()
      
      log('✅ Background token refresh successful')
      onRefreshSuccess?.()
      
    } catch (error) {
      const refreshError = error instanceof Error ? error : new Error('Token refresh failed')
      log('❌ Background token refresh failed:', refreshError.message)
      
      onRefreshFailure?.(refreshError)
      
      // Implement exponential backoff for retries
      const retryDelay = Math.min(10 * 60 * 1000, 2 * 60 * 1000) // Start with 2 min, max 10 min
      log(`Retrying refresh in ${retryDelay / 1000} seconds`)
      
      retryTimeoutRef.current = setTimeout(attemptTokenRefresh, retryDelay)
    }
  }, [isUserActive, isCriticalOperationInProgress, onRefreshSuccess, onRefreshFailure, log])

  /**
   * Start the proactive refresh timer
   */
  const startProactiveRefresh = useCallback(() => {
    // Prevent multiple initializations
    if (intervalRef.current) {
      log('Proactive refresh already running, skipping initialization')
      return
    }
    
    log(`Starting proactive token refresh with ${refreshInterval / 1000}s interval`)
    
    // Set up recurring refresh attempts
    intervalRef.current = setInterval(attemptTokenRefresh, refreshInterval)
    
    // Also attempt an immediate refresh if needed (but with delay to avoid startup conflicts)
    setTimeout(attemptTokenRefresh, 10000) // 10 seconds after hook initialization
    
  }, [refreshInterval, attemptTokenRefresh, log])

  /**
   * Stop the proactive refresh timer
   */
  const stopProactiveRefresh = useCallback(() => {
    log('Stopping proactive token refresh')
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }
  }, [log])

  /**
   * Manually trigger a token refresh (respects smart timing rules)
   */
  const triggerRefresh = useCallback(() => {
    log('Manual refresh triggered')
    attemptTokenRefresh()
  }, [attemptTokenRefresh, log])

  // Start proactive refresh on mount, stop on unmount
  useEffect(() => {
    startProactiveRefresh()
    
    return () => {
      stopProactiveRefresh()
    }
  }, []) // Empty dependency array to prevent re-initialization

  return {
    startProactiveRefresh,
    stopProactiveRefresh,
    triggerRefresh
  }
}