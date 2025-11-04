// File: src/models/domain/cart.ts
//
// Purpose:
// Domain model for shopping cart in kiosk.
// Represents the customer's order assembly with items, quantities, and wishes.
// Clean, framework-agnostic model for business logic.

/**
 * CartItem
 * Domain model for a single item in the shopping cart.
 * Maps to backend OrderItemRequest structure.
 */
export interface CartItem {
  item_id: number;
  quantity: number;
  wishes: string | null;
}

/**
 * Cart
 * Domain model for the complete shopping cart.
 * Contains all items customer wants to order.
 */
export interface Cart {
  items: CartItem[];
  created_at: Date;
  updated_at: Date;
}

/**
 * CartTotals
 * Domain model for cart price calculations.
 * All calculations performed on frontend for fast updates.
 */
export interface CartTotals {
  total_items_count: number;
  total_net_amount: number;
  total_vat_amount: number;
  total_gross_amount: number;
  currency: string;
}