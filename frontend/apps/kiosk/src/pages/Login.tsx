// File: src/pages/Login.tsx
//
// Purpose:
// Login page for kiosk. Collects user credentials, delegates auth to context/service,
// and renders user-friendly errors. Contains no transport or business logic.
//
// Architecture:
// 1. Authenticate user
// 2. Clear old media cache
// 3. Download ALL media (categories + items) into IndexedDB
// 4. Show progress bar during download
// 5. Navigate to main screen when complete
import { FunctionComponent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useItems } from '../contexts/ItemsContext'
import { AuthError } from '../api/authApi'
import { mediaCacheService, type DownloadProgress } from '../services/mediaCache.service'
import { getAllMenuItemsForPreload } from '../api/getAllMenuItemsForPreload.api'
import MediaLoadingProgress from '../components/MediaLoadingProgress'
import { getKioskServiceModeStatusForSelf } from '../api/serviceMode.api'
import { useServiceModeStore } from '../stores/ServiceModeStore'

export const Login: FunctionComponent = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { refetch: refetchItems } = useItems()
  const { activate: activateServiceMode } = useServiceModeStore()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [errorType, setErrorType] = useState<'network' | 'unauthorized' | 'server' | 'unknown' | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Media download state
  const [isDownloadingMedia, setIsDownloadingMedia] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null)

  const handleSubmit = async () => {
    // Clear previous errors
    setError(null)
    setErrorType(null)

    // Validate inputs
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password')
      setErrorType('unauthorized')
      return
    }

    setIsLoading(true)

    try {
      // Step 1: Authenticate
      await login({ username, password })

      // Service Mode: read current status early to build preload set
      let serviceModeStatus: { is_service_mode: boolean; service_picture_name: string | null } | null = null
      try {
        serviceModeStatus = await getKioskServiceModeStatusForSelf()
        console.log('🛠️ Service mode status at login:', serviceModeStatus)
      } catch (e) {
        console.warn('⚠️ Failed to fetch service mode status at login, proceeding without it', e)
        serviceModeStatus = null
      }

      // Step 2: Clear old media cache
      console.log('🧹 Clearing old media cache...')
      await mediaCacheService.clearAll()

      // Step 3: Fetch ALL items and categories from menu for preloading
      console.log('📡 Fetching all menu items and categories for preload...')
      const menuData = await getAllMenuItemsForPreload()

      // Step 4: Download all media
      setIsLoading(false)
      setIsDownloadingMedia(true)

      // First, preload named baseline assets from env lists (screensaver, order handling, service mode)
      await mediaCacheService.downloadAllScreensaverMediaAtLogin((progress) => {
        setDownloadProgress(progress)
      })
      await mediaCacheService.downloadAllOrderHandlingMediaAtLogin((progress) => {
        setDownloadProgress(progress)
      })
      await mediaCacheService.downloadAllServiceModeMediaAtLogin(
        serviceModeStatus?.service_picture_name ? [serviceModeStatus.service_picture_name] : [],
        (progress) => {
          setDownloadProgress(progress)
        }
      )

      console.log('📥 Starting media download...')

      // Get category names and item IDs from menu
      // Backend now includes synthetic promoted category in category_names at [0]
      const categoryNames = menuData.category_names
      const itemIds = menuData.item_ids

      // Synthetic promoted category is always first in the array
      const syntheticPromotedCategoryName = categoryNames[0] || 'promoted'

      console.log(`📋 Categories to download: ${categoryNames.length}`)
      console.log(`📋 Items to download: ${itemIds.length}`)
      console.log(`📋 Category names (with synthetic promoted):`, categoryNames)
      console.log(`📋 Synthetic promoted category: ${syntheticPromotedCategoryName}`)
      console.log(`📋 Item IDs:`, itemIds)

      await mediaCacheService.downloadAllMedia(
        categoryNames,
        itemIds,
        syntheticPromotedCategoryName,
        (progress) => {
          setDownloadProgress(progress)
        }
      )

      console.log('✅ Media download complete!')

      // Step 5: Trigger items refetch (now that we have token) and navigate
      console.log('🔄 Triggering items refetch...')
      await refetchItems()

      if (serviceModeStatus?.is_service_mode) {
        // Activate service mode in store before navigating
        console.log('🛠️ Activating service mode with picture:', serviceModeStatus.service_picture_name)
        activateServiceMode(serviceModeStatus.service_picture_name)
        navigate('/service-mode')
      } else {
        navigate('/main')
      }

    } catch (err: any) {
      // Reset states
      setIsDownloadingMedia(false)
      setDownloadProgress(null)

      // Check if it's a quota error
      if (err.message?.includes('QUOTA_EXCEEDED')) {
        setError('Storage full! Cannot download media. Please free up disk space and try again.')
        setErrorType('server')
      } else if (err instanceof AuthError) {
        setError(err.message)
        setErrorType(err.type)
      } else {
        setError(err.message || 'Login failed')
        setErrorType('unknown')
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Show media loading progress
  if (isDownloadingMedia && downloadProgress) {
    return (
      <MediaLoadingProgress
        current={downloadProgress.current}
        total={downloadProgress.total}
        currentItem={downloadProgress.currentItem}
        quotaUsed={downloadProgress.quotaUsed}
        quotaAvailable={downloadProgress.quotaAvailable}
      />
    )
  }

  return (
    <div className="w-full relative bg-[#fff] h-[922px] flex flex-col items-center justify-center py-[386px] px-5 box-border gap-5 text-center text-[42px] text-[#000] font-['DM_Sans']">
      <b className="self-stretch relative leading-10">
        <p className="m-0">Bequemunbequemlichkeit</p>
      </b>
      {error && (
        <div className={`flex items-center justify-center p-3 rounded-lg text-[17px] ${
          errorType === 'unauthorized' ? 'bg-red-100 text-red-700' :
          errorType === 'network' ? 'bg-yellow-100 text-yellow-700' :
          errorType === 'server' ? 'bg-orange-100 text-orange-700' :
          'bg-red-100 text-red-700'
        }`}>
          <span className="mr-2">
            {errorType === 'unauthorized' ? '🔒' :
             errorType === 'network' ? '🌐' :
             errorType === 'server' ? '🖥️' : '⚠️'}
          </span>
          {error}
        </div>
      )}
      <div className="w-full flex flex-row items-center justify-center flex-wrap content-center py-0 px-2.5 box-border gap-5 max-w-[600px] text-left text-[17px] text-[rgba(0,0,0,0.5)]">
        <input
          type="text"
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Username"
          className="flex-1 rounded-2xl bg-[rgba(0,0,0,0.08)] h-[50px] box-border min-w-[150px] py-[13.5px] px-[13px] outline-none"
        />
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Password"
          className="flex-1 rounded-2xl bg-[rgba(0,0,0,0.08)] h-[50px] box-border min-w-[150px] py-[13.5px] px-[13px] outline-none"
        />
        <button
          className={`flex-1 rounded-2xl ${isLoading ? 'bg-[#ff6666]' : 'bg-[#ff0000]'} flex flex-row items-center justify-center py-[13.5px] px-[13px] box-border min-w-[150px] cursor-pointer text-center text-[#000]`}
          onClick={handleSubmit}
          disabled={isLoading}
        >
          <div className="flex-1 relative leading-[135%] overflow-hidden text-ellipsis whitespace-nowrap">
            {isLoading ? 'Logging in...' : 'Goooo!'}
          </div>
        </button>
      </div>
    </div>
  )
}

export default Login
