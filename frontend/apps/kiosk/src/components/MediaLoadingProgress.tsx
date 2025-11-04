// File: src/components/MediaLoadingProgress.tsx
//
// Purpose:
// Progress bar component shown during media cache download on login.
// Displays:
// - Current progress (e.g., "Loading 47/123 (38%)")
// - Current item being downloaded
// - Storage quota status
//
// Shown in full-screen overlay until all media is cached.

import { FunctionComponent } from 'react'

export interface MediaLoadingProgressProps {
  current: number
  total: number
  currentItem: string
  quotaUsed: number // bytes
  quotaAvailable: number // bytes
}

const MediaLoadingProgress: FunctionComponent<MediaLoadingProgressProps> = ({
  current,
  total,
  currentItem,
  quotaUsed,
  quotaAvailable
}) => {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0
  const quotaUsedMB = Math.round(quotaUsed / 1024 / 1024)
  const quotaTotalMB = Math.round((quotaUsed + quotaAvailable) / 1024 / 1024)

  // ASCII progress bar (50 characters wide)
  const barWidth = 50
  const filledWidth = Math.round((percentage / 100) * barWidth)
  const emptyWidth = barWidth - filledWidth
  const progressBar = `[${'█'.repeat(filledWidth)}${' '.repeat(emptyWidth)}]`

  return (
    <div className="fixed inset-0 z-[10000] bg-black flex flex-col items-center justify-center select-none overflow-hidden">
      {/* Optional: CRT scanlines effect */}
      <div className="absolute inset-0 pointer-events-none scanlines opacity-20" />

      {/* Main content */}
      <div className="flex flex-col items-center gap-[2rem]">
        {/* Logo */}
        <div className="mb-[2rem]">
          <h1 className="text-[3rem] font-mono text-[#c0c0c0]">
            Zero Culture®
          </h1>
        </div>

        {/* Main progress info */}
        <div className="text-center">
          <div className="text-[2rem] font-mono text-[#c0c0c0] mb-[1rem]">
            Loading media...
          </div>
          <div className="text-[1.5rem] font-mono text-[#c0c0c0]">
            <span className="text-[#ffff00] font-bold">{current}</span> / <span className="text-[#ffff00] font-bold">{total}</span> (<span className="text-[#ffff00] font-bold">{percentage}%</span>)
          </div>
        </div>

        {/* ASCII Progress bar */}
        <div className="text-[1.5rem] font-mono text-[#c0c0c0] tracking-wider">
          {progressBar}
        </div>

        {/* Current item */}
        <div className="text-[1.25rem] font-mono text-[#c0c0c0] text-center max-w-[50rem] truncate">
          {currentItem}
        </div>

        {/* Storage quota info */}
        <div className="text-[1.25rem] font-mono text-[#c0c0c0] text-center">
          <div>Storage: <span className="text-[#ffff00]">{quotaUsedMB} MB</span> / {quotaTotalMB} MB</div>
          <div className="mt-[0.5rem]">
            {quotaTotalMB < 1024 && (
              <span className="text-[#ff0000]">
                [!] Low storage available
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MediaLoadingProgress
