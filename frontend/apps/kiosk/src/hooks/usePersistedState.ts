// File: src/hooks/usePersistedState.ts
//
// Purpose:
// Generic hook for persisting React state to browser storage (localStorage/sessionStorage)
// with TTL (time-to-live) expiration support for cache invalidation.
// Used for items and categories to survive page reloads.

import { useState, useEffect, useCallback, Dispatch, SetStateAction } from 'react'

interface PersistedData<T> {
  data: T
  timestamp: number
  ttl: number // milliseconds
}

export interface UsePersistedStateOptions {
  /**
   * Storage type to use
   * - localStorage: Persists across browser sessions (survives tab close)
   * - sessionStorage: Persists only during browser session (cleared on tab close)
   */
  storage: 'localStorage' | 'sessionStorage'

  /**
   * Time-to-live in milliseconds
   * After this duration, cached data is considered stale and won't be loaded
   */
  ttl: number

  /**
   * Enable debug logging
   */
  debug?: boolean
}

/**
 * usePersistedState
 *
 * React state hook with automatic persistence to browser storage.
 * Includes TTL-based cache invalidation.
 *
 * @param key - Unique storage key (should be namespaced, e.g., 'kiosk_items')
 * @param initialValue - Initial value if no cached data exists
 * @param options - Storage configuration (storage type, TTL, debug)
 *
 * @example
 * const [items, setItems] = usePersistedState('kiosk_items', [], {
 *   storage: 'sessionStorage',
 *   ttl: 3600000, // 1 hour
 *   debug: true
 * })
 */
export function usePersistedState<T>(
  key: string,
  initialValue: T,
  options: UsePersistedStateOptions
): [T, Dispatch<SetStateAction<T>>, () => void] {
  const { storage: storageType, ttl, debug = false } = options

  const storage = storageType === 'localStorage' ? localStorage : sessionStorage

  const log = (message: string, ...args: any[]) => {
    if (debug) {
      console.log(`[usePersistedState:${key}] ${message}`, ...args)
    }
  }

  /**
   * Initialize state from storage or use initial value
   */
  const [state, setState] = useState<T>(() => {
    try {
      const cached = storage.getItem(key)

      if (!cached) {
        log('No cached data found, using initial value')
        return initialValue
      }

      const parsed: PersistedData<T> = JSON.parse(cached)
      const now = Date.now()
      const age = now - parsed.timestamp

      // Check if data is still valid (within TTL)
      if (age > parsed.ttl) {
        log(`Cached data expired (age: ${age}ms, TTL: ${parsed.ttl}ms), using initial value`)
        storage.removeItem(key) // Cleanup expired data
        return initialValue
      }

      log(`Loaded cached data (age: ${age}ms, TTL: ${parsed.ttl}ms)`)
      return parsed.data

    } catch (error) {
      log('Error loading cached data, using initial value:', error)
      storage.removeItem(key) // Cleanup corrupted data
      return initialValue
    }
  })

  /**
   * Persist state to storage whenever it changes
   */
  useEffect(() => {
    try {
      const dataToStore: PersistedData<T> = {
        data: state,
        timestamp: Date.now(),
        ttl
      }

      storage.setItem(key, JSON.stringify(dataToStore))
      log('State persisted to storage')

    } catch (error) {
      // Storage quota exceeded or other errors
      console.error(`[usePersistedState:${key}] Failed to persist state:`, error)

      // Try to clear old data to make space
      try {
        storage.removeItem(key)
      } catch (cleanupError) {
        // Ignore cleanup errors
      }
    }
  }, [state, key, ttl, storage])

  /**
   * Clear cached data from storage
   */
  const clearCache = useCallback(() => {
    try {
      storage.removeItem(key)
      log('Cache cleared')
    } catch (error) {
      console.error(`[usePersistedState:${key}] Failed to clear cache:`, error)
    }
  }, [key, storage])

  return [state, setState, clearCache]
}

/**
 * Predefined configurations for common use cases
 */
export const PERSISTENCE_CONFIGS = {
  /**
   * Items: localStorage, 4 hour TTL
   * Consistent with categories and refresh tokens for full Amazon-like persistence
   * Survives browser close/open scenarios, real-time updates via SSE keep data fresh
   */
  ITEMS: {
    storage: 'localStorage' as const,
    ttl: 14400000, // 4 hours
    debug: true
  },

  /**
   * Categories: localStorage, 24 hour TTL
   * Categories change rarely, longer TTL for better performance
   */
  CATEGORIES: {
    storage: 'localStorage' as const,
    ttl: 86400000, // 24 hours
    debug: true
  },

  /**
   * Cart: sessionStorage, 1 hour TTL
   * Cart is session-specific but survives reload
   */
  CART: {
    storage: 'sessionStorage' as const,
    ttl: 3600000, // 1 hour
    debug: true
  }
} as const
