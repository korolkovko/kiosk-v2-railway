// File: src/api/getAllMenuItemsForPreload.api.ts
//
// Purpose:
// Transport-layer API call for fetching ALL items and categories from active menu for media preload.
// Returns items regardless of stock, stop list, or availability - used for caching media at login.

import { KIOSK_MENU_ALL_FOR_PRELOAD } from '../config/constants'
import { fetchWithAuth, handleApiResponse } from './apiHttpClient'

export interface GetAllMenuItemsForPreloadResponseDto {
  item_ids: number[]
  category_names: string[]  // Now includes synthetic promoted at [0]
}

/**
 * getAllMenuItemsForPreload()
 * Fetch ALL item IDs and category names from active menu for media preloading.
 * Requires kiosk authentication.
 *
 * Returns ALL items and categories from active menu regardless of:
 * - Stock quantity (includes items with stock = 0)
 * - Stop list status
 * - Availability status
 * - Active/archived status
 *
 * Purpose: Called at login to cache media for items that might become available
 * during the session via SSE (stock replenishment, stop list removal, etc.).
 *
 * @returns Promise<GetAllMenuItemsForPreloadResponseDto> Object with item_ids and category_names arrays
 * @throws ApiError if request fails
 */
export async function getAllMenuItemsForPreload(): Promise<GetAllMenuItemsForPreloadResponseDto> {
  const response = await fetchWithAuth(KIOSK_MENU_ALL_FOR_PRELOAD, {
    method: 'GET',
  })

  return handleApiResponse<GetAllMenuItemsForPreloadResponseDto>(response)
}
