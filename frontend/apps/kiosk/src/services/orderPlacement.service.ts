// File: src/services/orderPlacement.service.ts
//
// Purpose:
// Service for placing orders through the kiosk API.
// Handles order creation with cart items and returns domain Order model.
// Uses DTO → Domain mapper pattern for type safety and kopeck conversion.

import { fetchWithAuth, handleApiResponse } from '../api/apiHttpClient'
import type { CartItemVM } from '../models/view/cart.vm'
import type { Order } from '../models/domain/order'
import type { OrderCreationRequestDto, OrderCreationResponseDto } from '../models/dto/orderPlacement.dto'
import { mapOrderCreationResponseToDomain } from './mappers/orderPlacement.mappers'

/**
 * Place an order with the current cart items
 *
 * Flow:
 * 1. Validate cart items
 * 2. Transform to API request format (DTO)
 * 3. Call backend API
 * 4. Map response DTO → Domain (kopecks → rubles conversion)
 * 5. Return domain Order model
 *
 * @param cartItems - Array of cart items to order
 * @returns Promise with domain Order model
 * @throws Error if order placement fails
 */
export async function placeOrder(cartItems: CartItemVM[]): Promise<Order> {
  if (!cartItems || cartItems.length === 0) {
    throw new Error('Cannot place order with empty cart')
  }

  // Transform cart items to API request format (DTO)
  const orderRequest: OrderCreationRequestDto = {
    items: cartItems.map(item => ({
      item_id: item.item_id,
      quantity: item.quantity
      // wishes can be added when cart items support it
    })),
    currency: '643'  // RUB currency code (ISO 4217)
  }

  try {
    const response = await fetchWithAuth('/kiosk/orders', {
      method: 'POST',
      body: JSON.stringify(orderRequest)
    })

    // Get DTO response from API
    const responseDto = await handleApiResponse<OrderCreationResponseDto>(response)

    // Map DTO → Domain (converts kopecks to rubles)
    const domainOrder = mapOrderCreationResponseToDomain(responseDto)

    console.log('✅ Order created and mapped:', domainOrder)

    return domainOrder

  } catch (error: any) {
    // Handle API errors
    const errorMessage = error.message || 'Unknown error'
    console.error('❌ Order placement failed:', errorMessage)
    throw new Error(`Order placement failed: ${errorMessage}`)
  }
}

/**
 * Order placement service
 */
export const orderPlacementService = {
  placeOrder
}
