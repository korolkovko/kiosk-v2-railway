// File: src/services/posterLogic.service.ts
//
// Purpose:
// Pure service for determining which poster media to display based on category and available items.
// Simple logic: show main poster if items available, fallback poster if no items.
// Supports both images (.png, .jpg, etc.) and videos (.mp4, .webm, etc.)

import type { AvailableItemVM } from '../models/view/availableItem.vm'
import { getStorageProvider } from './storage/storageFactory'
import { MediaType } from './storage/types/mediaTypes.types'

export interface PosterInfo {
  imagePath: string
  altText: string
}

/**
 * MEDIA FOLDER STRUCTURE
 *
 * Media paths are now configurable via storage providers (local filesystem or S3).
 * See: src/services/storage/
 *
 * Categories:
 *   - CATEGORIES_OPEN: Posters when category has available items
 *   - CATEGORIES_SORRY: Posters when category has NO available items
 *
 *   File naming:
 *   - Regular categories: Use category name from backend (e.g., main.png, drinks.mp4)
 *   - Promoted category: Uses name from promoted_label table in DB (e.g., promoted.mp4, specials.mp4)
 *
 * Items:
 *   - ITEMS: Item posters named by ID (e.g., 1.png, 8.mp4)
 *
 * System automatically detects file extension:
 * - Tries video formats first: .mp4, .webm
 * - Then tries image formats: .png, .jpg, .jpeg, .gif
 */

/**
 * File extensions to try, in order of preference
 * Videos first (better for kiosk displays), then images
 */
export const MEDIA_EXTENSIONS = ['.mp4', '.webm', '.png', '.jpg', '.jpeg', '.gif']

/**
 * Helper to build category poster path using storage provider
 * @param categoryName - Category name from backend (e.g., "main", "drinks", "promoted")
 * @param isAvailable - True for open poster, false for sorry poster
 * @param promotedCategoryName - Name of the promoted category from categories[0].name
 */
function getCategoryPosterPath(
  categoryName: string,
  isAvailable: boolean,
  promotedCategoryName: string
): string {
  const storageProvider = getStorageProvider()
  const categoryLower = categoryName.toLowerCase()

  // Determine filename - use dynamic name from promoted_label table for promoted category
  const filename = categoryLower === promotedCategoryName.toLowerCase()
    ? promotedCategoryName.toLowerCase()
    : categoryLower

  // Determine media type
  // Promoted category uses dedicated CATEGORIES_PROMOTED folder (no sorry variant)
  // Other categories use CATEGORIES_OPEN or CATEGORIES_SORRY
  let mediaType: MediaType
  if (categoryLower === promotedCategoryName.toLowerCase()) {
    mediaType = MediaType.CATEGORIES_PROMOTED
  } else {
    mediaType = isAvailable ? MediaType.CATEGORIES_OPEN : MediaType.CATEGORIES_SORRY
  }

  // Return base path (without extension - extension detection happens in MediaDisplay component)
  return storageProvider.getBasePath(mediaType) + '/' + filename
}

/**
 * getPosterForCategory()
 * Determines which poster media to show based on category and available items.
 * Files are organized in subfolders (categories_open_poster / categories_sorry_poster).
 * Filename = category name from backend, except promoted category which uses "promoted".
 *
 * @param category - Category name from backend (e.g., "promoted", "main", "drinks", "sides")
 * @param availableItems - List of available items
 * @param selectedItem - Optional: If provided, shows item poster instead of category poster
 * @param promotedCategoryName - Name of the promoted category from categories[0].name
 */
export function getPosterForCategory(
  category: string,
  availableItems: AvailableItemVM[],
  selectedItem: AvailableItemVM | null | undefined,
  promotedCategoryName: string
): PosterInfo {
  // If an item is selected (items navigation mode), show item poster
  if (selectedItem) {
    return {
      imagePath: selectedItem.posterPath,
      altText: selectedItem.nameRu
    }
  }

  const categoryLower = category.toLowerCase()

  // Promoted category always shows promoted poster (no sorry variant)
  if (categoryLower === promotedCategoryName.toLowerCase()) {
    return {
      imagePath: getCategoryPosterPath(category, true, promotedCategoryName),
      altText: 'Promoted items'
    }
  }

  // Check if category has available items
  const hasAvailableItems = availableItems.some(item =>
    item.foodCategory.toLowerCase() === categoryLower &&
    item.isAvailable &&
    item.stockQuantity > 0
  )

  // Return poster path based on availability
  // Use category name from backend as filename (main, drinks, sides, etc.)
  return {
    imagePath: getCategoryPosterPath(categoryLower, hasAvailableItems, promotedCategoryName),
    altText: hasAvailableItems
      ? `${category} menu`
      : `${category} menu - currently unavailable`
  }
}

/**
 * getItemsForCategory()
 * Filters available items by category for display in ItemList.
 * Handles both 'food' and 'main' category names from backend.
 *
 * @param category - Category name from backend
 * @param availableItems - List of available items
 * @param promotedCategoryName - Name of the promoted category from categories[0].name
 */
export function getItemsForCategory(
  category: string,
  availableItems: AvailableItemVM[],
  promotedCategoryName: string
): AvailableItemVM[] {
  if (category.toLowerCase() === promotedCategoryName.toLowerCase()) {
    // Promoted category shows promoted items across all categories
    return availableItems.filter(item => item.promoted && item.isAvailable)
  }

  const categoryLower = category.toLowerCase()

  return availableItems.filter(item => {
    const itemCategory = item.foodCategory.toLowerCase()

    // Handle 'main' from backend mapping to 'food' in UI
    if (categoryLower === 'food' && itemCategory === 'main') {
      return item.isAvailable
    }

    return itemCategory === categoryLower && item.isAvailable
  })
}