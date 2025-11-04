// ServiceModeStore.ts
//
// Purpose:
// Zustand store for Kiosk Service Mode state.
// Tracks activation, target media name, and pending-activation while an order is gracefully finishing.
// UI blocking is performed by the overlay component; SSE and other data updates keep running under the hood.
//
// Persistence:
// Service mode state is persisted to localStorage to survive page refresh.
// This prevents users from bypassing service mode by refreshing or manually navigating.

import { create } from 'zustand'

// localStorage key for persisting service mode state
const SERVICE_MODE_STORAGE_KEY = 'kiosk_service_mode_state'

export interface ServiceModeState {
  // True when service mode is active and UI must be blocked
  isActive: boolean
  // Logical media name to display for service mode (without extension), e.g., "maintenance"
  pictureName: string | null
  // True when activation arrived during order processing; activation deferred until terminal state after countdown
  isPendingActivation: boolean
}

export interface ServiceModeActions {
  /**
   * Activate service mode immediately.
   * - Sets isActive true and stores pictureName
   * - Clears pending flag
   */
  activate: (pictureName: string | null) => void

  /**
   * Deactivate service mode.
   * - Sets isActive false
   * - Clears pictureName and pending flag
   */
  deactivate: () => void

  /**
   * Set pending activation. Used when service mode activation arrives while order is processing.
   * - Stores intended pictureName and sets isPendingActivation
   */
  setPendingActivation: (pictureName: string | null) => void

  /**
   * Clear pending activation flag (e.g., if canceled or after activation applied).
   */
  clearPendingActivation: () => void
}

type ServiceModeStore = ServiceModeState & ServiceModeActions

const initialState: ServiceModeState = {
  isActive: false,
  pictureName: null,
  isPendingActivation: false
}

/**
 * Load persisted service mode state from localStorage
 * Returns initialState if nothing persisted or parse fails
 */
function loadPersistedState(): ServiceModeState {
  try {
    const stored = localStorage.getItem(SERVICE_MODE_STORAGE_KEY)
    if (!stored) {
      return initialState
    }
    const parsed = JSON.parse(stored) as ServiceModeState
    console.log('🛠️ ServiceModeStore: Loaded persisted state:', parsed)
    return parsed
  } catch (error) {
    console.warn('🛠️ ServiceModeStore: Failed to load persisted state, using initial state:', error)
    return initialState
  }
}

/**
 * Save service mode state to localStorage
 */
function saveState(state: ServiceModeState): void {
  try {
    localStorage.setItem(SERVICE_MODE_STORAGE_KEY, JSON.stringify(state))
    console.log('🛠️ ServiceModeStore: State persisted:', state)
  } catch (error) {
    console.warn('🛠️ ServiceModeStore: Failed to persist state:', error)
  }
}

/**
 * Clear persisted service mode state from localStorage
 */
function clearPersistedState(): void {
  try {
    localStorage.removeItem(SERVICE_MODE_STORAGE_KEY)
    console.log('🛠️ ServiceModeStore: Persisted state cleared')
  } catch (error) {
    console.warn('🛠️ ServiceModeStore: Failed to clear persisted state:', error)
  }
}

/**
 * useServiceModeStore
 * Global state for service mode. Only UI input should be blocked; data flows (SSE, contexts) continue.
 * State is persisted to localStorage to survive page refresh.
 */
export const useServiceModeStore = create<ServiceModeStore>((set) => ({
  // Load initial state from localStorage (if persisted)
  ...loadPersistedState(),

  activate: (pictureName) => {
    const newState = {
      isActive: true,
      pictureName,
      isPendingActivation: false
    }
    set(newState)
    saveState(newState)
    console.log('🛠️ ServiceModeStore.activate:', { pictureName })
  },

  deactivate: () => {
    const newState = {
      isActive: false,
      pictureName: null,
      isPendingActivation: false
    }
    set(newState)
    clearPersistedState()
    console.log('🛠️ ServiceModeStore.deactivate')
  },

  setPendingActivation: (pictureName) => {
    set((state) => {
      const newState = {
        ...state,
        isPendingActivation: true,
        pictureName
      }
      saveState(newState)
      return newState
    })
    console.log('🛠️ ServiceModeStore.setPendingActivation:', { pictureName })
  },

  clearPendingActivation: () => {
    set((state) => {
      const newState = {
        ...state,
        isPendingActivation: false
      }
      saveState(newState)
      return newState
    })
    console.log('🛠️ ServiceModeStore.clearPendingActivation')
  }
}))