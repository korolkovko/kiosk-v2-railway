// sseService.ts
// SSE service for real-time item updates in kiosk
// Updated to handle kopecks from backend

// ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (import section)
// Added tryRefreshToken for token refresh on SSE errors
import { getAccessToken, tryRefreshToken, getRefreshToken } from '../api/apiHttpClient'
// ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END

export interface SSEEvent {
  event_type: 'ITEM_STATUS_CHANGED' | 'ITEM_PROMOTION_CHANGED' | 'ITEM_STOCK_CHANGED' | 'ITEM_CREATED' | 'ITEM_PROPERTIES_CHANGED' | 'ORDER_STATUS_CHANGED' | 'ORDER_EVENT_TRIGGERED' | 'KIOSK_SERVICE_MODE_CHANGED' | 'HEARTBEAT' | 'MEDIA_UPDATE' | 'MENU_ACTIVATED'
  timestamp?: string
}

export interface ItemStatusChangedEvent extends SSEEvent {
  event_type: 'ITEM_STATUS_CHANGED'
  item_id: number
  is_active: boolean
}

export interface ItemPromotionChangedEvent extends SSEEvent {
  event_type: 'ITEM_PROMOTION_CHANGED'
  item_id: number
  promoted: boolean
}

export interface ItemStockChangedEvent extends SSEEvent {
  event_type: 'ITEM_STOCK_CHANGED'
  item_id: number
  stock_quantity: number
  change_quantity: number
  changed_by: string
}

export interface ItemCreatedEvent extends SSEEvent {
  event_type: 'ITEM_CREATED'
  item_id: number
  name_ru: string
  name_eng: string | null
  description_ru: string
  description_eng: string | null
  unit_measure_name_eng: string
  food_category_name: string
  // Price fields now in kopecks from backend
  price_net_kopecks: string
  vat_rate: string | null
  vat_amount_kopecks: string
  price_gross_kopecks: string
  is_active: boolean
  promoted: boolean
  stock_quantity: number
}

export interface ItemPropertiesChangedEvent extends SSEEvent {
  event_type: 'ITEM_PROPERTIES_CHANGED'
  item_id: number
  name_ru: string
  name_eng: string | null
  description_ru: string
  description_eng: string | null
  unit_measure_name_eng: string
  food_category_name: string
  // Price fields now in kopecks from backend
  price_net_kopecks: string
  vat_rate: string | null
  vat_amount_kopecks: string
  price_gross_kopecks: string
}

export interface OrderStatusChangedEvent extends SSEEvent {
  event_type: 'ORDER_STATUS_CHANGED'
  order_id: number
  kiosk_username: string  // Kiosk that created this order (for frontend filtering)
  status: string
  previous_status: string | null
}

export interface OrderEventTriggeredEvent extends SSEEvent {
  event_type: 'ORDER_EVENT_TRIGGERED'
  order_id: number
  kiosk_username: string  // Kiosk that created this order (for frontend filtering)
  fsm_event: string
  fsm_state: string
  previous_state: string | null
  actor_type: string | null
}

export interface KioskServiceModeChangedEvent extends SSEEvent {
  event_type: 'KIOSK_SERVICE_MODE_CHANGED'
  kiosk_username: string
  is_service_mode: boolean
  service_picture_name: string | null
}

export interface HeartbeatEvent extends SSEEvent {
  event_type: 'HEARTBEAT'
}

export interface MediaUpdateEvent extends SSEEvent {
  event_type: 'MEDIA_UPDATE'
  media_type?: string
  media_path?: string
}

export interface MenuActivatedEvent extends SSEEvent {
  event_type: 'MENU_ACTIVATED'
  menu_id?: number
  menu_name?: string
}

export type KioskSSEEvent = ItemStatusChangedEvent | ItemPromotionChangedEvent | ItemStockChangedEvent | ItemCreatedEvent | ItemPropertiesChangedEvent | OrderStatusChangedEvent | OrderEventTriggeredEvent | KioskServiceModeChangedEvent | HeartbeatEvent | MediaUpdateEvent | MenuActivatedEvent

export interface SSEServiceConfig {
  url: string
  reconnectInterval: number
  maxReconnectAttempts: number
}

export class SSEService {
  private eventSource: EventSource | null = null
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private eventHandlers: Map<string, (event: KioskSSEEvent) => void> = new Map()
  private connectionStatusHandlers: Set<(connected: boolean) => void> = new Set()
  // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (connecting flag)
  private isConnecting = false // Prevents race conditions when multiple hooks call connect() simultaneously
  // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END
  // Heartbeat timeout detection (backend sends heartbeat every 15s, we timeout after 20s)
  private lastMessageTime: number | null = null
  private heartbeatCheckInterval: number | null = null
  private readonly HEARTBEAT_TIMEOUT_MS = 20000 // 20 seconds (15s backend interval + 5s buffer)

