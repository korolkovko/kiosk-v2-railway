// File: src/utils/promotedCategory.ts
//
// Purpose:
// Utility functions for working with the promoted category.
// Provides a single source of truth for promoted category identification
// instead of hardcoded "NEW" strings throughout the codebase.

import type { CategoryVM } from '../models/view/categories.vm'

/**
 * Get the promoted category name from the categories list.
 * The promoted category is always the first category (displayOrder: 0).
 *
 * @param categories - List of categories from context
 * @returns The name of the promoted category, or 'promoted' as fallback
 */
export function getPromotedCategoryName(categories: CategoryVM[]): string {
  // Promoted category is always first in the list
  // Fallback to 'promoted' to match the default in promoted_label table
  return categories.length > 0 ? categories[0].name : 'promoted'
}

/**
 * Check if a given category name is the promoted category.
 *
 * @param categoryName - Category name to check
 * @param categories - List of categories from context
 * @returns true if the category is the promoted category
 */
export function isPromotedCategory(categoryName: string, categories: CategoryVM[]): boolean {
  const promotedName = getPromotedCategoryName(categories)
  return categoryName.toLowerCase() === promotedName.toLowerCase()
}
