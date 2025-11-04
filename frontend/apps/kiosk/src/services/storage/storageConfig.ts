import { StorageConfig, StorageProviderType } from './types/storageProvider.types';
import { MediaType } from './types/mediaTypes.types';

/**
 * Reads storage configuration from environment variables
 * Supports both local filesystem and S3 storage
 */
export function loadStorageConfig(): StorageConfig {
  // Determine active provider
  const providerEnv = import.meta.env.VITE_STORAGE_PROVIDER || 'local';
  const provider = providerEnv === 's3' ? StorageProviderType.S3 : StorageProviderType.LOCAL;

  // Local filesystem configuration
  const localConfig = {
    basePath: import.meta.env.VITE_LOCAL_MEDIA_BASE_PATH || '/media',
    paths: {
      [MediaType.ITEMS]: import.meta.env.VITE_LOCAL_PATH_ITEMS || '/items',
      [MediaType.CATEGORIES_OPEN]: import.meta.env.VITE_LOCAL_PATH_CATEGORIES_OPEN || '/categories/open',
      [MediaType.CATEGORIES_SORRY]: import.meta.env.VITE_LOCAL_PATH_CATEGORIES_SORRY || '/categories/sorry',
      [MediaType.CATEGORIES_PROMOTED]: import.meta.env.VITE_LOCAL_PATH_CATEGORIES_PROMOTED || '/categories/promoted',
      [MediaType.SCREENSAVER]: import.meta.env.VITE_LOCAL_PATH_SCREENSAVER || '/screensaver',
      [MediaType.ORDER_HANDLING]: import.meta.env.VITE_LOCAL_PATH_ORDER_HANDLING || '/order_handling',
      [MediaType.SERVICE_MODE]: import.meta.env.VITE_LOCAL_PATH_SERVICE_MODE || '/service_mode',
      [MediaType.FABRIC]: import.meta.env.VITE_LOCAL_PATH_FABRIC || '/fabric',
    },
  };

  // S3 storage configuration
  const s3Config = {
    endpoint: import.meta.env.VITE_S3_ENDPOINT || '',
    bucket: import.meta.env.VITE_S3_BUCKET || '',
    region: import.meta.env.VITE_S3_REGION || 'us-east-1',
    accessKeyId: import.meta.env.VITE_S3_ACCESS_KEY_ID || '',
    secretAccessKey: import.meta.env.VITE_S3_SECRET_ACCESS_KEY || '',
    useSSL: import.meta.env.VITE_S3_USE_SSL !== 'false',
    paths: {
      [MediaType.ITEMS]: import.meta.env.VITE_S3_PATH_ITEMS || '/items',
      [MediaType.CATEGORIES_OPEN]: import.meta.env.VITE_S3_PATH_CATEGORIES_OPEN || '/categories/open',
      [MediaType.CATEGORIES_SORRY]: import.meta.env.VITE_S3_PATH_CATEGORIES_SORRY || '/categories/sorry',
      [MediaType.CATEGORIES_PROMOTED]: import.meta.env.VITE_S3_PATH_CATEGORIES_PROMOTED || '/categories/promoted',
      [MediaType.SCREENSAVER]: import.meta.env.VITE_S3_PATH_SCREENSAVER || '/screensaver',
      [MediaType.ORDER_HANDLING]: import.meta.env.VITE_S3_PATH_ORDER_HANDLING || '/order_handling',
      [MediaType.SERVICE_MODE]: import.meta.env.VITE_S3_PATH_SERVICE_MODE || '/service_mode',
      [MediaType.FABRIC]: import.meta.env.VITE_S3_PATH_FABRIC || '/fabric',
    },
  };

  return {
    provider,
    local: localConfig,
    s3: s3Config,
  };
}

/**
 * Singleton storage configuration instance
 */
export const storageConfig = loadStorageConfig();

/**
 * Log current storage configuration (useful for debugging)
 */
export function logStorageConfig(): void {
  console.log('[Storage Config] Active provider:', storageConfig.provider);

  if (storageConfig.provider === StorageProviderType.LOCAL) {
    console.log('[Storage Config] Local base path:', storageConfig.local.basePath);
    console.log('[Storage Config] Local paths:', storageConfig.local.paths);
  } else {
    console.log('[Storage Config] S3 endpoint:', storageConfig.s3.endpoint);
    console.log('[Storage Config] S3 bucket:', storageConfig.s3.bucket);
    console.log('[Storage Config] S3 region:', storageConfig.s3.region);
    console.log('[Storage Config] S3 paths:', storageConfig.s3.paths);
    console.log('[Storage Config] S3 credentials configured:', !!(storageConfig.s3.accessKeyId && storageConfig.s3.secretAccessKey));
  }
}
