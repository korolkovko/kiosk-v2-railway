// File: src/contexts/CategoriesContext.tsx
//
// Purpose:
// Categories context exposing categories state and operations for UI.
// Delegates all business logic to services (DTO→Domain→ViewModel mapping, API calls).
// No direct API calls here; no transport details leaked to consumers.

import { createContext, useContext, ReactNode, useCallback, useEffect } from 'react'

// View-layer model for categories
import type { CategoryVM, CategoriesListVM } from '../models/view/categories.vm'

// Auth context for integration
import { useAuth } from './AuthContext'

// Orchestration service (business logic)
import {
  fetchCategoriesWithSyntheticPromoted,
  createLoadingCategoriesVM,
  createErrorCategoriesVM,
} from '../services/categories.service'

// Persistence utility
import { usePersistedState, PERSISTENCE_CONFIGS } from '../hooks/usePersistedState'

interface CategoriesContextType {
  categoriesData: CategoriesListVM
  categories: CategoryVM[]
  isLoading: boolean
  error: string | null
  fetchCategories: () => Promise<void>
  clearError: () => void
}

const CategoriesContext = createContext<CategoriesContextType | undefined>(undefined)

export const CategoriesProvider = ({ children }: { children: ReactNode }) => {
  const { onCategoriesFetch } = useAuth()

  // Use persisted state for categories (localStorage, 24 hour TTL)
  const [categoriesData, setCategoriesData] = usePersistedState<CategoriesListVM>(
    'kiosk_categories',
    {
      categories: [],
      totalCount: 0,
      isLoading: false,
      error: null,
    },
    PERSISTENCE_CONFIGS.CATEGORIES
  )

  /**
   * fetchCategories()
   * Fetch categories from API and update context state
   */
  const fetchCategories = useCallback(async () => {
    try {
      // Set loading state
      setCategoriesData(createLoadingCategoriesVM())

      // Fetch categories with synthetic promoted from backend
      const categoriesVM = await fetchCategoriesWithSyntheticPromoted()
      setCategoriesData(categoriesVM)
    } catch (error) {
      // Handle error state
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch categories'
      setCategoriesData(createErrorCategoriesVM(errorMessage))
    }
  }, [])

  /**
   * clearError()
   * Clear error state
   */
  const clearError = useCallback(() => {
    if (categoriesData.error) {
      setCategoriesData(prev => ({
        ...prev,
        error: null,
      }))
    }
  }, [categoriesData.error])

  /**
   * Auto-fetch categories on mount
   */
  useEffect(() => {
    fetchCategories()
  }, [fetchCategories])

  /**
   * Register fetchCategories with AuthContext for compatibility
   */
  useEffect(() => {
    if (onCategoriesFetch) {
      onCategoriesFetch(fetchCategories)
    }
  }, [onCategoriesFetch, fetchCategories])

  return (
    <CategoriesContext.Provider
      value={{
        categoriesData,
        categories: categoriesData.categories,
        isLoading: categoriesData.isLoading,
        error: categoriesData.error,
        fetchCategories,
        clearError,
      }}
    >
      {children}
    </CategoriesContext.Provider>
  )
}

export const useCategories = (): CategoriesContextType => {
  const context = useContext(CategoriesContext)
  if (!context) {
    throw new Error('useCategories must be used within CategoriesProvider')
  }
  return context
}