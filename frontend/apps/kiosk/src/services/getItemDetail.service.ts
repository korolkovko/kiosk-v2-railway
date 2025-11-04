// getItemDetail.service.ts
// Service layer for fetching individual item details

import { getItemDetailAPI } from '../api/getItemDetail.api'
import { mapGetAvailableItemsDtoToDomain, mapGetAvailableItemsDomainToVM } from './mappers/getAvailableItems.mappers'
import type { AvailableItemVM } from '../models/view/availableItem.vm'

/**
 * Fetch detailed information for a specific item by ID and convert to ViewModel.
 *
 * Used when SSE updates reference items that weren't in the initial
 * available items list (e.g., items that had 0 stock when kiosk first
 * loaded but now have stock > 0).
 *
 * @param itemId - The ID of the item to fetch
 * @returns Promise resolving to AvailableItemVM with current item details
 * @throws Error if item not found or request fails
 */
export async function getItemDetailVM(itemId: number): Promise<AvailableItemVM> {
  try {
    const itemDto = await getItemDetailAPI(itemId)
    
    // Transform DTO → Domain → ViewModel using existing mappers
    const domainItems = mapGetAvailableItemsDtoToDomain([itemDto])
    const viewModelItems = mapGetAvailableItemsDomainToVM(domainItems)
    
    return viewModelItems[0]
  } catch (error) {
    console.error(`Failed to fetch item detail for ID ${itemId}:`, error)
    throw error
  }
}