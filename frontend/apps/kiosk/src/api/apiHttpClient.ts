// File: src/api/apiHttpClient.ts
//
// Purpose:
// Centralized HTTP client for all API transport.
// Responsibilities:
// - Base URL prefixing and credentials
// - Bearer access token injection
// - 401 Unauthorized handling with refresh + retry
// - Standardized ApiError classification and response parsing
// - In-memory accessToken management

import type { RefreshResponseDto } from '../models/dto/auth.dto'
import { API_BASE_URL, KIOSK_AUTH_REFRESH } from '../config/constants'

/**
 * Authentication token management
 * Access token is stored in memory for security
 * Refresh token is stored in localStorage (persists across browser sessions for Amazon-like experience)
 */
let accessToken: string | null = null;

const REFRESH_TOKEN_KEY = 'kiosk_refresh_token';

export function setAccessToken(token: string) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setRefreshToken(token: string) {
  try {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to save refresh token:', e);
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    console.error('Failed to load refresh token:', e);
    return null;
  }
}

export function clearRefreshToken() {
  try {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    console.error('Failed to clear refresh token:', e);
  }
}

/**
 * Error class for API request errors
 */
export class ApiError extends Error {
  status?: number;
  type: 'network' | 'unauthorized' | 'server' | 'unknown';

  constructor(message: string, type: 'network' | 'unauthorized' | 'server' | 'unknown', status?: number) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.status = status;
  }
}

/**
 * Refresh the access token using stored refresh token
 */
export async function refreshAccessToken(): Promise<void> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    throw new ApiError('No refresh token available. Please log in again.', 'unauthorized', 401);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${KIOSK_AUTH_REFRESH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: "include"
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = null;
      }

      if (response.status === 401) {
        // Refresh token is invalid/expired - clear tokens and force re-login
        clearAccessToken();
        clearRefreshToken();
        throw new ApiError('Session expired. Please log in again.', 'unauthorized', response.status);
      } else {
        throw new ApiError(
          errorData?.detail || 'Failed to refresh token',
          'unknown',
          response.status
        );
      }
    }

    const data: RefreshResponseDto = await response.json();
    accessToken = data.access_token;
    // Also update refresh token as backend returns new one
    if (data.refresh_token) {
      setRefreshToken(data.refresh_token);
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Could not connect to server for token refresh', 'network');
  }
}

/**
 * Extended fetch options with authentication retry
 */
interface FetchOptions extends RequestInit {
  retryOnUnauthenticated?: boolean;
}

/**
 * Main fetch function for all API calls
 * Handles authentication, token refresh, and standardized error handling
 *
 * @param endpoint The API endpoint (relative path without base URL)
 * @param init Fetch options
 * @returns Response object
 */
export async function fetchWithAuth(
  endpoint: RequestInfo,
  init: FetchOptions = {}
): Promise<Response> {
  // Always use the API_BASE_URL for consistency
  // This ensures we're always using the proxy configuration
  const url = typeof endpoint === "string"
    ? `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
    : endpoint;

  console.log('🌐 fetchWithAuth: Calling', url, 'method:', init.method || 'GET');

  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
    console.log('🔑 fetchWithAuth: Using access token');
  }

  try {
    const response = await fetch(url, {
      ...init,
      headers,
      credentials: "include"
    });

    console.log('📡 fetchWithAuth: Response status', response.status, 'for', url);

    // Handle 403 Forbidden (wrong role/permissions) - no retry, clear tokens
    if (response.status === 403) {
      clearAccessToken();
      clearRefreshToken();
      throw new ApiError(
        'Access denied. Please log in with proper credentials.',
        'unauthorized',
        403
      );
    }

    // Handle 401 Unauthorized by refreshing token and retrying
    if (response.status === 401 && init.retryOnUnauthenticated !== false) {
      try {
        await refreshAccessToken();
        // Retry the original request with new access token
        headers.set("Authorization", `Bearer ${accessToken}`);
        return fetchWithAuth(endpoint, { ...init, retryOnUnauthenticated: false });
      } catch (refreshError) {
        // If refresh fails, clear tokens and force login
        clearAccessToken();
        clearRefreshToken();
        throw refreshError;
      }
    }

    return response;
  } catch (error) {
    // Preserve ApiError raised upstream (e.g., refreshAccessToken or handleApiResponse)
    if (error instanceof ApiError) {
      throw error;
    }
    // Handle actual network errors (fetch failures, CORS, DNS, etc.)
    console.error(`Network error for ${url}:`, error);
    throw new ApiError(
      'Could not connect to server. Please check your internet connection and try again.',
      'network'
    );
  }
}

// ============================================================================
// ROLLBACK_MARKER: SSE_TOKEN_REFRESH_START
// Purpose: Simplified token refresh for SSE error handling
// Context: When backend restarts, SSE connections fail with 401. This function
//          allows SSE service to attempt token refresh without full error handling.
// Date: 2025-10-26
// To rollback: Remove this function and revert sseService.ts onerror handler
// ============================================================================
/**
 * Attempt to refresh access token (for SSE error recovery)
 *
 * Unlike refreshAccessToken(), this version:
 * - Returns boolean success/failure instead of throwing
 * - Used by SSE service to recover from backend restarts
 * - Minimal error handling for silent background refresh
 *
 * @returns true if token refreshed successfully, false otherwise
 */
export async function tryRefreshToken(): Promise<boolean> {
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      console.log('🔄 tryRefreshToken: No refresh token available');
      return false;
    }

    console.log('🔄 tryRefreshToken: Attempting token refresh...');
    const response = await fetch(`${API_BASE_URL}${KIOSK_AUTH_REFRESH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: "include"
    });

    if (!response.ok) {
      console.error('🔄 tryRefreshToken: Refresh failed with status', response.status);
      return false;
    }

    const data: RefreshResponseDto = await response.json();
    setAccessToken(data.access_token);
    // Also update refresh token as backend returns new one
    if (data.refresh_token) {
      setRefreshToken(data.refresh_token);
    }
    console.log('✅ tryRefreshToken: Token refreshed successfully');
    return true;
  } catch (error) {
    console.error('🔄 tryRefreshToken: Error during refresh:', error);
    return false;
  }
}
// ROLLBACK_MARKER: SSE_TOKEN_REFRESH_END
// ============================================================================

/**
 * Helper function to handle API responses with standardized error handling
 *
 * @param response The fetch Response object
 * @returns Parsed JSON data
 * @throws ApiError with appropriate type and message
 */
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let errorData;
    try {
      errorData = JSON.parse(errorText);
    } catch (e) {
      errorData = null;
    }

    // Handle specific error status codes
    if (response.status === 401) {
      throw new ApiError(
        'Unauthorized access. Please log in again.',
        'unauthorized',
        response.status
      );
    } else if (response.status >= 500) {
      throw new ApiError(
        'Server error, please try again later',
        'server',
        response.status
      );
    } else {
      throw new ApiError(
        errorData?.detail || `Request failed with status ${response.status}`,
        'unknown',
        response.status
      );
    }
  }

  return await response.json();
}
