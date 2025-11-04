// File: src/models/dto/getAvailableItems.dto.ts
//
// Purpose:
// Transport-layer DTOs for "Get Available Items" kiosk endpoint.
// These interfaces reflect the exact JSON shape returned by the backend for
// kiosk available items operation. No domain or view logic here.

/**
 * GetAvailableItemDto
 * One item as returned by the backend "kiosk/items/available" endpoint.
 * Notes:
 * - Backend now sends prices in kopecks (integers) after migration
 * - Frontend will convert kopecks to rubles for display (divide by 100)
 * - *_eng fields can be null
 * - stock_quantity is included for kiosk menu display
 */
export interface GetAvailableItemDto {
  item_id: number;
  name_ru: string;
  name_eng: string | null;
  description_ru: string;
  description_eng: string | null;
  unit_measure_name_eng: string;
  food_category_name: string;
  price_net_kopecks: number;   // Backend sends integer kopecks
  vat_rate: string | null; // numeric string or null (percentage)
  vat_amount_kopecks: number; // Backend sends integer kopecks
  price_gross_kopecks: number; // Backend sends integer kopecks
  is_active: boolean;
  promoted: boolean;
  stock_quantity: number;

  // Menu display fields
  display_order: number;
  start_at: string | null; // Time in HH:MM:SS format or null (all day)
  end_at: string | null;   // Time in HH:MM:SS format or null (all day)
}

/**
 * GetAvailableItemsResponseDto
 * Array of items as returned by the endpoint.
 */
export type GetAvailableItemsResponseDto = GetAvailableItemDto[];
