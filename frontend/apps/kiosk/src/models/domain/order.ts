// File: src/models/domain/order.ts
//
// Purpose:
// Domain model for order status tracking in kiosk.
// Represents order lifecycle with all status fields for SSE updates.
// Clean, framework-agnostic model for business logic.

/**
 * OrderStatus
 * Enum for overall order status tracking (matches backend models.py).
 */
export enum OrderStatus {
  PENDING = 'PENDING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

/**
 * FSMEvent
 * Enum for FSM event tracking (matches backend fsm_spec.Event exactly).
 * These events are sent via ORDER_EVENT_TRIGGERED SSE events.
 */
export enum FSMEvent {
  FISCALIZATION_SUCCEEDED = 'FISCALIZATION_SUCCEEDED',
  FISCALIZATION_FAILED = 'FISCALIZATION_FAILED',
  PAYMENT_SUCCEEDED = 'PAYMENT_SUCCEEDED',
  USER_CANCELED = 'USER_CANCELED',
  INACTIVITY_TIMEOUT = 'INACTIVITY_TIMEOUT',
  PAYMENT_FAILED = 'PAYMENT_FAILED',
  PRINTING_SUCCEEDED = 'PRINTING_SUCCEEDED',
  PRINTING_FAILED_OR_TIMEOUT = 'PRINTING_FAILED_OR_TIMEOUT',
  KDS_CONFIRMATION = 'KDS_CONFIRMATION',
  KDS_ERROR_OR_NO_RESPONSE = 'KDS_ERROR_OR_NO_RESPONSE'
}

/**
 * FSMState
 * Enum for FSM state tracking (matches backend fsm_spec.State exactly).
 * These are the exact states the server sends via SSE.
 */
export enum FSMState {
  INIT = 'INIT',
  AWAITING_PAYMENT = 'AWAITING_PAYMENT',
  AWAITING_PRINTING = 'AWAITING_PRINTING',
  AWAITING_KDS = 'AWAITING_KDS',
  
  // Terminal / failure / side branches
  CANCELED_BY_USER = 'CANCELED_BY_USER',
  CANCELED_BY_TIMEOUT = 'CANCELED_BY_TIMEOUT',
  UNSUCCESSFUL_PAYMENT = 'UNSUCCESSFUL_PAYMENT',
  PRINTING_FAILED = 'PRINTING_FAILED',
  SENT_TO_KDS = 'SENT_TO_KDS',
  SENT_TO_KDS_FAILED = 'SENT_TO_KDS_FAILED',
  UNSUCCESSFUL_FISCALIZATION = 'UNSUCCESSFUL_FISCALIZATION'
}

/**
 * FSMEventHistoryEntry
 * Single FSM event occurrence during order processing.
 * Stored in OrderContext alongside order status.
 */
export interface FSMEventHistoryEntry {
  event: FSMEvent
  fsm_state_after: string  // State after this event
  timestamp: Date
  actor_type?: string  // SYSTEM, USER, etc.
}

/**
 * Order
 * Domain model for order with status tracking fields (matches backend structure).
 * Updated via SSE from backend during order processing.
 * Stored in OrderContext (React Context) - cleared on terminal states.
 */
export interface Order {
  // Order identification (matches backend Order model)
  order_id: number;
  pickup_number: string;
  pin_code: string;

  // Overall order status (matches backend OrderStatus enum)
  status: OrderStatus;

  // FSM state for detailed processing tracking (matches backend FSM)
  fsm_state: FSMState;

  // FSM event history - stored in OrderContext, same as status
  // All events cleared together when order reaches terminal state
  fsm_event_history: FSMEventHistoryEntry[];

  // Financial information
  total_amount_net: number;
  total_amount_vat: number;
  total_amount_gross: number;
  currency: string;

  // Timestamps
  order_time: Date;
  created_at: Date;
  updated_at: Date;
}

/**
 * OrderStatusUpdate
 * Domain model for SSE status update events.
 */
export interface OrderStatusUpdate {
  order_id: number;
  field_name: keyof Pick<Order, 'status' | 'fsm_state'>;
  new_value: OrderStatus | FSMState;
  timestamp: Date;
}