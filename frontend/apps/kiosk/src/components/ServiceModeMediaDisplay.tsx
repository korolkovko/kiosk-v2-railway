// ServiceModeMediaDisplay.tsx
//
// Purpose:
// Dedicated media display component for Service Mode.
// Mirrors MediaDisplay behavior but loads media by service-specific cache key "service_<name>"
// from IndexedDB via mediaCacheService. If media is missing or pictureName is null, shows a
// clear fallback text "Service mode" as requested. No network requests here during session.
//
// Notes:
// - Under the hood, media is preloaded at login or fetched on-demand before activation.
// - This component only reads from cache and renders the proper element.

import { FunctionComponent, useEffect, useState } from 'react'
import { mediaCacheService } from '../services/mediaCache.service'

export type ServiceModeMediaDisplayProps = {
  pictureName: string | null
  className?: string
}

/**
 * ServiceModeMediaDisplay
 * Renders video or image for a given service-mode logical name from cache.
 * Falls back to a text banner when no media available or name is null.
 */
const ServiceModeMediaDisplay: FunctionComponent<ServiceModeMediaDisplayProps> = ({
  pictureName,
  className = ''
}) => {
  const [mediaUrl, setMediaUrl] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<'image' | 'video' | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    let blobUrl: string | null = null
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setMediaUrl(null)
      setMediaType(null)

      try {
        if (!pictureName) {
          // No name provided - fallback to text
          setIsLoading(false)
          return
        }

        const entry = await mediaCacheService.getServiceModeMediaEntry(pictureName)
        if (cancelled) return

        if (entry) {
          blobUrl = URL.createObjectURL(entry.blob)
          setMediaUrl(blobUrl)
          setMediaType(entry.type)
        } else {
          // Not cached - let caller ensure caching beforehand; we show fallback text
          setMediaUrl(null)
          setMediaType(null)
        }
      } catch (error) {
        console.error('ServiceModeMediaDisplay: failed to load media:', error)
        setMediaUrl(null)
        setMediaType(null)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    load()

    return () => {
      cancelled = true
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl)
      }
    }
  }, [pictureName])

  // Loading state - keep UI simple and quiet
  if (isLoading) {
    return (
      <div className={`w-full h-full flex items-center justify-center bg-black ${className}`}>
        <div className="text-[2rem] font-mono text-[#c0c0c0]">Loading service mode…</div>
      </div>
    )
  }

  // Fallback text when no media or no name
  if (!mediaUrl || !mediaType) {
    return (
      <div className={`w-full h-full flex items-center justify-center bg-black ${className}`}>
        <div className="text-[4rem] font-mono text-[#c0c0c0] uppercase tracking-wide">
          Service mode
        </div>
      </div>
    )
  }

  // Render video
  if (mediaType === 'video') {
    return (
      <video
        className={`w-full h-full object-cover ${className}`}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
      >
        <source src={mediaUrl} type="video/mp4" />
        Service mode
      </video>
    )
  }

  // Render image
  return (
    <img
      className={`w-full h-full object-cover ${className}`}
      alt="Service mode"
      src={mediaUrl}
    />
  )
}

export default ServiceModeMediaDisplay