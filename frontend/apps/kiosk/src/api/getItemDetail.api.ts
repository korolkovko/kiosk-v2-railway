// getItemDetail.api.ts
// API client for fetching individual item details

import { fetchWithAuth, handleApiResponse } from './apiHttpClient'
import type { GetAvailableItemDto } from '../models/dto/getAvailableItems.dto'

// Reuse the same DTO type since the response structure is identical
export type GetItemDetailResponseDTO = GetAvailableItemDto

/**
 * Fetch detailed information for a specific item by ID.
 *
 * Used when SSE updates reference items that weren't in the initial
 * available items list (e.g., items that had 0 stock when kiosk first
 * loaded but now have stock > 0).
 *
 * @param itemId - The ID of the item to fetch
 * @returns Promise resolving to item details with current stock
 * @throws Error if item not found or request fails
 */
export async function getItemDetailAPI(itemId: number): Promise<GetItemDetailResponseDTO> {
  const response = await fetchWithAuth(`/kiosk/items/${itemId}`)
  return await handleApiResponse<GetItemDetailResponseDTO>(response)
}