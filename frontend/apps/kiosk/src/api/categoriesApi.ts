// File: src/api/categoriesApi.ts
//
// Purpose:
// Transport-only functions for kiosk categories endpoints.
// Returns DTOs that reflect the exact backend JSON shape.
// No business logic or mapping here — keep it strictly HTTP + errors.

import type { CategoriesListResponseDto } from '../models/dto/categories.dto'
import { fetchWithAuth, handleApiResponse, ApiError } from './apiHttpClient'
import { KIOSK_CATEGORIES } from '../config/constants'

// Re-export ApiError as CategoriesError for backward compatibility
export { ApiError as CategoriesError }

/**
 * getCategories()
 * Transport call to GET /api/kiosk/categories
 * Returns raw DTO from backend without transformations.
 */
export async function getCategories(): Promise<CategoriesListResponseDto> {
  try {
    const response = await fetchWithAuth(KIOSK_CATEGORIES, {
      method: 'GET',
      // Enable retry on unauthenticated for this endpoint
      // since it requires valid kiosk authentication
      retryOnUnauthenticated: true,
    });

    return handleApiResponse<CategoriesListResponseDto>(response);
  } catch (error) {
    // Rethrow ApiErrors
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle unexpected errors
    throw new ApiError(
      'Failed to fetch categories. Please try again later.',
      'network'
    );
  }
}