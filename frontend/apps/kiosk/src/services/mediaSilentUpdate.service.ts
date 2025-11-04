// mediaSilentUpdate.service.ts
//
// Purpose:
// Handle MEDIA_UPDATE SSE events by silently re-downloading specific media in background.
// No UI interruption, no loading overlay, no navigation - completely silent.
//
// Flow:
// 1. Receive MEDIA_UPDATE event with media_type and identifier
// 2. Determine storage paths based on media_type
// 3. Silently fetch from storage (local/S3 based on env)
// 4. Update IndexedDB cache (overwrite existing entry)
// 5. Tolerate 404s - if file doesn't exist, skip silently
//
// Media Type Mapping:
// - "item" → MediaType.ITEMS, key: "item_{identifier}"
// - "category_open" → MediaType.CATEGORIES_OPEN, key: "category_{identifier}"
// - "category_sorry" → MediaType.CATEGORIES_SORRY, key: "category_ssory_{identifier}"
// - "category_promoted" → MediaType.CATEGORIES_PROMOTED, key: "category_promoted"
// - "screensaver" → MediaType.SCREENSAVER, key: "screensaver_{identifier}"
// - "order_handling" → MediaType.ORDER_HANDLING, key: "order_handling_{identifier}"
// - "service_mode" → MediaType.SERVICE_MODE, key: "service_mode_{identifier}"

import { mediaCacheService } from './mediaCache.service'
import { MediaType } from './storage/types/mediaTypes.types'

export interface MediaUpdateResult {
  success: boolean
  error?: string
}

export class MediaSilentUpdateService {
  /**
   * Handle media update event - silently re-download and update cache
   * @param mediaType Type of media to update
   * @param identifier Item ID, category name, or specific name
   * @returns Result indicating success or failure
   */
  async handleMediaUpdate(
    mediaType: string,
    identifier: string
  ): Promise<MediaUpdateResult> {
    try {
      console.log(`🔄 Silent media update: type=${mediaType}, identifier=${identifier}`)

      // Map media_type to MediaType enum and cache key
      const mapping = this.getMediaTypeMapping(mediaType, identifier)
      if (!mapping) {
        console.warn(`⚠️ Unknown media type: ${mediaType}`)
        return { success: false, error: `Unknown media type: ${mediaType}` }
      }

      const { storageMediaType, cacheKey, fileName } = mapping

      // Silently fetch media from storage
      const media = await mediaCacheService.findMediaFile(storageMediaType, fileName)

      if (!media) {
        // File doesn't exist in storage - tolerate and skip
        console.log(`ℹ️ Media not found in storage (404 tolerated): ${fileName}`)
        return { success: true } // Not an error - file just doesn't exist
      }

      // Determine media type (image or video)
      const isVideo = media.extension.match(/\.(mp4|webm|mov|avi)$/i)
      const mediaTypeString: 'image' | 'video' = isVideo ? 'video' : 'image'

      // Create cache entry
      const entry = {
        key: cacheKey,
        blob: media.blob,
        extension: media.extension,
        type: mediaTypeString,
        cachedAt: Date.now()
      }

      // Update IndexedDB cache (overwrites existing)
      await mediaCacheService.storeMediaEntry(entry)

      console.log(`✅ Silent media update complete: ${cacheKey}`)
      return { success: true }

    } catch (error: any) {
      console.error(`❌ Silent media update failed: ${error.message}`)
      return { success: false, error: error.message || 'Failed to update media' }
    }
  }

  /**
   * Map media_type string to MediaType enum, cache key, and file name
   * @param mediaType Media type from SSE event
   * @param identifier Identifier from SSE event
   * @returns Mapping object or null if unknown type
   */
  private getMediaTypeMapping(
    mediaType: string,
    identifier: string
  ): { storageMediaType: MediaType; cacheKey: string; fileName: string } | null {
    switch (mediaType) {
      case 'item':
        return {
          storageMediaType: MediaType.ITEMS,
          cacheKey: `item_${identifier}`,
          fileName: identifier  // Item ID as string
        }

      case 'category_open':
        return {
          storageMediaType: MediaType.CATEGORIES_OPEN,
          cacheKey: `category_${identifier}`,
          fileName: this.getCategoryPosterFileName(identifier)
        }

      case 'category_sorry':
        return {
          storageMediaType: MediaType.CATEGORIES_SORRY,
          cacheKey: `category_${identifier}_unavailable`,  // Must match mediaCache format
          fileName: this.getCategoryPosterFileName(identifier)
        }

      case 'category_promoted':
        return {
          storageMediaType: MediaType.CATEGORIES_PROMOTED,
          cacheKey: `category_${identifier}`,  // Must use identifier, not hardcoded
          fileName: this.getCategoryPosterFileName(identifier)
        }

      case 'screensaver':
        return {
          storageMediaType: MediaType.SCREENSAVER,
          cacheKey: `screensaver_${identifier}`,
          fileName: identifier  // Should be "screensaver"
        }

      case 'order_handling':
        return {
          storageMediaType: MediaType.ORDER_HANDLING,
          cacheKey: `orderhandling_${identifier}`,  // Must match mediaCache prefix (no underscore)
          fileName: identifier  // Should be "order_handling"
        }

      case 'service_mode':
        return {
          storageMediaType: MediaType.SERVICE_MODE,
          cacheKey: `service_${identifier}`,  // Must match buildServiceModeKey() format
          fileName: identifier  // Should be "menu", "maintenance", or "dayoff"
        }

      default:
        return null
    }
  }

  /**
   * Get category poster file name from category name
   * Uses dynamic name from promoted_label table (no hardcoding)
   * @param categoryName Category name from backend
   * @returns Poster file name (lowercase)
   */
  private getCategoryPosterFileName(categoryName: string): string {
    // Backend sends the actual category name from promoted_label table
    // No special mapping needed - just use the name as-is (lowercased)
    return categoryName.toLowerCase()
  }
}

// Singleton instance
export const mediaSilentUpdateService = new MediaSilentUpdateService()