  // ============================================================================
  // EMERGENCY MODE STATE
  // Purpose: Track when max reconnection attempts reached and show emergency overlay
  // - isEmergencyMode: true when max attempts reached, backend unreachable
  // - emergencyModeHandlers: callbacks to notify UI components (EmergencyOverlay)
  // - After max attempts, switch to slow background polling (60s intervals) forever
  // - Emergency flag persisted to localStorage to survive page refresh
  // ============================================================================
  private isEmergencyMode = false
  private emergencyModeHandlers: Set<(isActive: boolean) => void> = new Set()
  private readonly SLOW_POLL_INTERVAL_MS = 60000 // 60 seconds for background polling
  private readonly EMERGENCY_FLAG_KEY = 'kiosk_emergency_mode'

  constructor(private config: SSEServiceConfig) {}

  /**
   * Persist emergency mode flag to localStorage
   * Survives page refresh, browser crash, computer restart
   */
  private setEmergencyFlag(value: boolean): void {
    if (value) {
      localStorage.setItem(this.EMERGENCY_FLAG_KEY, 'true')
      console.log('💾 SSE: Emergency flag set in localStorage')
    } else {
      localStorage.removeItem(this.EMERGENCY_FLAG_KEY)
      console.log('🧹 SSE: Emergency flag cleared from localStorage')
    }
  }

  /**
   * Check if emergency flag is set in localStorage
   */
  private getEmergencyFlag(): boolean {
    return localStorage.getItem(this.EMERGENCY_FLAG_KEY) === 'true'
  }

