// File: src/services/categories.service.ts
//
// Purpose:
// Categories service orchestrating transport calls, mapping DTO→Domain→ViewModel,
// and state management. No UI or transport-specific logic here.
//
// Responsibilities:
// - Coordinate API calls (getCategories)
// - Map API DTOs to Domain and to ViewModel
// - Expose clear, self-descriptive methods for consumers (contexts/hooks/pages)
//
// Notes:
// - All functions are named exports (no default).
// - Consumers at UI level should prefer methods returning ViewModels.
// - Validation can be added at boundaries (e.g., zod) if/when needed.

import type { CategoriesListResponseDto } from '../models/dto/categories.dto'
import type { CategoriesList } from '../models/domain/categories'
import type { CategoriesListVM } from '../models/view/categories.vm'

import * as categoriesApi from '../api/categoriesApi'
import {
  mapCategoriesListResponseDtoToDomain,
  mapCategoriesListDomainToVM,
} from './mappers/categories.mappers'

/**
 * fetchCategoriesAndGetDomain()
 * - Calls transport API to fetch categories
 * - Maps DTO → Domain
 * - Returns Domain model for service-level consumption
 */
export async function fetchCategoriesAndGetDomain(): Promise<CategoriesList> {
  // Transport call
  const dto: CategoriesListResponseDto = await categoriesApi.getCategories()

  // DTO → Domain
  const categoriesList: CategoriesList = mapCategoriesListResponseDtoToDomain(dto)

  return categoriesList
}

/**
 * fetchCategoriesAndGetVM()
 * - Same as fetchCategoriesAndGetDomain() but returns VM for UI consumption
 */
export async function fetchCategoriesAndGetVM(): Promise<CategoriesListVM> {
  const categoriesList = await fetchCategoriesAndGetDomain()
  
  // Domain → ViewModel
  return mapCategoriesListDomainToVM(categoriesList)
}

/**
 * fetchCategoriesWithSyntheticPromoted()
 * - Fetches categories from backend (already includes synthetic promoted at [0])
 * - Backend provides unified structure, just map to ViewModels
 * - Returns ViewModel for kiosk navigation UI
 */
export async function fetchCategoriesWithSyntheticPromoted(): Promise<CategoriesListVM> {
  const backendCategoriesList = await fetchCategoriesAndGetDomain()

  console.log('🔍 Categories from backend (with synthetic promoted):', backendCategoriesList)
  console.log('📊 Total categories (including synthetic promoted):', backendCategoriesList.categories.length)
  console.log('📋 Categories structure:', backendCategoriesList.categories.map(c => ({
    name: c.name,
    displayOrder: c.displayOrder,
    ruLabel: c.ruLabel
  })))

  // Backend already provides unified structure with synthetic promoted at [0]
  // Just map to ViewModels - no need to create synthetic category here!
  return mapCategoriesListDomainToVM(backendCategoriesList, false, null)
}

/**
 * createLoadingCategoriesVM()
 * - Creates a loading state ViewModel for UI consumption
 */
export function createLoadingCategoriesVM(): CategoriesListVM {
  return {
    categories: [],
    totalCount: 0,
    isLoading: true,
    error: null
  }
}

/**
 * createErrorCategoriesVM()
 * - Creates an error state ViewModel for UI consumption
 */
export function createErrorCategoriesVM(error: string): CategoriesListVM {
  return {
    categories: [],
    totalCount: 0,
    isLoading: false,
    error
  }
}