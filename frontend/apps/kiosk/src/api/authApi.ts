// File: src/api/authApi.ts
//
// Purpose:
// Transport-only functions for kiosk authentication endpoints.
// Returns DTOs that reflect the exact backend JSON shape.
// No business logic or mapping here — keep it strictly HTTP + errors.

import type { LoginRequestDto, LoginResponseDto, RefreshResponseDto } from '../models/dto/auth.dto'
import { fetchWithAuth, handleApiResponse, ApiError } from './apiHttpClient'
import { KIOSK_AUTH_LOGIN, KIOSK_AUTH_REFRESH, KIOSK_AUTH_LOGOUT } from '../config/constants'

// Re-export ApiError as AuthError for backward compatibility
export { ApiError as AuthError }

/**
 * login()
 * Transport call to POST /api/kiosk/auth/login
 * Returns raw DTO from backend without transformations.
 */
export async function login(request: LoginRequestDto): Promise<LoginResponseDto> {

  try {
    const response = await fetchWithAuth(KIOSK_AUTH_LOGIN, {
      method: 'POST',
      body: JSON.stringify(request),
      // Do not attempt refresh+retry on login:
      // a 401 here means bad credentials and must surface to UI unchanged.
      retryOnUnauthenticated: false,
    });

    // Special handling for 401 in login case
    if (response.status === 401) {
      throw new ApiError(
        'Invalid username or password',
        'unauthorized',
        response.status
      );
    }

    return handleApiResponse<LoginResponseDto>(response);
  } catch (error) {

    // Rethrow ApiErrors
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle unexpected errors
    throw new ApiError(
      'Login failed. Please try again later.',
      'unknown'
    );
  }
}

/**
 * refresh()
 * Transport call to POST /api/kiosk/refresh
 * Returns raw DTO containing the new access token.
 * Note: This is called by auth.service.ts which handles refresh token from storage
 */
export async function refresh(refreshToken: string): Promise<RefreshResponseDto> {
  try {
    const response = await fetchWithAuth(KIOSK_AUTH_REFRESH, {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    return handleApiResponse<RefreshResponseDto>(response);
  } catch (error) {

    // Rethrow ApiErrors
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle unexpected errors
    throw new ApiError(
      'Failed to refresh token. Please log in again.',
      'network'
    );
  }
}

/**
 * Logout the current kiosk user
 * This will clear the refresh token cookie on the server
 */
export async function logout(): Promise<void> {
  try {
    await fetchWithAuth(KIOSK_AUTH_LOGOUT, {
      method: 'POST',
    });
  } catch (error) {
    // We don't throw here because we want to clear the local state
    // even if the server logout fails
  }
}
