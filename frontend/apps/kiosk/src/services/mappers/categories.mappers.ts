// File: src/services/mappers/categories.mappers.ts
//
// Purpose:
// Pure mapping functions for the Categories feature.
// - DTO → Domain: clean/normalize API transport data
// - Domain → ViewModel: shape/format data for UI
//
// Notes:
// - No side-effects. No I/O. Deterministic and testable.
// - Business rules/orchestration live in services (e.g. src/services/categories.service.ts).
// - Validation schemas (zod/valibot) can be applied at API boundary; mappers assume valid input.

import type { CategoryDto, CategoriesListResponseDto } from '../../models/dto/categories.dto'
import type { Category, CategoriesList } from '../../models/domain/categories'
import type { CategoryVM, CategoriesListVM } from '../../models/view/categories.vm'

/**
 * mapCategoryDtoToDomain()
 * Convert API CategoryDto -> domain Category
 * Backend provides unified structure with synthetic promoted at [0]
 */
export function mapCategoryDtoToDomain(dto: CategoryDto): Category {
  return {
    name: dto.name,
    displayOrder: dto.display_order,
    ruLabel: dto.ru_label,
    enLabel: dto.en_label,
    createdAt: new Date(dto.created_at)
  }
}

/**
 * mapCategoriesListResponseDtoToDomain()
 * Convert API CategoriesListResponseDto -> domain CategoriesList
 * Categories array already includes synthetic promoted at index [0]
 */
export function mapCategoriesListResponseDtoToDomain(dto: CategoriesListResponseDto): CategoriesList {
  return {
    categories: dto.categories.map(mapCategoryDtoToDomain),
    totalCount: dto.total_count
  }
}

/**
 * mapCategoryDomainToVM()
 * Convert domain Category -> UI-friendly CategoryVM
 * Uses ru_label if available, falls back to name (Option 1)
 */
export function mapCategoryDomainToVM(category: Category): CategoryVM {
  // Option 1: Use ru_label if available, fallback to name
  const displayLabel = category.ruLabel || category.name

  return {
    name: category.name,
    displayName: `[${category.displayOrder + 1}] ${displayLabel}`,
    displayOrder: category.displayOrder,
    ruLabel: category.ruLabel,
    enLabel: category.enLabel,
    createdAt: category.createdAt
  }
}

/**
 * mapCategoriesListDomainToVM()
 * Convert domain CategoriesList -> UI-friendly CategoriesListVM
 * Categories already include synthetic promoted at [0]
 */
export function mapCategoriesListDomainToVM(
  categoriesList: CategoriesList,
  isLoading: boolean = false,
  error: string | null = null
): CategoriesListVM {
  return {
    categories: categoriesList.categories.map(mapCategoryDomainToVM),
    totalCount: categoriesList.totalCount,
    isLoading,
    error
  }
}