// File: src/api/menuActivation.api.ts
//
// Purpose:
// Transport-only function for menu activation status endpoint.
// Returns DTO that reflects the exact backend JSON shape.
// No business logic or mapping here — keep it strictly HTTP + errors.

import { fetchWithAuth, handleApiResponse, ApiError } from './apiHttpClient'
import { MENU_ACTIVATION_STATUS } from '../config/constants'

/**
 * MenuInfo
 * Information about an active menu
 */
export interface MenuInfo {
  id: number
  name: string
  description: string | null
}

/**
 * MenuActivationStatusResponse
 * Response from menu activation status endpoint
 */
export interface MenuActivationStatusResponse {
  total_menus: number
  active_menus: number
  inactive_menus: number
  currently_active_menu: MenuInfo | null
}

/**
 * getMenuActivationStatus()
 * Transport call to GET /api/v1/menu-management/activation-status
 * Returns raw DTO from backend without transformations.
 *
 * @returns Menu activation status with currently active menu info (or null)
 * @throws ApiError if request fails
 */
export async function getMenuActivationStatus(): Promise<MenuActivationStatusResponse> {
  try {
    const response = await fetchWithAuth(MENU_ACTIVATION_STATUS, {
      method: 'GET',
    })

    return handleApiResponse<MenuActivationStatusResponse>(response)
  } catch (error) {
    // Rethrow ApiErrors
    if (error instanceof ApiError) {
      throw error
    }

    // Handle unexpected errors
    throw new ApiError(
      'Failed to fetch menu activation status. Please try again later.',
      'network'
    )
  }
}
