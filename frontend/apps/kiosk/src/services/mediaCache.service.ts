// File: src/services/mediaCache.service.ts
//
// Purpose:
// IndexedDB-based media caching service for kiosk.
// Downloads all media (category posters, item posters) on login and stores in IndexedDB.
// No network requests during session - instant media display.
//
// Architecture:
// - Login: Download ALL media → Store in IndexedDB
// - Session: Read from IndexedDB only (zero network requests)
// - Logout: Clear IndexedDB
//
// Storage Budget: 1GB (Safari limit)

import { MEDIA_EXTENSIONS } from './storage/types/mediaTypes.types'
import { getStorageProvider } from './storage/storageFactory'
import { MediaType } from './storage/types/mediaTypes.types'

const DB_NAME = 'KioskMediaCache'
const DB_VERSION = 1
const STORE_NAME = 'media'

export interface MediaCacheEntry {
  key: string // e.g., "category_NEW" or "item_8"
  blob: Blob
  extension: string // e.g., ".mp4" or ".png"
  type: 'image' | 'video'
  cachedAt: number // timestamp
}

export interface DownloadProgress {
  current: number
  total: number
  currentItem: string
  quotaUsed: number // bytes
  quotaAvailable: number // bytes
}

class MediaCacheService {
  private db: IDBDatabase | null = null

