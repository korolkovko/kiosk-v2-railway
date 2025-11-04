/**
 * Storage service public API
 *
 * This module provides a unified interface for media storage,
 * supporting both local filesystem and S3-compatible cloud storage.
 *
 * Usage:
 * ```typescript
 * import { getStorageProvider, MediaType } from '@/services/storage'
 *
 * const storage = getStorageProvider()
 * const itemUrl = storage.getMediaUrl(MediaType.ITEMS, '123.png')
 * ```
 */

// Main factory and utilities
export {
  getStorageProvider,
  getStorageProviderType,
  isStorageConfigured,
  resetStorageProvider
} from './storageFactory'

// Configuration
export { storageConfig, logStorageConfig } from './storageConfig'

// Types
export type {
  IStorageProvider,
  StorageConfig,
  LocalStorageConfig,
  S3StorageConfig,
  StorageProviderType
} from './types/storageProvider.types'

export { MediaType, MEDIA_EXTENSIONS, isSupportedExtension } from './types/mediaTypes.types'
export type { MediaExtension } from './types/mediaTypes.types'

// Providers (for advanced usage)
export { LocalFilesystemProvider } from './providers/localFilesystem.provider'
export { S3StorageProvider } from './providers/s3Storage.provider'
