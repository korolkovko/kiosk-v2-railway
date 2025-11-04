import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { CategoriesProvider } from './contexts/CategoriesContext'
import { ItemsProvider } from './contexts/ItemsContext'
import { OrderProvider } from './contexts/OrderContext'
import { Login } from './pages/Login'
import MainScreen from './pages/MainScreen'
import OrderHandlingPage from './pages/OrderHandlingPage'
import { RouteGuard } from './components/RouteGuard'
import ServiceModePage from './pages/ServiceModePage'
import ServiceModeEventBridge from './components/ServiceModeEventBridge'
import EmergencyModeEventBridge from './components/EmergencyModeEventBridge'
import MenuRefreshEventBridge from './components/MenuRefreshEventBridge'
import MediaUpdateEventBridge from './components/MediaUpdateEventBridge'
import EmergencyOverlay from './components/EmergencyOverlay'
import { useSSEEmergency } from './SSESubscription/useSSEEmergency'

function App() {
  const location = useLocation()

  // Subscribe to SSE emergency mode (backend connection lost)
  const { isEmergencyMode } = useSSEEmergency()

  // Never show emergency on login page - it's the recovery path
  const isLoginPage = location.pathname === '/login'
  const shouldShowEmergency = isEmergencyMode && !isLoginPage

  return (
    <AuthProvider>
      <CategoriesProvider>
        <ItemsProvider>
          <OrderProvider>
            {/* Bridge SSE service mode events to UI actions globally */}
            <ServiceModeEventBridge />
            {/* Bridge SSE emergency mode events to UI actions globally */}
            <EmergencyModeEventBridge />
            {/* Bridge SSE menu activation events to UI actions globally */}
            <MenuRefreshEventBridge />
            {/* Bridge SSE media update events to silent background updates globally */}
            <MediaUpdateEventBridge />
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/main"
                element={
                  <RouteGuard>
                    <MainScreen />
                  </RouteGuard>
                }
              />
              <Route
                path="/order-handling"
                element={
                  <RouteGuard>
                    <OrderHandlingPage />
                  </RouteGuard>
                }
              />
              <Route
                path="/service-mode"
                element={
                  <RouteGuard>
                    <ServiceModePage />
                  </RouteGuard>
                }
              />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>

            {/* Emergency overlay - shows when backend connection lost after max reconnection attempts */}
            {/* Blocks all user input and displays "Something went wrong" or emergency picture from cache */}
            {/* Auto-dismisses when SSE connection restored */}
            {/* NEVER shows on login page - login is the recovery path */}
            <EmergencyOverlay isVisible={shouldShowEmergency} />
          </OrderProvider>
        </ItemsProvider>
      </CategoriesProvider>
    </AuthProvider>
  )
}

export default App