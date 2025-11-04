// File: src/hooks/useGetAvailableItems.ts
//
// Purpose:
// Thin React hook over the Get Available Items service.
// No transport or business logic; only manages UI-ready state and refetch.
// Returns ViewModels to be used directly by components/pages.
// Handles conversion from backend kopecks to frontend ruble display

import { useEffect, useState, useCallback, useMemo } from 'react'
import type { AvailableItemVM } from '../models/view/availableItem.vm'
import { getAvailableItemsVM } from '../services/getAvailableItems.service'
import { getItemDetailVM } from '../services/getItemDetail.service'
import { useSSEItemUpdates, type ItemUpdateData, type SSEConnectionStatus } from '../SSESubscription/useSSEItemUpdates'
import { getAccessToken, refreshAccessToken, ApiError } from '../api/apiHttpClient'
import { usePersistedState, PERSISTENCE_CONFIGS } from './usePersistedState'
import { useNavigate } from 'react-router-dom'

/**
 * isItemVisibleAtTime
 * Check if an item should be visible based on current time and its time restrictions.
 * Items with null start_at/end_at are visible all day.
 */
function isItemVisibleAtTime(item: AvailableItemVM, currentTime: Date): boolean {
  // If no time restrictions, item is visible all day
  if (!item.startAt && !item.endAt) {
    return true
  }

  const now = currentTime.getHours() * 60 + currentTime.getMinutes() // Convert to minutes since midnight

  // Parse time strings (HH:MM:SS format) to minutes since midnight
  const parseTimeToMinutes = (timeStr: string | null): number | null => {
    if (!timeStr) return null
    const [hours, minutes] = timeStr.split(':').map(Number)
    return hours * 60 + minutes
  }

  const startMinutes = parseTimeToMinutes(item.startAt)
  const endMinutes = parseTimeToMinutes(item.endAt)

  // If only start_at is set, visible from start_at onwards
  if (startMinutes !== null && endMinutes === null) {
    return now >= startMinutes
  }

  // If only end_at is set, visible until end_at
  if (startMinutes === null && endMinutes !== null) {
    return now <= endMinutes
  }

  // Both start_at and end_at are set
  if (startMinutes !== null && endMinutes !== null) {
    return now >= startMinutes && now <= endMinutes
  }

  return true
}

/**
 * UseGetAvailableItemsResult
 * Public shape returned by the hook for consumption in UI.
 */
