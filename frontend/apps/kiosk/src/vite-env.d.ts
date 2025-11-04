/// <reference types="vite/client" />

// Type definitions for environment variables
interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_URL?: string
  readonly VITE_WS_URL?: string

  // Storage Configuration
  readonly VITE_STORAGE_PROVIDER?: string
  readonly VITE_LOCAL_MEDIA_BASE_PATH?: string

  // Local Storage Paths
  readonly VITE_LOCAL_PATH_ITEMS?: string
  readonly VITE_LOCAL_PATH_CATEGORIES_OPEN?: string
  readonly VITE_LOCAL_PATH_CATEGORIES_SORRY?: string
  readonly VITE_LOCAL_PATH_CATEGORIES_PROMOTED?: string
  readonly VITE_LOCAL_PATH_SCREENSAVER?: string
  readonly VITE_LOCAL_PATH_ORDER_HANDLING?: string
  readonly VITE_LOCAL_PATH_SERVICE_MODE?: string
  readonly VITE_LOCAL_PATH_FABRIC?: string

  // S3 Storage Configuration
  readonly VITE_S3_ENDPOINT?: string
  readonly VITE_S3_BUCKET?: string
  readonly VITE_S3_REGION?: string
  readonly VITE_S3_ACCESS_KEY_ID?: string
  readonly VITE_S3_SECRET_ACCESS_KEY?: string
  readonly VITE_S3_USE_SSL?: string

  // S3 Paths
  readonly VITE_S3_PATH_ITEMS?: string
  readonly VITE_S3_PATH_CATEGORIES_OPEN?: string
  readonly VITE_S3_PATH_CATEGORIES_SORRY?: string
  readonly VITE_S3_PATH_CATEGORIES_PROMOTED?: string
  readonly VITE_S3_PATH_SCREENSAVER?: string
  readonly VITE_S3_PATH_ORDER_HANDLING?: string
  readonly VITE_S3_PATH_SERVICE_MODE?: string
  readonly VITE_S3_PATH_FABRIC?: string

  // Named Media Lists
  readonly VITE_SERVICE_MODE_MEDIA_NAMES?: string
  readonly VITE_SCREENSAVER_MEDIA_NAMES?: string
  readonly VITE_ORDER_HANDLING_MEDIA_NAMES?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
