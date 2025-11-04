// File: src/models/view/categories.vm.ts
//
// Purpose:
// View-layer models for the categories feature.
// These types are tailored for the UI (components/pages) and should contain
// only the data and naming that the UI needs, after domain mapping.
// No transport (API) concerns and no business logic should be placed here.

/**
 * CategoryVM
 * View-model representation of a food category for UI consumption.
 *
 * Backend provides unified structure with synthetic promoted at index [0].
 * All categories have same structure with optional ru_label/en_label.
 * Display name uses ru_label if available, falls back to name (Option 1).
 */
export interface CategoryVM {
  name: string
  displayName: string // Formatted display: "[1] Промо", "[2] Сладости", etc.
  displayOrder: number // 0 = synthetic promoted, 1+ = regular
  ruLabel: string | null // Russian label (optional, falls back to name)
  enLabel: string | null // English label (optional, falls back to name)
  createdAt: Date
}

/**
 * CategoriesListVM
 * View-model representation of the categories list for UI consumption.
 * Categories array includes synthetic promoted category at index [0].
 */
export interface CategoriesListVM {
  categories: CategoryVM[] // [0] = synthetic promoted, [1+] = regular
  totalCount: number // Total including synthetic promoted
  isLoading: boolean
  error: string | null
}