export interface UseGetAvailableItemsResult {
  items: AvailableItemVM[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  connectionStatus: SSEConnectionStatus
}

/**
 * useGetAvailableItems()
 * Fetch and manage the list of available menu items for kiosk UI consumption.
 * Items are persisted to localStorage with 4-hour TTL for Amazon-like persistence.
 */
export function useGetAvailableItems(): UseGetAvailableItemsResult {
  const navigate = useNavigate()
  
  // Use persisted state for items (localStorage, 4 hour TTL)
  const [items, setItems] = usePersistedState<AvailableItemVM[]>(
    'kiosk_items',
    [],
    PERSISTENCE_CONFIGS.ITEMS
  )

  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<SSEConnectionStatus>({
    connected: false,
    reconnecting: false
  })

  /**
   * fetchItems()
   * Call service and update local state; resets error on retry.
   */
  const fetchItems = async () => {
    try {
      console.log('🔄 useGetAvailableItems: Starting to fetch items...')
      setLoading(true)
      setError(null)
      const data = await getAvailableItemsVM()
      console.log('✅ useGetAvailableItems: Items fetched successfully:', data.length, 'items', data)
      setItems(data)
      console.log('📦 useGetAvailableItems: State updated with items')
    } catch (err) {
      console.error('❌ useGetAvailableItems: Failed to fetch items:', err)
      
      // Handle authentication errors with silent redirect
      if (err instanceof ApiError && (err.type === 'unauthorized' || err.status === 401 || err.status === 403)) {
        console.log('🔐 useGetAvailableItems: Authentication failed, redirecting to login...')
        navigate('/login', { replace: true })
        return // Don't set error state, just redirect
      }
      
      setError(err instanceof Error ? err : new Error('Failed to load available items'))
    } finally {
      setLoading(false)
      console.log('🏁 useGetAvailableItems: Fetch completed')
    }
  }

  // Handle real-time item updates from SSE
  const handleItemUpdate = useCallback(async (updateData: ItemUpdateData) => {
    console.log('📡 SSE Item Update Received:', updateData)
    
    setItems(currentItems => {
      // Handle new item creation
      if (updateData.newItem) {
        // Convert kopecks to rubles for display (backend now sends kopecks)
        const priceGrossRubles = (updateData.priceGrossKopecks || 0) / 100
        const priceNetRubles = (updateData.priceNetKopecks || 0) / 100
        
        const newItem: AvailableItemVM = {
          itemId: updateData.itemId,
          nameRu: updateData.nameRu!,
          nameEng: updateData.nameEng ?? null,
          descriptionRu: updateData.descriptionRu!,
          descriptionEng: updateData.descriptionEng ?? null,
          unitMeasure: updateData.unitMeasure!,
          foodCategory: updateData.foodCategory!,
          priceGrossDisplay: `${priceGrossRubles.toFixed(2)} ₽`,
          priceNetDisplay: `${priceNetRubles.toFixed(2)} ₽`,
          vatRateDisplay: updateData.vatRate !== null && updateData.vatRate !== undefined ? `${updateData.vatRate.toFixed(0)}%` : null,
          priceGross: priceGrossRubles,
          priceNet: priceNetRubles,
          vatRate: updateData.vatRate ?? null,
          promoted: updateData.promoted!,
          stockQuantity: updateData.stockQuantity!,
          isAvailable: updateData.isAvailable!,
          displayOrder: 0, // SSE updates don't include menu info, will be fetched from backend
          startAt: null,
          endAt: null,
          posterPath: `/items picture/${updateData.itemId}`
        }
        return [...currentItems, newItem]
      }
      
      // Check if item exists in current list
      const existingItemIndex = currentItems.findIndex(item => item.itemId === updateData.itemId)
      
      if (existingItemIndex >= 0) {
        // Handle existing item updates
        return currentItems.map(item => {
          if (item.itemId === updateData.itemId) {
            const updatedItem = { ...item }
            
            // Update basic properties
            if (updateData.isAvailable !== undefined) updatedItem.isAvailable = updateData.isAvailable
            if (updateData.promoted !== undefined) updatedItem.promoted = updateData.promoted
            if (updateData.stockQuantity !== undefined) {
              updatedItem.stockQuantity = updateData.stockQuantity
              // Update availability based on stock quantity
              updatedItem.isAvailable = updateData.stockQuantity > 0 && updatedItem.isAvailable
            }
            
            // Update detailed properties if provided
            if (updateData.nameRu !== undefined) updatedItem.nameRu = updateData.nameRu
            if (updateData.nameEng !== undefined) updatedItem.nameEng = updateData.nameEng
            if (updateData.descriptionRu !== undefined) updatedItem.descriptionRu = updateData.descriptionRu
            if (updateData.descriptionEng !== undefined) updatedItem.descriptionEng = updateData.descriptionEng
            if (updateData.unitMeasure !== undefined) updatedItem.unitMeasure = updateData.unitMeasure
            if (updateData.foodCategory !== undefined) updatedItem.foodCategory = updateData.foodCategory
            
            // Update price properties and recalculate display strings (convert kopecks to rubles)
            if (updateData.priceGrossKopecks !== undefined) {
              const priceGrossRubles = updateData.priceGrossKopecks / 100
              updatedItem.priceGross = priceGrossRubles
              updatedItem.priceGrossDisplay = `${priceGrossRubles.toFixed(2)} ₽`
            }
            if (updateData.priceNetKopecks !== undefined) {
              const priceNetRubles = updateData.priceNetKopecks / 100
              updatedItem.priceNet = priceNetRubles
              updatedItem.priceNetDisplay = `${priceNetRubles.toFixed(2)} ₽`
            }
            if (updateData.vatRate !== undefined) {
              updatedItem.vatRate = updateData.vatRate
              updatedItem.vatRateDisplay = updateData.vatRate !== null ? `${updateData.vatRate.toFixed(0)}%` : null
            }
            
            return updatedItem
          }
          return item
        }).filter(item => {
          // Remove items that have 0 stock (became unavailable)
          if (item.itemId === updateData.itemId && updateData.stockQuantity !== undefined && updateData.stockQuantity <= 0) {
            console.log(`🗑️ SSE: Removing item ${item.itemId} from list (stock = ${updateData.stockQuantity})`)
            return false
          }
          return true
        })
      } else {
        // Item not in current list - fetch it from backend if it now has stock
        if (updateData.stockQuantity && updateData.stockQuantity > 0) {
          console.log(`🔍 SSE: Item ${updateData.itemId} not in current list but has stock. Fetching details...`)
          
          // Fetch item details asynchronously and add to list
          getItemDetailVM(updateData.itemId)
            .then(newItem => {
              console.log(`✅ SSE: Successfully fetched item ${updateData.itemId}, adding to list`)
              setItems(prevItems => {
                // Double-check item isn't already added by another update
                if (prevItems.some(item => item.itemId === updateData.itemId)) {
                  return prevItems
                }
                return [...prevItems, newItem]
              })
            })
            .catch(error => {
              // Handle 404 silently - item not in active menu
              if (error instanceof ApiError && error.status === 404) {
                console.log(`ℹ️ SSE: Item ${updateData.itemId} not available in current menu (404), ignoring`)
                return
              }
              console.error(`❌ SSE: Failed to fetch item ${updateData.itemId}:`, error)
            })
        }
        
        // Return current items unchanged for now (async fetch will update later)
        return currentItems
      }
    })
  }, [])

  // Handle SSE connection status changes
  const handleConnectionStatusChange = useCallback((status: SSEConnectionStatus) => {
    setConnectionStatus(status)
  }, [])

  // Set up SSE for real-time updates
  useSSEItemUpdates({
    onItemUpdate: handleItemUpdate,
    onConnectionStatusChange: handleConnectionStatusChange
  })

  // Initial load - try to refresh token if needed, then fetch items
  useEffect(() => {
    const loadItemsWithAuthCheck = async () => {
      let token = getAccessToken()
      
      // If no access token, try to refresh using stored refresh token
      if (!token) {
        try {
          console.log('🔄 useGetAvailableItems: No access token, attempting refresh...')
          await refreshAccessToken()
          token = getAccessToken()
          console.log('✅ useGetAvailableItems: Token refreshed successfully')
        } catch (error) {
          console.log('⏭️ useGetAvailableItems: Token refresh failed, checking if redirect needed:', error)
          
          // If refresh fails due to invalid/expired refresh token, redirect to login
          if (error instanceof ApiError && (error.type === 'unauthorized' || error.status === 401)) {
            console.log('🔐 useGetAvailableItems: Refresh token invalid, redirecting to login...')
            navigate('/login', { replace: true })
          }
          return
        }
      }
      
      if (token) {
        console.log('🔐 useGetAvailableItems: Auth token available, fetching items...')
        fetchItems()
      }
    }
    
    loadItemsWithAuthCheck()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Debug: log when items state changes
  useEffect(() => {
    console.log('🔍 useGetAvailableItems: Items state changed:', items.length, 'items')
  }, [items])

  // State for triggering time-based filtering re-evaluation
  const [currentTime, setCurrentTime] = useState<Date>(new Date())

  // Check every minute if items should appear/disappear based on time
  useEffect(() => {
    const intervalId = setInterval(() => {
      setCurrentTime(new Date())
    }, 60000) // 60 seconds

    return () => clearInterval(intervalId)
  }, [])

  // Filter items by time and sort by displayOrder
  const visibleItems = useMemo(() => {
    console.log('🔄 Filtering and sorting items by time and displayOrder...')

    // First, filter by time visibility
    const timeFilteredItems = items.filter(item => isItemVisibleAtTime(item, currentTime))

    console.log(`✅ Time filtering: ${items.length} -> ${timeFilteredItems.length} items visible at ${currentTime.toTimeString()}`)

    // Then, sort by displayOrder (ascending)
    const sortedItems = [...timeFilteredItems].sort((a, b) => a.displayOrder - b.displayOrder)

    return sortedItems
  }, [items, currentTime])

  return {
    items: visibleItems,
    loading,
    error,
    refetch: fetchItems,
    connectionStatus,
  }
}