  async connect(): Promise<void> {
    // ============================================================================
    // EMERGENCY FLAG CHECK ON PAGE LOAD
    // Check if we were in emergency mode before page refresh
    // If flag exists + refresh token exists → Show emergency immediately, try reconnect
    // If flag exists but no refresh token → Clear stale flag (user logged out)
    // ============================================================================
    const wasInEmergency = this.getEmergencyFlag()
    const hasRefreshToken = getRefreshToken()

    if (wasInEmergency && hasRefreshToken) {
      console.log('🚨 SSE: Emergency flag detected from previous session (page refresh during emergency)')
      console.log('🚨 SSE: Activating emergency mode immediately while attempting reconnection...')
      // Immediately activate emergency mode UI (no 30s wait after page refresh)
      this.setEmergencyMode(true)
      // Continue with normal connect() flow below - will auto-clear flag if connection succeeds
    } else if (wasInEmergency && !hasRefreshToken) {
      // Stale flag - user logged out between sessions
      console.log('🧹 SSE: Clearing stale emergency flag (no refresh token - user logged out)')
      this.setEmergencyFlag(false)
    }

    // Check if already connected or our own connection is in progress
    if (this.eventSource?.readyState === EventSource.OPEN || this.isConnecting) {
      console.log(`⏭️ SSE: Connection already ${this.eventSource?.readyState === EventSource.OPEN ? 'OPEN' : 'IN PROGRESS'}, skipping duplicate connection attempt`)
      return
    }

    // If there is an EventSource that is not OPEN (e.g., CONNECTING or CLOSED), close it proactively
    if (this.eventSource && this.eventSource.readyState !== EventSource.OPEN) {
      try {
        this.eventSource.close()
      } catch (e) {
        console.warn('SSE: Error closing stale EventSource before connect', e)
      }
      this.eventSource = null
    }

    // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (set connecting flag)
    this.isConnecting = true
    // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END

    let token = getAccessToken()
    // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (connect method token check)
    // If no access token, try to refresh it using refresh token from localStorage
    if (!token) {
      console.log('🔄 SSE: No access token found, attempting to refresh...')
      const refreshed = await tryRefreshToken()
      if (refreshed) {
        token = getAccessToken()
        console.log('✅ SSE: Token refreshed, proceeding with connection')
      } else {
        console.error('❌ SSE: No auth token and refresh failed, scheduling reconnect')
        this.isConnecting = false
        // Schedule reconnect with backoff so that future auth (e.g., login) can establish SSE
        this.handleReconnect()
        return
      }
    }
    // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END

    // Final check - token should exist at this point
    if (!token) {
      console.error('❌ SSE: Token is null after refresh attempt, cannot connect')
      this.isConnecting = false
      return
    }

    try {
      // EventSource doesn't support headers, so pass access_token as query parameter
      const urlWithToken = `${this.config.url}?token=${encodeURIComponent(token)}`
      console.log(`🔗 SSE: Attempting connection to: ${urlWithToken}`)
      console.log(`🔑 SSE: Using token: ${token.substring(0, 20)}...`)
      this.eventSource = new EventSource(urlWithToken)

      this.eventSource.onopen = () => {
        console.log('✅ SSE: Connection established')
        this.reconnectAttempts = 0
        // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (clear connecting flag on success)
        this.isConnecting = false
        // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END

        // Exit emergency mode if we were in it (connection restored!)
        if (this.isEmergencyMode) {
          console.log('✅ SSE: Connection restored - exiting emergency mode')
          this.setEmergencyMode(false)
        }

        this.notifyConnectionStatus(true)

        // Start heartbeat monitoring
        this.startHeartbeatMonitoring()
      }

      this.eventSource.onmessage = (event) => {
        // Update last message time (includes heartbeat pings and actual events)
        this.lastMessageTime = Date.now()

        try {
          const data: KioskSSEEvent = JSON.parse(event.data)

          // Skip heartbeat events - they're only for keeping connection alive
          if (data.event_type === 'HEARTBEAT') {
            console.log('💓 SSE: Heartbeat received, connection alive')
            return
          }

          console.log('📨 SSE: Event received:', data.event_type)
          this.handleEvent(data)
        } catch (error) {
          console.error('Failed to parse SSE event:', error, event.data)
        }
      }

      // ============================================================================
      // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (error handler)
      // Purpose: Handle backend restarts by refreshing token before reconnecting
      // Context: When backend restarts, access tokens become invalid (in-memory state lost)
      //          but refresh tokens remain valid (stateless JWT). This tries to refresh
      //          the token before reconnecting. If refresh fails, redirects to login.
      // Date: 2025-10-26
      // To rollback: Replace with simple error handler (see git history)
      // ============================================================================
      this.eventSource.onerror = async (error) => {
        console.error('SSE connection error:', error)
        console.error('SSE readyState:', this.eventSource?.readyState)
        console.error('SSE url:', this.eventSource?.url)

        // Close and nullify the old EventSource immediately to prevent race conditions
        // The browser's auto-retry would keep using the stale URL with old token
        if (this.eventSource) {
          this.eventSource.close()
          this.eventSource = null
          console.log('🔌 SSE: Closed old EventSource instance')
        }

        // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (clear connecting flag on error)
        this.isConnecting = false
        // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END
        this.notifyConnectionStatus(false)

        // Try to refresh token before reconnecting
        // This handles the case where backend restarted and invalidated in-memory access tokens
        console.log('🔄 SSE: Attempting token refresh before reconnecting...')
        const refreshed = await tryRefreshToken()

        if (refreshed) {
          console.log('✅ SSE: Token refreshed successfully, will reconnect with new token')
        } else {
          console.error('❌ SSE: Token refresh failed on connection error - will retry with backoff')
        }

        // Always call handleReconnect() whether refresh succeeded or not
        // This ensures proper backoff delays and emergency mode activation
        this.handleReconnect()
      }
      // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END
      // ============================================================================

    } catch (error) {
      console.error('Failed to create SSE connection:', error)
      // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START (clear connecting flag on exception)
      this.isConnecting = false
      // ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END
      this.handleReconnect()
    }
  }

  disconnect(): void {
    console.log('🔌 SSE: Disconnecting...')

    // Clear emergency mode and flag on explicit disconnect (logout)
    if (this.isEmergencyMode) {
      console.log('🧹 SSE: Clearing emergency mode on disconnect')
      this.setEmergencyMode(false)
    }

    // Stop heartbeat monitoring
    this.stopHeartbeatMonitoring()

    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }

