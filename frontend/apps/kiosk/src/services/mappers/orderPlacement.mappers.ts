// File: src/services/mappers/orderPlacement.mappers.ts
//
// Purpose:
// Pure mapper functions for transforming order placement data through layers.
// DTO → Domain: Convert kopecks to rubles, parse enums, normalize field names
// Follows same pattern as getAvailableItems.mappers.ts

import type { OrderDto, OrderCreationResponseDto } from '../../models/dto/orderPlacement.dto'
import type { Order } from '../../models/domain/order'
import { OrderStatus, FSMState } from '../../models/domain/order'

/**
 * mapOrderDtoToDomain
 * Transform single OrderDto to Domain Order
 * Converts kopecks (integers) from backend to rubles (decimals) for domain layer
 */
export function mapOrderDtoToDomain(dto: OrderDto): Order {
  // Backend sends kopecks (integers), convert to rubles (decimals) for domain layer
  const totalNetRubles = dto.total_amount_net_kopecks / 100
  const totalVatRubles = dto.total_amount_vat_kopecks / 100
  const totalGrossRubles = dto.total_amount_gross_kopecks / 100

  return {
    order_id: dto.order_id,
    pickup_number: dto.pickup_number,
    pin_code: dto.pin_code,
    status: parseOrderStatus(dto.status),
    fsm_state: parseFSMState(dto.fsm_state),
    fsm_event_history: [],
    total_amount_net: totalNetRubles,
    total_amount_vat: totalVatRubles,
    total_amount_gross: totalGrossRubles,
    currency: dto.currency,
    order_time: new Date(dto.order_time),
    created_at: new Date(dto.order_time),  // Use order_time as created_at
    updated_at: new Date(dto.order_time)   // Use order_time as updated_at initially
  }
}

/**
 * mapOrderCreationResponseToDomain
 * Transform complete API response to Domain Order
 */
export function mapOrderCreationResponseToDomain(response: OrderCreationResponseDto): Order {
  return mapOrderDtoToDomain(response.order)
}

/**
 * Parse OrderStatus from string to enum
 * Provides fallback for unknown values
 */
function parseOrderStatus(status: string): OrderStatus {
  const upperStatus = status.toUpperCase()

  if (upperStatus in OrderStatus) {
    return OrderStatus[upperStatus as keyof typeof OrderStatus]
  }

  console.warn(`Unknown order status: ${status}, defaulting to PENDING`)
  return OrderStatus.PENDING
}

/**
 * Parse FSMState from string to enum
 * Provides fallback for unknown values
 */
function parseFSMState(state: string): FSMState {
  const upperState = state.toUpperCase()

  if (upperState in FSMState) {
    return FSMState[upperState as keyof typeof FSMState]
  }

  console.warn(`Unknown FSM state: ${state}, defaulting to INIT`)
  return FSMState.INIT
}
