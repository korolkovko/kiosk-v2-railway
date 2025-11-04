// menuRefresh.service.ts
//
// Purpose:
// Handle menu activation SSE events by downloading new media and refreshing menu data.
// Simplified approach: Show loading UI regardless of service mode state.
//
// Flow:
// 1. Check if on service mode page (if yes, download silently)
// 2. Show loading overlay (if not on service mode page)
// 3. Fetch new menu items and categories
// 4. Download only NEW media (incremental download - skip already cached)
// 5. Refresh items context
// 6. Navigate to main page (if not on service mode page)

import { getAllMenuItemsForPreload } from '../api/getAllMenuItemsForPreload.api'
import { mediaCacheService } from './mediaCache.service'
import type { DownloadProgress } from './mediaCache.service'

export interface MenuRefreshResult {
  success: boolean
  error?: string
}

export class MenuRefreshService {
  /**
   * Handle menu activation event
   * @param menuId ID of the activated menu
   * @param menuName Name of the activated menu
   * @param onProgress Progress callback for media downloads
   * @returns Result indicating success or failure
   */
  async handleMenuActivation(
    menuId: number,
    menuName: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<MenuRefreshResult> {
    try {
      console.log(`📋 Menu activated: ${menuName} (ID: ${menuId})`)

      // Step 1: Fetch ALL items and categories from the newly activated menu
      console.log('📡 Fetching menu items and categories for new menu...')
      const menuData = await getAllMenuItemsForPreload()

      // Step 2: Download media incrementally (only new items/categories)
      console.log('📥 Starting incremental media download...')

      // Get category names from backend (already includes synthetic promoted at [0])
      const categoryNames = menuData.category_names
      const itemIds = menuData.item_ids

      // Synthetic promoted category is always first in the array
      const syntheticPromotedCategoryName = categoryNames[0] || 'promoted'

      console.log(`📋 Categories to check: ${categoryNames.length}`)
      console.log(`📋 Items to check: ${itemIds.length}`)
      console.log(`📋 Synthetic promoted category: ${syntheticPromotedCategoryName}`)

      // downloadAllMedia will skip items already in cache (incremental download)
      await mediaCacheService.downloadAllMedia(
        categoryNames,
        itemIds,
        syntheticPromotedCategoryName,
        onProgress
      )

      console.log('✅ Menu refresh complete!')

      return { success: true }

    } catch (error: any) {
      console.error('❌ Menu refresh failed:', error)
      return {
        success: false,
        error: error.message || 'Failed to refresh menu'
      }
    }
  }

  /**
   * Check if a specific category is already cached
   * @param categoryName Category name to check
   * @returns True if cached, false otherwise
   */
  async isCategoryCached(categoryName: string): Promise<boolean> {
    const openKey = `category_${categoryName}`
    const openMedia = await mediaCacheService.getMediaEntry(openKey)
    return openMedia !== null
  }

  /**
   * Check if a specific item is already cached
   * @param itemId Item ID to check
   * @returns True if cached, false otherwise
   */
  async isItemCached(itemId: number): Promise<boolean> {
    const itemKey = `item_${itemId}`
    const itemMedia = await mediaCacheService.getMediaEntry(itemKey)
    return itemMedia !== null
  }
}

// Singleton instance
export const menuRefreshService = new MenuRefreshService()
