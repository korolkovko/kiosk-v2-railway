// File: src/stores/navigationStore.ts
//
// Purpose:
// Zustand store for kiosk navigation UI state.
// Manages active category, item selection, and navigation mode.
// Simple, fast state for UI interactions without duplicating server data.

import { create } from 'zustand'

export type NavigationMode = 'categories' | 'items' | 'cart' | 'order_processing'

interface NavigationState {
  activeCategory: string | null
  activeItemIndex: number
  activeCartItemIndex: number
  navigationMode: NavigationMode
  // State to return to when exiting cart mode
  previousMode: NavigationMode | null
  previousCategory: string | null
  previousItemIndex: number
}

interface NavigationActions {
  setActiveCategory: (category: string | null) => void
  setActiveItemIndex: (index: number) => void
  setActiveCartItemIndex: (index: number) => void
  setNavigationMode: (mode: NavigationMode) => void
  resetNavigation: () => void
  navigateToCategory: (category: string) => void
  navigateToItems: () => void
  navigateBackToCategories: () => void
  navigateToCart: () => void
  navigateBackFromCart: () => void
  navigateToOrderProcessing: () => void
  navigateBackFromOrderProcessing: () => void
}

type NavigationStore = NavigationState & NavigationActions

const initialState: NavigationState = {
  activeCategory: null, // Will be set to first category when categories load
  activeItemIndex: 0,
  activeCartItemIndex: 0,
  navigationMode: 'categories',
  previousMode: null,
  previousCategory: null,
  previousItemIndex: 0
}

export const useNavigationStore = create<NavigationStore>((set, get) => ({
  ...initialState,

  setActiveCategory: (category) => {
    set({
      activeCategory: category,
      activeItemIndex: 0 // Reset item index when changing category
    })
  },

  setActiveItemIndex: (index) => {
    set({ activeItemIndex: index })
  },

  setActiveCartItemIndex: (index) => {
    set({ activeCartItemIndex: index })
  },

  setNavigationMode: (mode) => {
    set({ navigationMode: mode })
  },

  resetNavigation: () => {
    set(initialState)
  },

  // Convenience methods for common navigation patterns
  navigateToCategory: (category) => {
    set({
      activeCategory: category,
      activeItemIndex: 0,
      navigationMode: 'categories'
    })
  },

  navigateToItems: () => {
    console.log('🔄 Navigation: Switching to ITEMS mode, activeItemIndex set to 0')
    set({
      navigationMode: 'items',
      activeItemIndex: 0
    })
  },

  navigateBackToCategories: () => {
    console.log('🔄 Navigation: Switching to CATEGORIES mode')
    set({
      navigationMode: 'categories'
    })
  },

  navigateToCart: () => {
    const { navigationMode, activeCategory, activeItemIndex } = get()
    console.log('🛒 Navigation: Switching to CART mode, saving previous state:', {
      previousMode: navigationMode,
      previousCategory: activeCategory,
      previousItemIndex: activeItemIndex
    })
    set({
      previousMode: navigationMode,
      previousCategory: activeCategory,
      previousItemIndex: activeItemIndex,
      navigationMode: 'cart',
      activeCartItemIndex: 0
    })
  },

  navigateBackFromCart: () => {
    const { previousMode, previousCategory, previousItemIndex } = get()
    console.log('🔙 Navigation: Exiting CART mode, restoring state:', {
      previousMode,
      previousCategory,
      previousItemIndex
    })
    set({
      navigationMode: previousMode || 'categories',
      activeCategory: previousCategory,
      activeItemIndex: previousItemIndex,
      previousMode: null,
      previousCategory: null,
      previousItemIndex: 0
    })
  },

  navigateToOrderProcessing: () => {
    const { navigationMode, activeCategory, activeItemIndex } = get()
    console.log('📦 Navigation: Switching to ORDER_PROCESSING mode, saving previous state:', {
      previousMode: navigationMode,
      previousCategory: activeCategory,
      previousItemIndex: activeItemIndex
    })
    set({
      previousMode: navigationMode,
      previousCategory: activeCategory,
      previousItemIndex: activeItemIndex,
      navigationMode: 'order_processing'
    })
  },

  navigateBackFromOrderProcessing: () => {
    const { previousMode, previousCategory, previousItemIndex } = get()
    console.log('🔙 Navigation: Exiting ORDER_PROCESSING mode, restoring state:', {
      previousMode,
      previousCategory,
      previousItemIndex
    })
    set({
      navigationMode: previousMode || 'categories',
      activeCategory: previousCategory,
      activeItemIndex: previousItemIndex,
      previousMode: null,
      previousCategory: null,
      previousItemIndex: 0
    })
  },

}))