    this.notifyConnectionStatus(false)
  }

  onEvent(eventType: string, handler: (event: KioskSSEEvent) => void): void {
    this.eventHandlers.set(eventType, handler)
  }

  onConnectionStatus(handler: (connected: boolean) => void): void {
    this.connectionStatusHandlers.add(handler)
  }

  // ============================================================================
  // EMERGENCY MODE PUBLIC API
  // Purpose: Allow UI components to subscribe to emergency mode state changes
  // Usage: Call onEmergencyMode() with a callback that receives boolean (true = show overlay)
  // ============================================================================
  onEmergencyMode(handler: (isActive: boolean) => void): void {
    this.emergencyModeHandlers.add(handler)
    // Immediately notify with current state
    handler(this.isEmergencyMode)
  }

  getEmergencyMode(): boolean {
    return this.isEmergencyMode
  }

  private handleEvent(event: KioskSSEEvent): void {
    const handler = this.eventHandlers.get(event.event_type)
    if (handler) {
      handler(event)
    }
  }

  // ============================================================================
  // RECONNECTION LOGIC WITH EMERGENCY MODE
  // Purpose: Aggressive retry for first 4 attempts (~30s), then infinite slow polling
  //
  // Phase 1 (attempts 1-4): Exponential backoff 2s → 4s → 8s → 16s (~30s total)
  // Phase 2 (attempts 5+): Emergency mode + 60s background polling forever
  //
  // When connection restored: Exit emergency mode → return to normal operation
  // ============================================================================
  private handleReconnect(): void {
    // Don't schedule a new reconnection if one is already pending
    if (this.reconnectTimer !== null) {
      console.log('⏭️ SSE: Reconnection already scheduled, skipping duplicate')
      return
    }

    this.reconnectAttempts++

    // Check if we've exceeded max attempts and should enter emergency mode
    if (this.reconnectAttempts > this.config.maxReconnectAttempts) {
      // Enter emergency mode (first time only)
      if (!this.isEmergencyMode) {
        console.error('🚨 SSE: Max reconnection attempts reached - entering EMERGENCY MODE')
        this.setEmergencyMode(true)
      }

      // Continue trying forever with slow polling (60s intervals)
      const delay = this.SLOW_POLL_INTERVAL_MS
      console.log(`🚨 SSE: Emergency mode - background polling in ${delay / 1000}s (attempt ${this.reconnectAttempts})`)

      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null
        this.connect()
      }, delay)
      return
    }

    // Phase 1: Aggressive exponential backoff (attempts 1-5)
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    console.log(`🔄 SSE: Attempting reconnection in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`)

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  private setEmergencyMode(isActive: boolean): void {
    if (this.isEmergencyMode === isActive) return

    this.isEmergencyMode = isActive
    console.log(`🚨 SSE: Emergency mode ${isActive ? 'ACTIVATED' : 'DEACTIVATED'}`)

    // Persist flag to localStorage to survive page refresh
    this.setEmergencyFlag(isActive)

    // Notify all subscribers (EmergencyOverlay component)
    this.emergencyModeHandlers.forEach(handler => handler(isActive))
  }

  private notifyConnectionStatus(connected: boolean): void {
    this.connectionStatusHandlers.forEach(handler => handler(connected))
  }

  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN
  }

  private startHeartbeatMonitoring(): void {
    // Stop any existing monitoring
    this.stopHeartbeatMonitoring()

    // Initialize last message time
    this.lastMessageTime = Date.now()

    // Check for heartbeat timeout every 5 seconds
    this.heartbeatCheckInterval = window.setInterval(() => {
      if (!this.lastMessageTime) return

      const timeSinceLastMessage = Date.now() - this.lastMessageTime
      console.log(`💓 SSE: Heartbeat check - ${timeSinceLastMessage}ms since last message (timeout: ${this.HEARTBEAT_TIMEOUT_MS}ms)`)

      if (timeSinceLastMessage > this.HEARTBEAT_TIMEOUT_MS) {
        console.error(`💔 SSE: Heartbeat timeout detected (${timeSinceLastMessage}ms since last message)`)
        console.error('💔 SSE: Connection appears dead, forcing reconnection...')

        // Stop monitoring before reconnecting
        this.stopHeartbeatMonitoring()

        // Manually trigger the reconnection logic
        this.handleConnectionFailure()
      }
    }, 5000) // Check every 5 seconds

    console.log('💓 SSE: Heartbeat monitoring started (timeout: 20s)')
  }

  private stopHeartbeatMonitoring(): void {
    if (this.heartbeatCheckInterval) {
      window.clearInterval(this.heartbeatCheckInterval)
      this.heartbeatCheckInterval = null
      this.lastMessageTime = null
      console.log('💔 SSE: Heartbeat monitoring stopped')
    }
  }

  private async handleConnectionFailure(): Promise<void> {
    console.log('🔄 SSE: Handling connection failure...')

    // Close and nullify the old EventSource
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
      console.log('🔌 SSE: Closed dead EventSource instance')
    }

    this.isConnecting = false
    this.notifyConnectionStatus(false)

    // Try to refresh token before reconnecting
    console.log('🔄 SSE: Attempting token refresh before reconnecting...')
    const refreshed = await tryRefreshToken()

    if (refreshed) {
      console.log('✅ SSE: Token refreshed successfully, will reconnect with new token')
    } else {
      console.error('❌ SSE: Token refresh failed during heartbeat timeout - will retry with backoff')
    }

    // Always call handleReconnect() whether refresh succeeded or not
    // This ensures proper backoff delays and emergency mode activation
    this.handleReconnect()
  }
}

// Global SSE service instance
export const sseService = new SSEService({
  url: '/api/kiosk/events', // Vite proxy will rewrite /api -> /api/v1
  reconnectInterval: 3000,
  maxReconnectAttempts: 3 // Emergency mode triggers after ~34 seconds (20s heartbeat + 2s+4s+8s = 34s)
})