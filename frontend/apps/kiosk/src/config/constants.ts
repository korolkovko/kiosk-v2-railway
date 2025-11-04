// File: src/config/constants.ts
//
// Purpose:
// Central configuration constants for the kiosk application.

/**
 * API Base URL
 *
 * Development (Vite proxy):
 *   - Uses /api which is proxied to localhost:8000/api/v1
 *   - Set VITE_API_URL in .env to override
 *
 * Production (Railway):
 *   - Must be full Backend URL: https://kiosk-backend.railway.app/api/v1
 *   - Set via VITE_API_URL environment variable at build time
 *
 * Docker Compose Production:
 *   - Uses /api (Nginx proxies to backend:8000/api/v1)
 *   - Leave VITE_API_URL empty or set to '/api'
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Kiosk-specific endpoints
 * Note: API_BASE_URL already includes /api, so endpoints just need the path after that
 * /api + /kiosk/login → /api/kiosk/login → proxied to /api/v1/kiosk/login
 */
export const KIOSK_AUTH_LOGIN = '/kiosk/login'
export const KIOSK_AUTH_REFRESH = '/kiosk/refresh'
export const KIOSK_AUTH_LOGOUT = '/kiosk/logout'

/**
 * Kiosk menu endpoints
 */
export const KIOSK_ITEMS_AVAILABLE = '/kiosk/items/available'
export const KIOSK_CATEGORIES = '/kiosk/categories'
export const KIOSK_MENU_ALL_FOR_PRELOAD = '/kiosk/menu/all-for-preload'

/**
 * Menu management endpoints
 */
export const MENU_ACTIVATION_STATUS = '/v1/menu-management/activation-status'

/**
 * Service mode endpoints
 */
export const KIOSK_SERVICE_MODE_STATUS_SELF = '/kiosk/service-mode/kiosk-status-for-kiosk-user'
