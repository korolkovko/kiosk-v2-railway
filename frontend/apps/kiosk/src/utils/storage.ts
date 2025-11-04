// src/utils/storage.ts

const SESSION_KEY = 'kiosk_app_session'

export interface SessionData<T = any> {
  data: T
  expiresAt: number
}

/**
 * Save session data in localStorage using Base64 encoding.
 * data: arbitrary object (e.g., { accessToken, user, expiresIn })
 * expiresIn: seconds until expiration
 */
export function saveSession<T>(data: T, expiresIn: number): void {
  const session: SessionData<T> = {
    data,
    expiresAt: Date.now() + expiresIn * 1000,
  }
  const json = JSON.stringify(session)
  const encoded = btoa(json)
  localStorage.setItem(SESSION_KEY, encoded)
}

/**
 * Load session data from localStorage if not expired.
 * Returns data or null if missing/expired/corrupt.
 */
export function loadSession<T>(): T | null {
  const encoded = localStorage.getItem(SESSION_KEY)
  if (!encoded) return null
  try {
    const json = atob(encoded)
    const session: SessionData<T> = JSON.parse(json)
    if (Date.now() > session.expiresAt) {
      clearSession()
      return null
    }
    return session.data
  } catch {
    clearSession()
    return null
  }
}

/** Clear stored session data */
export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY)
}
