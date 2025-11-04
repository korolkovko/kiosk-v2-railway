// useSSEItemUpdates.ts
// React hook for managing SSE-based real-time item updates
// Updated to handle kopecks from backend

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent } from './sseService'
export interface SSEConnectionStatus {
  connected: boolean
  reconnecting: boolean
}

export interface ItemUpdateData {
  itemId: number
  isAvailable?: boolean
  promoted?: boolean
  stockQuantity?: number
  // For new items or property changes
  newItem?: boolean
  nameRu?: string
  nameEng?: string | null
  descriptionRu?: string
  descriptionEng?: string | null
  unitMeasure?: string
  foodCategory?: string
  // Price fields now in kopecks from backend
  priceNetKopecks?: number
  vatRate?: number | null
  vatAmountKopecks?: number
  priceGrossKopecks?: number
  // Legacy fields for backward compatibility (will be removed later)
  priceNet?: number
  vatAmount?: number
  priceGross?: number
}

export interface UseSSEItemUpdatesProps {
  onItemUpdate: (updatedItem: ItemUpdateData) => void
  onConnectionStatusChange?: (status: SSEConnectionStatus) => void
}

export function useSSEItemUpdates({ 
  onItemUpdate, 
  onConnectionStatusChange 
}: UseSSEItemUpdatesProps) {
  
  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    console.log('Received SSE event:', event)
    
    switch (event.event_type) {
      case 'ITEM_STATUS_CHANGED':
        onItemUpdate({
          itemId: event.item_id,
          isAvailable: event.is_active
        })
        break
        
      case 'ITEM_PROMOTION_CHANGED':
        onItemUpdate({
          itemId: event.item_id,
          promoted: event.promoted
        })
        break
        
      case 'ITEM_STOCK_CHANGED':
        onItemUpdate({
          itemId: event.item_id,
          stockQuantity: event.stock_quantity,
          isAvailable: event.stock_quantity > 0
        })
        break
        
      case 'ITEM_CREATED':
        onItemUpdate({
          itemId: event.item_id,
          newItem: true,
          nameRu: event.name_ru,
          nameEng: event.name_eng,
          descriptionRu: event.description_ru,
          descriptionEng: event.description_eng,
          unitMeasure: event.unit_measure_name_eng,
          foodCategory: event.food_category_name,
          // Backend now sends kopecks, parse as integers
          priceNetKopecks: parseInt(event.price_net_kopecks),
          vatRate: event.vat_rate ? parseFloat(event.vat_rate) : null,
          vatAmountKopecks: parseInt(event.vat_amount_kopecks),
          priceGrossKopecks: parseInt(event.price_gross_kopecks),
          promoted: event.promoted,
          stockQuantity: event.stock_quantity,
          isAvailable: event.is_active && event.stock_quantity > 0
        })
        break
        
      case 'ITEM_PROPERTIES_CHANGED':
        onItemUpdate({
          itemId: event.item_id,
          nameRu: event.name_ru,
          nameEng: event.name_eng,
          descriptionRu: event.description_ru,
          descriptionEng: event.description_eng,
          unitMeasure: event.unit_measure_name_eng,
          foodCategory: event.food_category_name,
          // Backend now sends kopecks, parse as integers
          priceNetKopecks: parseInt(event.price_net_kopecks),
          vatRate: event.vat_rate ? parseFloat(event.vat_rate) : null,
          vatAmountKopecks: parseInt(event.vat_amount_kopecks),
          priceGrossKopecks: parseInt(event.price_gross_kopecks)
        })
        break
        
      default:
        console.warn('Unknown SSE event type:', event)
    }
  }, [onItemUpdate])

  const handleConnectionStatus = useCallback((connected: boolean) => {
    if (onConnectionStatusChange) {
      onConnectionStatusChange({
        connected,
        reconnecting: !connected && sseService.isConnected()
      })
    }
  }, [onConnectionStatusChange])

  useEffect(() => {
    // NOTE: Connection lifecycle is managed by AuthContext (login/init/logout)
    // This hook only subscribes to events - no connect() call needed here

    // Set up event handlers
    sseService.onEvent('ITEM_STATUS_CHANGED', handleSSEEvent)
    sseService.onEvent('ITEM_PROMOTION_CHANGED', handleSSEEvent)
    sseService.onEvent('ITEM_STOCK_CHANGED', handleSSEEvent)
    sseService.onEvent('ITEM_CREATED', handleSSEEvent)
    sseService.onEvent('ITEM_PROPERTIES_CHANGED', handleSSEEvent)
    sseService.onConnectionStatus(handleConnectionStatus)

    // Cleanup on unmount
    return () => {
      // Note: We don't disconnect the SSE service here since it's shared globally
      // The connection persists across component remounts (important for React.StrictMode)
    }
  }, [handleSSEEvent, handleConnectionStatus])

  return {
    isConnected: sseService.isConnected(),
    disconnect: () => sseService.disconnect(),
    reconnect: () => sseService.connect()
  }
}