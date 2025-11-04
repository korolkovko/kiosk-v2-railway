// File: src/models/view/order.vm.ts
//
// Purpose:
// View model for order status tracking optimized for UI display.
// Contains formatted strings, status indicators, and progress information.
// Enriches domain model with UI-friendly display data.

import type { Order, OrderStatus, PaymentStatus, FSMState, OrderStatusUpdate } from '../domain/order'

/**
 * ProcessingStatusVM
 * View model for individual processing step status with UI display data.
 */
export interface FSMStatusVM {
  fsm_state: FSMState;
  status_display: string;        // e.g., "Payment Pending", "Completed", "Failed"
  status_color: string;          // e.g., "green", "yellow", "red"
  status_icon: string;           // e.g., "✓", "⟳", "✗"
  is_completed: boolean;
  is_failed: boolean;
  is_in_progress: boolean;
}

export interface PaymentStatusVM {
  payment_status: PaymentStatus;
  status_display: string;        // e.g., "Success", "Declined", "Error"
  status_color: string;          // e.g., "green", "red", "yellow"
  status_icon: string;           // e.g., "✓", "✗", "⚠"
  is_successful: boolean;
  is_failed: boolean;
  is_pending: boolean;
}

/**
 * OrderVM
 * Complete view model for order with all UI display data.
 * Single source of truth for order status rendering in components.
 */
export interface OrderVM {
  // Order identification (matches backend structure)
  order_id: number;
  pickup_number: string;
  pickup_number_display: string;  // e.g., "Pickup #123"
  pin_code: string;
  pin_code_display: string;       // e.g., "PIN: 4567"
  
  // Overall order status
  status: OrderStatus;
  status_display: string;         // e.g., "Pending", "Completed", "Failed"
  status_color: string;           // e.g., "green", "yellow", "red"
  
  // Payment status with UI data
  payment_status: PaymentStatusVM;
  
  // FSM state with UI data
  fsm_status: FSMStatusVM;
  
  // Progress indicators
  overall_progress_percentage: number;  // 0-100
  progress_display: string;             // e.g., "Payment completed, processing order"
  
  // Timestamps
  order_time: Date;
  created_at: Date;
  updated_at: Date;
  order_time_display: string;           // e.g., "Ordered 5 minutes ago"
  last_updated_display: string;         // e.g., "Updated 30 seconds ago"
  
  // Financial information
  total_amount_net: number;
  total_amount_vat: number;
  total_amount_gross: number;
  total_amount_display: string;         // e.g., "1,440.00 ₽"
  currency: string;
  
  // UI state
  is_completed: boolean;
  is_failed: boolean;
  is_ready_for_pickup: boolean;
  can_be_cancelled: boolean;
  requires_customer_action: boolean;
}

/**
 * OrderStatusUpdateVM
 * View model for SSE status update events with UI display data.
 */
export interface OrderStatusUpdateVM extends OrderStatusUpdate {
  // Display formatting
  field_display_name: string;          // e.g., "Payment Status", "Fiscalization"
  old_value_display?: string;          // e.g., "Pending"
  new_value_display: string;           // e.g., "Completed"
  update_message: string;              // e.g., "Payment completed successfully"
  timestamp_display: string;           // e.g., "2 minutes ago"
  
  // UI indicators
  is_positive_change: boolean;
  is_negative_change: boolean;
  notification_type: 'success' | 'warning' | 'error' | 'info';
}

/**
 * OrderListVM
 * View model for displaying multiple orders (for future extension).
 */
export interface OrderListVM {
  orders: OrderVM[];
  active_order?: OrderVM;
  completed_orders_count: number;
  pending_orders_count: number;
  failed_orders_count: number;
}