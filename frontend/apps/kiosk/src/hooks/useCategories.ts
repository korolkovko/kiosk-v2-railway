// File: src/hooks/useCategories.ts
//
// Purpose:
// Custom hook for accessing categories functionality with dynamic promoted category filtering.
// - Filters out promoted category if no promoted items exist
// - Adjusts category numbering dynamically ([1], [2], [3] vs [2], [3], [4])
// - Provides a clean interface for components to interact with categories.

import { useMemo } from 'react'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { useItems } from '../contexts/ItemsContext'
import type { CategoryVM } from '../models/view/categories.vm'

/**
 * useCategories()
 * Enhanced hook that dynamically shows/hides promoted category based on promoted items.
 *
 * Behavior:
 * - If any items have promoted=true → Promoted category appears as [1]
 * - If no promoted items → Promoted category hidden, numbering starts from [1] for other categories
 * - Updates in real-time via SSE when items are promoted/unpromoted
 */
export const useCategories = () => {
  const categoriesContext = useCategoriesContext()
  const { items: availableItems } = useItems()

  // Filter categories based on promoted items existence
  const filteredCategories = useMemo(() => {
    const { categories } = categoriesContext

    // Check if any items are promoted
    const hasPromotedItems = availableItems.some(item => item.promoted && item.isAvailable)

    // If no promoted items, filter out promoted category (always first in the list)
    if (!hasPromotedItems) {
      // Skip first category (promoted category) and keep the rest
      const categoriesWithoutPromoted = categories.slice(1)

      // Re-number categories starting from [1] instead of [2]
      const renumberedCategories: CategoryVM[] = categoriesWithoutPromoted.map((cat, index) => ({
        ...cat,
        displayName: `[${index + 1}] ${cat.name}`
      }))

      console.log('🔍 Categories: No promoted items, hiding promoted category')
      return renumberedCategories
    }

    // Has promoted items, keep all categories (including promoted)
    console.log('🔍 Categories: Has promoted items, showing promoted category')
    return categories
  }, [categoriesContext.categories, availableItems])

  // Return enhanced context with filtered categories
  return {
    ...categoriesContext,
    categories: filteredCategories
  }
}

/**
 * Export the hook as default for convenience
 */
export default useCategories