/**
 * RouteGuard guards application routes requiring authentication.
 * Waits for auth initialization (refresh attempt) before making decisions.
 * If the user is not authenticated after initialization, redirects to the login page.
 * If service mode is active, redirects to /service-mode to prevent bypassing the overlay.
 * If order processing is active, redirects to /order-handling to prevent bypassing (except /login for recovery).
 */
import React, { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useServiceModeStore } from '../stores/ServiceModeStore'
import { useNavigationStore } from '../stores/navigationStore'

interface RouteGuardProps {
  children: ReactNode
}

export const RouteGuard: React.FC<RouteGuardProps> = ({ children }) => {
  const { isAuthenticated, isInitialized } = useAuth()
  const location = useLocation()
  const { isActive: isServiceModeActive } = useServiceModeStore()
  const { navigationMode } = useNavigationStore()

  // Wait for auth initialization to complete (refresh attempt)
  if (!isInitialized) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
      </div>
    )
  }

  // If not authenticated after initialization, send user to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // If service mode is active and user tries to navigate away from /service-mode,
  // redirect them back to /service-mode to prevent bypassing the overlay
  if (isServiceModeActive && location.pathname !== '/service-mode') {
    console.log('🛠️ RouteGuard: Service mode active, redirecting to /service-mode')
    return <Navigate to="/service-mode" replace />
  }

  // If order processing is active and user tries to navigate away from /order-handling,
  // redirect them back to /order-handling (except /login - that's the recovery path for token expiry)
  // beforeunload warning in OrderHandlingPage will show warning before they navigate to /login
  if (navigationMode === 'order_processing' &&
      location.pathname !== '/order-handling' &&
      location.pathname !== '/login') {
    console.log('🛡️ RouteGuard: Order processing active, redirecting to /order-handling')
    return <Navigate to="/order-handling" replace />
  }

  // If authenticated, render children
  return <>{children}</>
}

export default RouteGuard
