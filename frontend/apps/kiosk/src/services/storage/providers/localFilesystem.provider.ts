import { IStorageProvider, LocalStorageConfig } from '../types/storageProvider.types';
import { MediaType } from '../types/mediaTypes.types';

/**
 * Local filesystem storage provider
 * Builds paths to media files stored on the local filesystem or served by local backend
 */
export class LocalFilesystemProvider implements IStorageProvider {
  private config: LocalStorageConfig;

  constructor(config: LocalStorageConfig) {
    this.config = config;
  }

  /**
   * Get the full path/URL for a media file
   * @param mediaType - Type of media
   * @param filename - Filename (e.g., "123.png", "beverages.mp4")
   * @returns Full path to the media file
   */
  getMediaUrl(mediaType: MediaType, filename: string): string {
    const basePath = this.getBasePath(mediaType);

    // Ensure proper path joining (handle trailing/leading slashes)
    const normalizedBase = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;
    const normalizedFilename = filename.startsWith('/') ? filename.slice(1) : filename;

    return `${normalizedBase}/${normalizedFilename}`;
  }

  /**
   * Get the base path for a specific media type
   * @param mediaType - Type of media
   * @returns Base path for this media type
   */
  getBasePath(mediaType: MediaType): string {
    const typePath = this.config.paths[mediaType];

    // If basePath is a full URL (starts with http/https), use it directly
    if (this.config.basePath.startsWith('http://') || this.config.basePath.startsWith('https://')) {
      const normalizedBase = this.config.basePath.endsWith('/')
        ? this.config.basePath.slice(0, -1)
        : this.config.basePath;
      const normalizedType = typePath.startsWith('/') ? typePath : `/${typePath}`;
      return `${normalizedBase}${normalizedType}`;
    }

    // For local file paths, join directly
    const normalizedBase = this.config.basePath.endsWith('/')
      ? this.config.basePath.slice(0, -1)
      : this.config.basePath;
    const normalizedType = typePath.startsWith('/') ? typePath : `/${typePath}`;
    return `${normalizedBase}${normalizedType}`;
  }

  /**
   * Check if the provider is properly configured
   * @returns true if base path is set
   */
  isConfigured(): boolean {
    return !!this.config.basePath;
  }

  /**
   * Get the provider configuration (useful for debugging)
   */
  getConfig(): LocalStorageConfig {
    return this.config;
  }
}
