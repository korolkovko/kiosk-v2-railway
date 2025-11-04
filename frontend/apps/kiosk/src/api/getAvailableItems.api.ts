// File: src/api/getAvailableItems.api.ts
//
// Purpose:
// Transport-layer API call for fetching available menu items.
// Uses authenticated fetch to retrieve items with stock from kiosk endpoint.

import { KIOSK_ITEMS_AVAILABLE } from '../config/constants'
import { fetchWithAuth, handleApiResponse } from './apiHttpClient'
import type { GetAvailableItemsResponseDto } from '../models/dto/getAvailableItems.dto'

/**
 * getAvailableItems()
 * Fetch available menu items from kiosk endpoint.
 * Requires kiosk authentication.
 *
 * @returns Promise<GetAvailableItemsResponseDto> Array of available items with stock
 * @throws ApiError if request fails
 */
export async function getAvailableItems(): Promise<GetAvailableItemsResponseDto> {
  const response = await fetchWithAuth(KIOSK_ITEMS_AVAILABLE, {
    method: 'GET',
  })

  return handleApiResponse<GetAvailableItemsResponseDto>(response)
}
