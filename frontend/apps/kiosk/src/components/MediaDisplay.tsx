// File: src/components/MediaDisplay.tsx
//
// Purpose:
// Media display component that reads from IndexedDB cache.
// NO network requests during session - instant media display.
//
// Architecture:
// - Reads from IndexedDB cache (populated on login)
// - Shows placeholder if media not cached
// - Zero network overhead during navigation

import { FunctionComponent, useState, useEffect } from 'react'
import { mediaCacheService } from '../services/mediaCache.service'

export type MediaDisplayType = {
  cacheKey: string  // e.g., "category_NEW" or "item_8"
  alt: string
  className?: string
  loading?: 'lazy' | 'eager'
}

const MediaDisplay: FunctionComponent<MediaDisplayType> = ({
  cacheKey,
  alt,
  className = '',
  loading = 'lazy'
}) => {
  const [mediaUrl, setMediaUrl] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let blobUrl: string | null = null

    const loadMedia = async () => {
      setIsLoading(true)
      console.log(`🔍 MediaDisplay: Loading cache key "${cacheKey}"`)

      try {
        // Get media entry from IndexedDB
        const entry = await mediaCacheService.getMediaEntry(cacheKey)

        if (entry) {
          console.log(`✅ MediaDisplay: Found cached ${entry.type} for "${cacheKey}" (${entry.blob.size} bytes)`)
          // Create blob URL from cached blob
          blobUrl = URL.createObjectURL(entry.blob)
          setMediaUrl(blobUrl)
          setMediaType(entry.type)
          console.log(`🎬 MediaDisplay: Created blob URL for "${cacheKey}":`, blobUrl)
        } else {
          console.warn(`⚠️  MediaDisplay: Media not cached: ${cacheKey}`)
          setMediaUrl(null)
          setMediaType(null)
        }
      } catch (error) {
        console.error(`❌ MediaDisplay: Failed to load media ${cacheKey}:`, error)
        setMediaUrl(null)
        setMediaType(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadMedia()

    // Cleanup: Revoke blob URL when component unmounts or cacheKey changes
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl)
      }
    }
  }, [cacheKey])

  // Loading state
  if (isLoading) {
    return (
      <div className={`${className} flex items-center justify-center bg-[#1a1a1a]`}>
        <div className="text-[#666] text-[1.5rem]">Loading...</div>
      </div>
    )
  }

  // Not cached - show placeholder
  if (!mediaUrl) {
    return (
      <div className={`${className} flex items-center justify-center bg-[#1a1a1a]`}>
        <div className="text-[#666] text-[1.5rem] text-center px-[2rem]">
          {alt}
          <div className="text-[1rem] mt-[1rem] text-[#444]">
            Media not cached
          </div>
        </div>
      </div>
    )
  }

  // Render video
  if (mediaType === 'video') {
    return (
      <video
        className={className}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
      >
        <source src={mediaUrl} type="video/mp4" />
        {alt}
      </video>
    )
  }

  // Render image
  return (
    <img
      className={className}
      loading={loading}
      alt={alt}
      src={mediaUrl}
    />
  )
}

export default MediaDisplay