  /**
   * Initialize IndexedDB
   */
  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'key' })
        }
      }
    })
  }

  /**
   * Request persistent storage (prevents browser from auto-clearing)
   */
  async requestPersistentStorage(): Promise<boolean> {
    if (!navigator.storage?.persist) {
      console.warn('Persistent storage not supported')
      return false
    }

    const persistent = await navigator.storage.persist()
    if (persistent) {
      console.log('✅ Persistent storage granted')
    } else {
      console.warn('⚠️ Persistent storage denied')
    }

    return persistent
  }

  /**
   * Get storage quota information
   */
  async getQuotaInfo(): Promise<{ used: number; available: number; total: number }> {
    if (!navigator.storage?.estimate) {
      return { used: 0, available: 0, total: 0 }
    }

    const estimate = await navigator.storage.estimate()
    const used = estimate.usage || 0
    const total = estimate.quota || 0
    const available = total - used

    return { used, available, total }
  }

  /**
   * Get category poster file name
   * Promoted category uses its name from DB, all others use backend category name directly
   * @param categoryName - Category name from backend
   * @param promotedCategoryName - Name of the promoted category from categories[0].name
   */
  private getCategoryPosterFileName(categoryName: string, promotedCategoryName: string): string {
    const lowerName = categoryName.toLowerCase()
    const promotedLower = promotedCategoryName.toLowerCase()

    // Promoted category uses its dynamic name from promoted_label table
    // This allows backend to control the media filename via the DB
    if (lowerName === promotedLower) {
      return promotedLower
    }

    // All other categories use backend category name as filename
    // e.g., "main" → main.png, "drinks" → drinks.mp4
    return lowerName
  }

  /**
   * Check if file exists with any supported extension
   * Returns { path, extension, blob } or null if not found
   * Public method used by mediaSilentUpdateService for SSE-driven media updates
   */
  async findMediaFile(mediaType: MediaType, filename: string): Promise<{ path: string; extension: string; blob: Blob } | null> {
    const storageProvider = getStorageProvider()

    for (const ext of MEDIA_EXTENSIONS) {
      const filenameWithExt = `${filename}${ext}`
      const testPath = storageProvider.getMediaUrl(mediaType, filenameWithExt)

      try {
        console.log(`📥 Attempting to fetch: ${testPath}`)
        // Skip HEAD request - just try to download directly
        // (HEAD requests have CORS issues in some browsers)
        // Use 'reload' to bypass cached 404 responses from previous attempts
        const response = await fetch(testPath, { cache: 'reload' })
        console.log(`📊 Response: status=${response.status}`)

        if (!response.ok) {
          console.log(`⏭️ Skipping ${testPath}: status ${response.status}`)
          continue
        }

        const contentType = response.headers.get('content-type') || ''
        console.log(`📊 Content-Type: "${contentType}"`)

        const isActualMedia =
          contentType.startsWith('image/') ||
          contentType.startsWith('video/') ||
          contentType.includes('octet-stream')

        if (isActualMedia) {
          const blob = await response.blob()
          console.log(`✅ Media downloaded: ${testPath} (${blob.size} bytes, ${blob.type})`)
          return { path: testPath, extension: ext, blob }
        } else {
          console.log(`⏭️ Skipping ${testPath}: not media (${contentType})`)
        }
      } catch (err) {
        console.error(`❌ Error fetching ${testPath}:`, err)
        // Try next extension
        continue
      }
    }

    return null
  }

  /**
   * Download all media and store in IndexedDB
   * Throws error if quota exceeded
   * @param categoryNames - List of category names
   * @param itemIds - List of item IDs
   * @param promotedCategoryName - Name of the promoted category from categories[0].name
   * @param onProgress - Progress callback
   */
  async downloadAllMedia(
    categoryNames: string[],
    itemIds: number[],
    promotedCategoryName: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    // Request persistent storage
    await this.requestPersistentStorage()

    // For categories with "ssory" variants, we need to download both versions
    // Calculate total: categories + ssory variants + items
    const promotedLower = promotedCategoryName.toLowerCase()
    const categoriesWithSsory = categoryNames.filter(cat =>
      cat.toLowerCase() !== promotedLower // Promoted category doesn't have ssory variant
    )
    const totalItems = categoryNames.length + categoriesWithSsory.length + itemIds.length
    let currentItem = 0

    const updateProgress = async (itemName: string) => {
      if (onProgress) {
        const quota = await this.getQuotaInfo()
        onProgress({
          current: currentItem,
          total: totalItems,
          currentItem: itemName,
          quotaUsed: quota.used,
          quotaAvailable: quota.available
        })
      }
    }

    // Download category posters (open versions - when items available)
    console.log('📁 Downloading category "open" posters:', categoryNames)
    for (const categoryName of categoryNames) {
      currentItem++
      await updateProgress(`Category (open): ${categoryName}`)

      const posterFileName = this.getCategoryPosterFileName(categoryName, promotedCategoryName)
      console.log(`📁 Category "${categoryName}" → file "${posterFileName}"`)

      // Promoted category uses dedicated CATEGORIES_PROMOTED media type
      const mediaType = categoryName.toLowerCase() === promotedLower
        ? MediaType.CATEGORIES_PROMOTED
        : MediaType.CATEGORIES_OPEN

      console.log(`🔍 Looking for open poster: ${posterFileName} (type: ${mediaType})`)
      const media = await this.findMediaFile(mediaType, posterFileName)

      if (media) {
        const entry: MediaCacheEntry = {
          key: `category_${categoryName}`,
          blob: media.blob,
          extension: media.extension,
          type: media.extension.match(/\.(mp4|webm|mov|avi)$/i) ? 'video' : 'image',
          cachedAt: Date.now()
        }

        await this.storeMedia(entry)
      } else {
        console.warn(`Category open poster not found: ${categoryName} (tried: ${posterFileName})`)
      }
    }

    // Download category posters (sorry versions - when NO items available)
    // Promoted category doesn't have sorry variant - already filtered out in categoriesWithSsory
    console.log('📁 Downloading category "sorry" posters...')
    for (const categoryName of categoriesWithSsory) {
      currentItem++
      await updateProgress(`Category (sorry): ${categoryName}`)

      const posterFileName = this.getCategoryPosterFileName(categoryName, promotedCategoryName)
      console.log(`📁 Category "${categoryName}" (sorry) → file "${posterFileName}"`)
      console.log(`🔍 Looking for sorry poster: ${posterFileName}`)
      const media = await this.findMediaFile(MediaType.CATEGORIES_SORRY, posterFileName)

      if (media) {
        const entry: MediaCacheEntry = {
          key: `category_${categoryName}_unavailable`, // Different cache key for sorry variant
          blob: media.blob,
          extension: media.extension,
          type: media.extension.match(/\.(mp4|webm|mov|avi)$/i) ? 'video' : 'image',
          cachedAt: Date.now()
        }

        await this.storeMedia(entry)
      } else {
        console.warn(`Category sorry poster not found: ${categoryName} (tried: ${posterFileName})`)
      }
    }

    // Download item posters
    console.log('📁 Downloading item posters...')
    for (const itemId of itemIds) {
      currentItem++
      await updateProgress(`Item: ${itemId}`)

      console.log(`🔍 Looking for item poster: ${itemId}`)
      const media = await this.findMediaFile(MediaType.ITEMS, String(itemId))

      if (media) {
        const entry: MediaCacheEntry = {
          key: `item_${itemId}`,
          blob: media.blob,
          extension: media.extension,
          type: media.extension.match(/\.(mp4|webm|mov|avi)$/i) ? 'video' : 'image',
          cachedAt: Date.now()
        }

        await this.storeMedia(entry)
      } else {
        console.warn(`Item poster not found: ${itemId}`)
      }
    }

    // Final progress update
    await updateProgress('Complete')
  }

  /**
   * Store media entry in IndexedDB
   * Throws error if quota exceeded
   */
  private async storeMedia(entry: MediaCacheEntry): Promise<void> {
    if (!this.db) {
      throw new Error('Database not initialized')
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.put(entry)

      request.onsuccess = () => resolve()
      request.onerror = () => {
        // Check if it's a quota error
        if (request.error?.name === 'QuotaExceededError') {
          reject(new Error('QUOTA_EXCEEDED: Storage limit reached. Cannot cache more media.'))
        } else {
          reject(request.error)
        }
      }
    })
  }

  /**
   * Store media entry in IndexedDB (public wrapper)
   * Used by external services like mediaSilentUpdate
   * Throws error if quota exceeded
   */
  async storeMediaEntry(entry: MediaCacheEntry): Promise<void> {
    if (!this.db) {
      await this.init()
    }
    return this.storeMedia(entry)
  }

  /**
   * Get media from IndexedDB cache
   * Returns Blob URL or null if not cached
   */
  async getMedia(key: string): Promise<string | null> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.get(key)

      request.onsuccess = () => {
        const entry = request.result as MediaCacheEntry | undefined

        if (entry) {
          // Create blob URL from cached blob
          const blobUrl = URL.createObjectURL(entry.blob)
          resolve(blobUrl)
        } else {
          resolve(null)
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get media entry with metadata
   */
  async getMediaEntry(key: string): Promise<MediaCacheEntry | null> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.get(key)

      request.onsuccess = () => {
        resolve(request.result || null)
      }

      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Clear all cached media (call on logout)
   */
  async clearAll(): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.clear()

      request.onsuccess = () => {
        console.log('✅ Media cache cleared')
        resolve()
      }
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Get all cached media keys (for debugging)
   */
  async getAllKeys(): Promise<string[]> {
    if (!this.db) {
      await this.init()
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.getAllKeys()

      request.onsuccess = () => resolve(request.result as string[])
      request.onerror = () => reject(request.error)
    })
  }

  /**
   * Check if media is cached
   */
  async isCached(key: string): Promise<boolean> {
    const entry = await this.getMediaEntry(key)
    return entry !== null
  }

  /**
   * Build cache key for service mode media
   * Example: "maintenance" -> "service_maintenance"
   */
  private buildServiceModeKey(name: string): string {
    return `service_${name}`
  }

  /**
   * Download all service mode media at login.
   * - Baseline names are read from env CSV VITE_SERVICE_MODE_MEDIA_NAMES
   * - You may pass additionalNames to include runtime-discovered names (e.g., current status picture)
   * - Uses existing findMediaFile() with MediaType.SERVICE_MODE and stores entries under "service_<name>" keys
   * - Progress labels use "asset" terminology to avoid confusion with menu Items
   */
  async downloadAllServiceModeMediaAtLogin(
    additionalNames: string[] = [],
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    // Request persistent storage
    await this.requestPersistentStorage()

    // Parse env CSV baseline list
    const csv = (import.meta.env.VITE_SERVICE_MODE_MEDIA_NAMES || '') as string
    const envNames = csv
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)

    // Union of env + additional names (case-sensitive by design; S3/local keys are case-sensitive)
    const nameSet = new Set<string>([
      ...envNames,
      ...additionalNames
    ])
    const names = Array.from(nameSet)

    const totalAssets = names.length
    let currentAsset = 0

    const updateProgress = async (assetLabel: string) => {
      if (onProgress) {
        const quota = await this.getQuotaInfo()
        onProgress({
          current: currentAsset,
          total: totalAssets,
          // Keep the existing "currentItem" field for compatibility, but label shows "asset"
          currentItem: assetLabel,
          quotaUsed: quota.used,
          quotaAvailable: quota.available
        })
      }
    }

    for (const name of names) {
      currentAsset++
      await updateProgress(`Service asset: ${name}`)

      // Skip if already cached
      const cacheKey = this.buildServiceModeKey(name)
      if (await this.isCached(cacheKey)) {
        console.log(`⏭️ Service mode media already cached: ${cacheKey}`)
        continue
      }

      console.log(`🔍 Looking for service mode media: ${name}`)
      const media = await this.findMediaFile(MediaType.SERVICE_MODE, name)

      if (media) {
        const entry: MediaCacheEntry = {
          key: cacheKey,
          blob: media.blob,
          extension: media.extension,
          type: /\.(mp4|webm|mov|avi)$/i.test(media.extension) ? 'video' : 'image',
          cachedAt: Date.now()
        }

        await this.storeMedia(entry)
        console.log(`✅ Cached service mode media: ${cacheKey}`)
      } else {
        console.warn(`⚠️ Service mode media not found: ${name}`)
      }
    }
  }

  /**
   * Ensure a specific service mode media is cached; download on demand if missing.
   * Returns true if the media exists in cache after the call, false otherwise.
   */
  async ensureServiceModeMediaCached(name: string): Promise<boolean> {
    if (!this.db) {
      await this.init()
    }

    const cacheKey = this.buildServiceModeKey(name)
    if (await this.isCached(cacheKey)) {
      return true
    }

    const media = await this.findMediaFile(MediaType.SERVICE_MODE, name)
    if (!media) {
      console.warn(`⚠️ ensureServiceModeMediaCached: media not found for "${name}"`)
      return false
    }

    const entry: MediaCacheEntry = {
      key: cacheKey,
      blob: media.blob,
      extension: media.extension,
      type: /\.(mp4|webm|mov|avi)$/i.test(media.extension) ? 'video' : 'image',
      cachedAt: Date.now()
    }

    await this.storeMedia(entry)
    console.log(`✅ ensureServiceModeMediaCached: cached "${cacheKey}"`)
    return true
  }

  /**
   * Get cached service mode media entry by logical name (without extension).
   * Returns null if not cached.
   */
  async getServiceModeMediaEntry(name: string): Promise<MediaCacheEntry | null> {
    return this.getMediaEntry(this.buildServiceModeKey(name))
  }

  /**
   * Generic downloader for named assets under a specific media type, driven by an env CSV.
   * Example usage:
   *  - mediaType = MediaType.SCREENSAVER, envVarName = 'VITE_SCREENSAVER_MEDIA_NAMES', cacheKeyPrefix = 'screensaver'
   *  - mediaType = MediaType.ORDER_HANDLING, envVarName = 'VITE_ORDER_HANDLING_MEDIA_NAMES', cacheKeyPrefix = 'orderhandling'
   */
  private async downloadNamedMediaAtLogin(
    mediaType: MediaType,
    envVarName: string,
    cacheKeyPrefix: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<void> {
    if (!this.db) {
      await this.init()
    }

    await this.requestPersistentStorage()

    const csv = ((import.meta.env as any)[envVarName] || '') as string
    const names = csv
      .split(',')
      .map((s: string) => s.trim())
      .filter(Boolean)

    const totalAssets = names.length
    let currentAsset = 0

    const updateProgress = async (assetLabel: string) => {
      if (onProgress) {
        const quota = await this.getQuotaInfo()
        onProgress({
          current: currentAsset,
          total: totalAssets,
          currentItem: assetLabel,
          quotaUsed: quota.used,
          quotaAvailable: quota.available
        })
      }
    }

    for (const name of names) {
      currentAsset++
      await updateProgress(`${cacheKeyPrefix} asset: ${name}`)

      const cacheKey = `${cacheKeyPrefix}_${name}`
      if (await this.isCached(cacheKey)) {
        console.log(`⏭️ ${cacheKeyPrefix} media already cached: ${cacheKey}`)
        continue
      }

      console.log(`🔍 Looking for ${cacheKeyPrefix} media: ${name}`)
      const media = await this.findMediaFile(mediaType, name)

      if (media) {
        const entry: MediaCacheEntry = {
          key: cacheKey,
          blob: media.blob,
          extension: media.extension,
          // Treat as video only for known video extensions; otherwise image (covers .webp)
          type: /\.(mp4|webm|mov|avi)$/i.test(media.extension) ? 'video' : 'image',
          cachedAt: Date.now()
        }

        await this.storeMedia(entry)
        console.log(`✅ Cached ${cacheKeyPrefix} media: ${cacheKey}`)
      } else {
        console.warn(`⚠️ ${cacheKeyPrefix} media not found: ${name}`)
      }
    }
  }

  /**
   * Download all Screensaver media by names provided in VITE_SCREENSAVER_MEDIA_NAMES
   */
  async downloadAllScreensaverMediaAtLogin(
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<void> {
    await this.downloadNamedMediaAtLogin(
      MediaType.SCREENSAVER,
      'VITE_SCREENSAVER_MEDIA_NAMES',
      'screensaver',
      onProgress
    )
  }

  /**
   * Download all Order Handling media by names provided in VITE_ORDER_HANDLING_MEDIA_NAMES
   */
  async downloadAllOrderHandlingMediaAtLogin(
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<void> {
    await this.downloadNamedMediaAtLogin(
      MediaType.ORDER_HANDLING,
      'VITE_ORDER_HANDLING_MEDIA_NAMES',
      'orderhandling',
      onProgress
    )
  }
}
 
// Export singleton instance
export const mediaCacheService = new MediaCacheService()
