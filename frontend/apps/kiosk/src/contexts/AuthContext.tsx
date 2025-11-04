// File: src/contexts/AuthContext.tsx
//
// Purpose:
// Authentication context exposing minimal auth state and operations for UI.
// Delegates all business logic to services (DTO→Domain→ViewModel mapping, storage, tokens).
// Includes proactive token refresh with smart timing to provide Amazon-like seamless experience.

import { createContext, useState, useContext, ReactNode, useEffect } from 'react'

// Transport-layer request type for login
import type { LoginRequestDto } from '../models/dto/auth.dto'

// View-layer model for user
import type { UserVM } from '../models/view/auth.vm'

// Orchestration service (business logic)
import {
  loginWithPassword,
  logoutAndClearSession,
  getPersistedSessionVM,
  refreshAccessTokenAndGetSessionVM,
} from '../services/auth.service'

// Media cache service
import { mediaCacheService } from '../services/mediaCache.service'

// HTTP client utilities
import { getRefreshToken } from '../api/apiHttpClient'

 // Proactive token refresh and user activity detection
import { useProactiveTokenRefresh } from '../hooks/useProactiveTokenRefresh'
import { useUserActivityDetection } from '../hooks/useUserActivityDetection'
import { sseService } from '../SSESubscription/sseService'


interface AuthContextType {
  user: UserVM | null
  isAuthenticated: boolean
  isInitialized: boolean
  login: (credentials: LoginRequestDto) => Promise<void>
  logout: () => Promise<void>
  onCategoriesFetch?: (fetchCategories: () => Promise<void>) => void
  setOrderInProgress: (inProgress: boolean) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  // Initialize from persisted session (if available and not expired)
  const initialUser = getPersistedSessionVM()?.user ?? null
  const [user, setUser] = useState<UserVM | null>(initialUser)
  const [isInitialized, setIsInitialized] = useState(false)
  
  // Categories fetch callback - will be set by CategoriesProvider
  const [categoriesFetchCallback, setCategoriesFetchCallback] = useState<(() => Promise<void>) | null>(null)

  // User activity detection for smart token refresh timing
  const {
    isUserActive,
    isCriticalOperationInProgress,
    setOrderInProgress
  } = useUserActivityDetection({
    debug: false // Disable debug to prevent console spam
  })

  // Proactive token refresh with smart timing
  useProactiveTokenRefresh({
    refreshInterval: 45 * 60 * 1000, // 45 minutes
    isUserActive,
    isCriticalOperationInProgress,
    onRefreshSuccess: () => {
      console.log('🔄 Background token refresh successful')
    },
    onRefreshFailure: (error) => {
      console.warn('⚠️ Background token refresh failed:', error.message)
      // Note: Don't force logout here - let the user continue until they make a request
      // The existing 401 handling in fetchWithAuth will handle expired tokens gracefully
    },
    debug: false // Disable debug to prevent console spam
  })

  /**
   * Initialize authentication on mount
   * Try to refresh access token if refresh token exists in storage
   */
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to refresh the session using stored refresh token
        const sessionVM = await refreshAccessTokenAndGetSessionVM()
        if (sessionVM) {
          setUser(sessionVM.user)
          console.log('🔐 AuthContext: Session refreshed, initiating SSE connection...')
          // Ensure SSE connected after auth init refresh
          try { void sseService.connect() } catch (e) { console.warn('Auth initialization: SSE connect failed', e) }
        }
      } catch (error) {
        // Refresh failed - could be network error (server down) or expired token
        console.log('Auth initialization: refresh not available or expired')

        // IMPORTANT: Still attempt SSE connection even if refresh failed
        // This handles the case where:
        // 1. Page refresh happens while server is down
        // 2. Refresh token is valid but backend unreachable (status 500)
        // 3. SSE will handle reconnection with backoff and trigger emergency mode
        const refreshToken = getRefreshToken()
        if (refreshToken) {
          console.log('🔐 AuthContext: Refresh token exists, attempting SSE connection despite refresh failure...')
          try { void sseService.connect() } catch (e) { console.warn('Auth initialization: SSE connect failed', e) }
        }
      } finally {
        setIsInitialized(true)
      }
    }

    initAuth()
  }, [])

  /**
   * login()
   * Authenticate with credentials via service, persist session, update UI state,
   * and trigger categories fetching.
   */
  const login = async (credentials: LoginRequestDto) => {
    const sessionVM = await loginWithPassword(credentials)
    setUser(sessionVM.user)
    console.log('🔐 AuthContext: Login successful, initiating SSE connection...')
    // Ensure SSE connected after explicit login
    try { void sseService.connect() } catch (e) { console.warn('Login: SSE connect failed', e) }
    
    // Trigger categories fetching after successful login
    if (categoriesFetchCallback) {
      try {
        await categoriesFetchCallback()
      } catch (error) {
        // Log error but don't fail login process
        console.warn('Failed to fetch categories after login:', error)
      }
    }
  }

  /**
   * logout()
   * Call service to logout, clear media cache, and clear local auth state.
   */
  const logout = async () => {
    try {
      // Clear auth session
      await logoutAndClearSession()

      // Clear media cache from IndexedDB
      console.log('🧹 Clearing media cache on logout...')
      await mediaCacheService.clearAll()
    } finally {
      // Ensure SSE disconnected on logout
      try { sseService.disconnect() } catch (e) { console.warn('Logout: SSE disconnect failed', e) }
      setUser(null)
    }
  }

  /**
   * onCategoriesFetch()
   * Callback to register categories fetch function from CategoriesProvider
   */
  const onCategoriesFetch = (fetchCategories: () => Promise<void>) => {
    setCategoriesFetchCallback(() => fetchCategories)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isInitialized,
        login,
        logout,
        onCategoriesFetch,
        setOrderInProgress,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
