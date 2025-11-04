// File: src/models/dto/categories.dto.ts
//
// Purpose:
// Data Transfer Objects (DTOs) for categories API endpoints.
// These types mirror the exact JSON structure returned by the backend API.
// No business logic or transformations here - pure transport layer types.

/**
 * DTO for a single category from the backend API
 * Mirrors the KioskCategoryResponse Pydantic model
 *
 * Backend returns unified structure with synthetic promoted at [0]
 */
export interface CategoryDto {
  name: string
  display_order: number // 0 = synthetic promoted, 1+ = regular categories
  ru_label: string | null // Russian label (optional, falls back to name)
  en_label: string | null // English label (optional, falls back to name)
  created_at: string // ISO datetime string from backend
}

/**
 * DTO for the categories list response from the backend API
 * Mirrors the KioskCategoriesListResponse Pydantic model
 *
 * Backend returns unified array with synthetic promoted category at index [0]
 */
export interface CategoriesListResponseDto {
  categories: CategoryDto[] // [0] = synthetic promoted, [1+] = regular
  total_count: number // Total including synthetic promoted
}