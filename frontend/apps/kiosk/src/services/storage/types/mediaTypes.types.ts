/**
 * Media type categories for the kiosk application
 * Each type represents a different category of media assets
 */
export enum MediaType {
  /** Food and beverage item images */
  ITEMS = 'items',

  /** Category posters displayed when items are available */
  CATEGORIES_OPEN = 'categories_open',

  /** Category posters displayed when items are out of stock */
  CATEGORIES_SORRY = 'categories_sorry',

  /** Promoted/NEW category posters (special promotional content) */
  CATEGORIES_PROMOTED = 'categories_promoted',

  /** Screensaver media (backgrounds, videos for idle state) */
  SCREENSAVER = 'screensaver',

  /** Order handling page assets (thank you screens, payment processing) */
  ORDER_HANDLING = 'order_handling',

  /** Service mode assets (maintenance/cleaning/technical/closed) */
  SERVICE_MODE = 'service_mode',

  /** Generic UI assets (logos, backgrounds, patterns) */
  FABRIC = 'fabric',
}

/**
 * Supported media file extensions
 * Reduced to only .mp4 and .png for performance (fewer HTTP requests on login)
 */
export const MEDIA_EXTENSIONS = [
  '.mp4',   // Video format
  // '.webm',  // Commented out - not used
  '.png',   // Image format
  // '.jpg',   // Commented out - not used
  // '.jpeg',  // Commented out - not used
  // '.gif',   // Commented out - not used
  // '.webp'   // Commented out - not used
] as const;

export type MediaExtension = typeof MEDIA_EXTENSIONS[number];

/**
 * Helper to check if a file extension is supported
 */
export function isSupportedExtension(ext: string): ext is MediaExtension {
  return MEDIA_EXTENSIONS.includes(ext as MediaExtension);
}
