import { MediaType } from './mediaTypes.types';

/**
 * Storage provider types supported by the application
 */
export enum StorageProviderType {
  /** Local filesystem storage */
  LOCAL = 'local',

  /** Amazon S3 or S3-compatible storage (MinIO, DigitalOcean Spaces) */
  S3 = 's3',
}

/**
 * Configuration for local filesystem storage
 */
export interface LocalStorageConfig {
  /** Base path or URL for local media */
  basePath: string;

  /** Path patterns for each media type */
  paths: {
    [MediaType.ITEMS]: string;
    [MediaType.CATEGORIES_OPEN]: string;
    [MediaType.CATEGORIES_SORRY]: string;
    [MediaType.CATEGORIES_PROMOTED]: string;
    [MediaType.SCREENSAVER]: string;
    [MediaType.ORDER_HANDLING]: string;
    [MediaType.FABRIC]: string;
  };
}

/**
 * Configuration for S3 storage
 */
export interface S3StorageConfig {
  /** S3 endpoint URL (e.g., https://s3.amazonaws.com or https://s3.ru-7.storage.selcloud.ru) */
  endpoint: string;

  /** S3 bucket name */
  bucket: string;

  /** S3 region */
  region: string;

  /** S3 access key ID */
  accessKeyId: string;

  /** S3 secret access key */
  secretAccessKey: string;

  /** Use SSL/HTTPS for S3 connections */
  useSSL: boolean;

  /** Path prefixes (folders) for each media type */
  paths: {
    [MediaType.ITEMS]: string;
    [MediaType.CATEGORIES_OPEN]: string;
    [MediaType.CATEGORIES_SORRY]: string;
    [MediaType.CATEGORIES_PROMOTED]: string;
    [MediaType.SCREENSAVER]: string;
    [MediaType.ORDER_HANDLING]: string;
    [MediaType.FABRIC]: string;
  };
}

/**
 * Unified storage configuration
 */
export interface StorageConfig {
  /** Active storage provider */
  provider: StorageProviderType;

  /** Local storage configuration */
  local: LocalStorageConfig;

  /** S3 storage configuration */
  s3: S3StorageConfig;
}

/**
 * Interface that all storage providers must implement
 */
export interface IStorageProvider {
  /**
   * Get the full URL for a media file
   * @param mediaType - Type of media (items, categories, etc.)
   * @param filename - Name of the file (e.g., "123.png", "beverages.mp4")
   * @returns Full URL or path to the media file
   */
  getMediaUrl(mediaType: MediaType, filename: string): string;

  /**
   * Get the base URL for a specific media type
   * @param mediaType - Type of media
   * @returns Base URL/path for this media type
   */
  getBasePath(mediaType: MediaType): string;

  /**
   * Check if the provider is properly configured
   * @returns true if configuration is valid
   */
  isConfigured(): boolean;
}
