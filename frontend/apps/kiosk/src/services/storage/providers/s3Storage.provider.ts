import { IStorageProvider, S3StorageConfig } from '../types/storageProvider.types';
import { MediaType } from '../types/mediaTypes.types';

/**
 * S3 storage provider
 * Builds URLs to media files stored in S3 or S3-compatible storage (MinIO, DigitalOcean Spaces, Selectel)
 *
 * URL Format: https://{endpoint}/{bucket}{path}/{filename}
 * Example: https://s3.ru-7.storage.selcloud.ru/kioskzc/items/123.png
 */
export class S3StorageProvider implements IStorageProvider {
  private config: S3StorageConfig;

  constructor(config: S3StorageConfig) {
    this.config = config;
  }

  /**
   * Get the full URL for a media file
   * @param mediaType - Type of media
   * @param filename - Filename (e.g., "123.png", "beverages.mp4")
   * @returns Full HTTPS URL to the media file
   */
  getMediaUrl(mediaType: MediaType, filename: string): string {
    const basePath = this.getBasePath(mediaType);

    // Ensure proper URL joining (handle trailing/leading slashes)
    const normalizedBase = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;
    const normalizedFilename = filename.startsWith('/') ? filename.slice(1) : filename;

    return `${normalizedBase}/${normalizedFilename}`;
  }

  /**
   * Get the base URL for a specific media type
   * Builds URL from: endpoint + bucket + path
   * @param mediaType - Type of media
   * @returns Base URL for this media type
   */
  getBasePath(mediaType: MediaType): string {
    const typePath = this.config.paths[mediaType];

    // Normalize endpoint (remove trailing slash)
    let endpoint = this.config.endpoint;
    if (endpoint.endsWith('/')) {
      endpoint = endpoint.slice(0, -1);
    }

    // Normalize type path (remove leading slash, keep structure)
    const path = typePath.startsWith('/') ? typePath.slice(1) : typePath;

    // If bucket is empty, endpoint already includes the bucket (e.g., Selectel CDN URL)
    // Format: https://cd4e3f93-c551-4c5c-a76d-733f763920f1.selstorage.ru/items
    if (!this.config.bucket) {
      return `${endpoint}/${path}`;
    }

    // Otherwise, build URL: https://endpoint/bucket/path
    // Format: https://s3.amazonaws.com/mybucket/items
    const bucket = this.config.bucket.replace(/^\/+|\/+$/g, '');
    return `${endpoint}/${bucket}/${path}`;
  }

  /**
   * Check if the provider is properly configured
   * @returns true if endpoint is set (bucket is optional for CDN URLs)
   */
  isConfigured(): boolean {
    return !!this.config.endpoint;
  }

  /**
   * Get the provider configuration (useful for debugging)
   * Note: Does not expose secret key for security
   */
  getConfig() {
    return {
      endpoint: this.config.endpoint,
      bucket: this.config.bucket,
      region: this.config.region,
      accessKeyId: this.config.accessKeyId,
      useSSL: this.config.useSSL,
      paths: this.config.paths,
    };
  }

  /**
   * Check if S3 credentials are configured
   */
  hasCredentials(): boolean {
    return !!(this.config.accessKeyId && this.config.secretAccessKey);
  }

  /**
   * Get S3 bucket name
   */
  getBucketName(): string {
    return this.config.bucket;
  }

  /**
   * Get S3 region
   */
  getRegion(): string {
    return this.config.region;
  }

  /**
   * Get S3 endpoint
   */
  getEndpoint(): string {
    return this.config.endpoint;
  }
}
