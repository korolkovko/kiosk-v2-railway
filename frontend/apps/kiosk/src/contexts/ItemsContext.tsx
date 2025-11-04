// File: src/contexts/ItemsContext.tsx
//
// Purpose:
// Items context to centralize items state management.
// Single source of truth for available items - fetched once, updated via SSE.
// Prevents multiple API calls and multiple SSE connections.

import { createContext, useContext, ReactNode } from 'react'
import { useGetAvailableItems, type UseGetAvailableItemsResult } from '../hooks/useGetAvailableItems'

type ItemsContextType = UseGetAvailableItemsResult

const ItemsContext = createContext<ItemsContextType | undefined>(undefined)

export const ItemsProvider = ({ children }: { children: ReactNode }) => {
  // Single instance of useGetAvailableItems hook
  // Fetches items once on mount, then updates via SSE
  const itemsData = useGetAvailableItems()

  return (
    <ItemsContext.Provider value={itemsData}>
      {children}
    </ItemsContext.Provider>
  )
}

export const useItems = (): ItemsContextType => {
  const context = useContext(ItemsContext)
  if (!context) {
    throw new Error('useItems must be used within ItemsProvider')
  }
  return context
}
