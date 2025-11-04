// File: src/services/imagePreloader.service.ts
//
// Purpose:
// Media preloading service for smooth kiosk navigation.
// Preloads category posters (images/videos) and item images to avoid loading delays.
// Uses auto-detection to find correct file extension.

import { MEDIA_EXTENSIONS } from './posterLogic.service'

/**
 * Try to preload media with auto-detection of file extension
 * Returns true if media was found and preloaded
 */
async function preloadMediaWithAutoDetect(basePath: string): Promise<boolean> {
  // Try each extension until we find one that exists
  for (const ext of MEDIA_EXTENSIONS) {
    const fullPath = `${basePath}${ext}`

    try {
      const response = await fetch(fullPath, { method: 'HEAD' })

      // Check Content-Type to ensure it's actually a media file (not HTML fallback)
      const contentType = response.headers.get('content-type') || ''
      const isActualMedia =
        contentType.startsWith('image/') ||
        contentType.startsWith('video/') ||
        contentType.includes('octet-stream')

      if (response.ok && isActualMedia) {
        // Found the file - now preload it properly
        const isVideo = ['.mp4', '.webm', '.mov'].includes(ext.toLowerCase())

        if (isVideo) {
          // Preload video
          const video = document.createElement('video')
          video.preload = 'auto'
          video.src = fullPath
          await new Promise((resolve) => {
            video.onloadeddata = () => resolve(true)
            video.onerror = () => resolve(false)
          })
        } else {
          // Preload image
          const img = new Image()
          await new Promise((resolve) => {
            img.onload = () => resolve(true)
            img.onerror = () => resolve(false)
            img.src = fullPath
          })
        }

        console.log(`✅ Preloaded: ${fullPath}`)
        return true
      }
    } catch (err) {
      // Continue to next extension
      continue
    }
  }

  console.warn(`⚠️ Media not found for: ${basePath}`)
  return false
}

/**
 * Preload multiple media files concurrently
 */
async function preloadMediaFiles(basePaths: string[]): Promise<void> {
  const results = await Promise.all(basePaths.map(preloadMediaWithAutoDetect))
  const successCount = results.filter(Boolean).length
  console.log(`✅ Media preloaded successfully: ${successCount}/${basePaths.length}`)
}

/**
 * Get all category poster base paths (without extensions)
 * Auto-detection will find .mp4, .webm, .png, .jpg, etc.
 */
function getCategoryPosterBasePaths(): string[] {
  return [
    '/categories picture/promoted',
    '/categories picture/foodposter',
    '/categories picture/foodposterssory',
    '/categories picture/drinksposter',
    '/categories picture/drinksposterssory',
    '/categories picture/sidesposter',
    '/categories picture/sidesposterssory'
  ]
}

/**
 * Get item image paths (numbered 1-12 based on available files)
 */
function getItemImagePaths(): string[] {
  const itemPaths = []
  for (let i = 1; i <= 12; i++) {
    itemPaths.push(`/items picture/${i}.png`)
  }
  return itemPaths
}

/**
 * Preload all category posters for smooth navigation
 */
export async function preloadCategoryPosters(): Promise<void> {
  const posterBasePaths = getCategoryPosterBasePaths()
  await preloadMediaFiles(posterBasePaths)
}

/**
 * Preload all item images for smooth display
 */
export async function preloadItemImages(): Promise<void> {
  const itemPaths = getItemImagePaths()
  // Item images still use exact paths (no auto-detection needed for now)
  const results = await Promise.all(
    itemPaths.map(path =>
      new Promise((resolve) => {
        const img = new Image()
        img.onload = () => resolve(true)
        img.onerror = () => resolve(false)
        img.src = path
      })
    )
  )
  const successCount = results.filter(Boolean).length
  console.log(`✅ Item images preloaded: ${successCount}/${itemPaths.length}`)
}

/**
 * Preload all kiosk media (category posters + item images)
 */
export async function preloadAllKioskImages(): Promise<void> {
  console.log('🖼️ Starting media preloading (images + videos)...')

  try {
    await Promise.all([preloadCategoryPosters(), preloadItemImages()])
    console.log('✅ All kiosk media preloaded successfully')
  } catch (error) {
    console.warn('⚠️ Media preloading completed with some errors:', error)
  }
}

/**
 * Initialize image preloading on app start
 * Call this from App.tsx or main component
 */
export function initializeImagePreloading(): void {
  // Start preloading in background without blocking UI
  setTimeout(() => {
    preloadAllKioskImages()
  }, 1000) // Delay to let initial UI render first
}