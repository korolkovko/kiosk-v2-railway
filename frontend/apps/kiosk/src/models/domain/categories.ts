// File: src/models/domain/categories.ts
//
// Purpose:
// Domain-layer models for categories feature.
// These interfaces represent business entities used across services/hooks/UI.
// They are independent of transport (API) and view formatting concerns.

/**
 * Category
 * Domain model for a food category with optional localized labels.
 * Backend returns unified structure with synthetic promoted at index [0].
 * All categories have same structure with optional ru_label/en_label.
 */
export interface Category {
  name: string
  displayOrder: number // 0 = synthetic promoted, 1+ = regular
  ruLabel: string | null // Russian label (optional, falls back to name)
  enLabel: string | null // English label (optional, falls back to name)
  createdAt: Date
}

/**
 * CategoriesList
 * Represents the categories collection within the domain layer.
 * Categories array includes synthetic promoted category at index [0].
 */
export interface CategoriesList {
  categories: Category[] // [0] = synthetic promoted, [1+] = regular
  totalCount: number // Total including synthetic promoted
}