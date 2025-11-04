import { IStorageProvider, StorageProviderType } from './types/storageProvider.types';
import { LocalFilesystemProvider } from './providers/localFilesystem.provider';
import { S3StorageProvider } from './providers/s3Storage.provider';
import { storageConfig } from './storageConfig';

/**
 * Factory to create and manage storage provider instances
 */
class StorageFactory {
  private static instance: IStorageProvider | null = null;

  /**
   * Get the active storage provider instance (singleton)
   * @returns Active storage provider based on configuration
   */
  static getProvider(): IStorageProvider {
    if (!this.instance) {
      this.instance = this.createProvider();
    }
    return this.instance;
  }

  /**
   * Create a new storage provider instance based on configuration
   * @returns Storage provider instance
   */
  private static createProvider(): IStorageProvider {
    const { provider } = storageConfig;

    switch (provider) {
      case StorageProviderType.S3:
        console.log('[StorageFactory] Initializing S3 storage provider');
        return new S3StorageProvider(storageConfig.s3);

      case StorageProviderType.LOCAL:
      default:
        console.log('[StorageFactory] Initializing local filesystem storage provider');
        return new LocalFilesystemProvider(storageConfig.local);
    }
  }

  /**
   * Reset the singleton instance (useful for testing or config changes)
   */
  static reset(): void {
    this.instance = null;
  }

  /**
   * Get the current provider type
   */
  static getProviderType(): StorageProviderType {
    return storageConfig.provider;
  }

  /**
   * Check if the current provider is properly configured
   */
  static isConfigured(): boolean {
    const provider = this.getProvider();
    return provider.isConfigured();
  }
}

/**
 * Get the active storage provider instance
 * This is the main export used throughout the application
 */
export function getStorageProvider(): IStorageProvider {
  return StorageFactory.getProvider();
}

/**
 * Get the current provider type
 */
export function getStorageProviderType(): StorageProviderType {
  return StorageFactory.getProviderType();
}

/**
 * Check if storage is properly configured
 */
export function isStorageConfigured(): boolean {
  return StorageFactory.isConfigured();
}

/**
 * Reset storage provider (useful for testing)
 */
export function resetStorageProvider(): void {
  StorageFactory.reset();
}
