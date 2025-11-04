// File: src/models/dto/orderPlacement.dto.ts
//
// Purpose:
// Transport-layer DTOs for order placement API.
// Reflects exact JSON shape from backend after kopeck migration.

/**
 * OrderCreationResponseDto
 * Response from POST /kiosk/orders after creating an order.
 * Backend now sends all amounts in kopecks (integers).
 */
export interface OrderCreationResponseDto {
  success: boolean
  order: OrderDto
  message: string
  listen: string  // SSE endpoint URL
}

/**
 * OrderDto
 * Order data as returned by backend API.
 * All monetary amounts are in kopecks (integers).
 */
export interface OrderDto {
  order_id: number
  pickup_number: string
  pin_code: string
  status: string  // OrderStatus enum value
  total_amount_net_kopecks: number    // Backend sends integer kopecks
  total_amount_vat_kopecks: number    // Backend sends integer kopecks
  total_amount_gross_kopecks: number  // Backend sends integer kopecks
  currency: string
  fsm_state: string          // FSM state enum value
  payment_status: string     // Payment status enum value
  order_time: string         // ISO datetime string
}

/**
 * OrderCreationRequestDto
 * Request for POST /kiosk/orders
 */
export interface OrderCreationRequestDto {
  items: Array<{
    item_id: number
    quantity: number
    wishes?: string
  }>
  currency: string
  customer_id?: number
  session_id?: string
}
