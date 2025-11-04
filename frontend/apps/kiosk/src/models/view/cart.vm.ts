// File: src/models/view/cart.vm.ts
//
// Purpose:
// View model for shopping cart optimized for UI display.
// Contains formatted strings, item details, and calculated totals.
// Enriches domain model with data from available items for fast UI rendering.

import type { CartTotals } from '../domain/cart'

/**
 * CartItemVM
 * View model for a single cart item with UI display data.
 * Enriched with item details from available items context.
 */
export interface CartItemVM {
  // Domain data
  item_id: number;
  quantity: number;
  wishes: string | null;
  
  // Enriched item details (from available items)
  name_ru: string;
  name_eng: string | null;
  description_ru: string;
  unit_measure: string;
  
  // Price data (numeric for calculations)
  price_net: number;
  vat_rate: number | null;
  vat_amount: number;
  price_gross: number;
  
  // Formatted price strings for display
  price_gross_display: string; // e.g., "150.00 ₽"
  line_total_display: string;  // e.g., "300.00 ₽" (quantity * price_gross)
  
  // UI state
  is_available: boolean;
  stock_quantity: number;
}

/**
 * CartTotalsVM
 * View model for cart totals with formatted display strings.
 */
export interface CartTotalsVM extends CartTotals {
  // Formatted display strings
  total_items_count_display: string;     // e.g., "3 items"
  total_net_amount_display: string;      // e.g., "1,200.00 ₽"
  total_vat_amount_display: string;      // e.g., "240.00 ₽"
  total_gross_amount_display: string;    // e.g., "1,440.00 ₽"
}

/**
 * CartVM
 * Complete view model for cart with all UI display data.
 * Single source of truth for cart rendering in components.
 */
export interface CartVM {
  // Cart items with full display data
  items: CartItemVM[];
  
  // Calculated totals with display formatting
  totals: CartTotalsVM;
  
  // Cart state
  is_empty: boolean;
  has_unavailable_items: boolean;
  can_place_order: boolean;
  
  // Timestamps for display
  created_at: Date;
  updated_at: Date;
  last_updated_display: string; // e.g., "Updated 2 minutes ago"
}

/**
 * CartItemUpdateRequest
 * View model for cart item update operations.
 * Used by cart management service for UI interactions.
 */
export interface CartItemUpdateRequest {
  item_id: number;
  quantity?: number;
  wishes?: string | null;
  operation: 'add' | 'update' | 'remove';
}