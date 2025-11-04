// File: src/services/cartTotalPriceCalculation.service.ts
//
// Purpose:
// Service for calculating cart totals on frontend for fast UI updates.
// Handles price calculations, VAT computations, and formatting.
// Integrates with available items context for current pricing data.

import type { Cart, CartTotals } from '../models/domain/cart'
import type { CartTotalsVM } from '../models/view/cart.vm'
import type { AvailableItem } from '../models/domain/availableItem'

/**
 * Calculate cart totals from cart items and available items data
 */
export function calculateCartTotals(
  cart: Cart,
  availableItems: AvailableItem[]
): CartTotals {
  if (cart.items.length === 0) {
    return {
      total_items_count: 0,
      total_net_amount: 0,
      total_vat_amount: 0,
      total_gross_amount: 0,
      currency: 'RUB'
    }
  }

  let totalItemsCount = 0
  let totalNetAmount = 0
  let totalVatAmount = 0
  let totalGrossAmount = 0

  // Create a map for fast item lookup
  const itemsMap = new Map(
    availableItems.map(item => [item.itemId, item])
  )

  // Calculate totals for each cart item
  for (const cartItem of cart.items) {
    const availableItem = itemsMap.get(cartItem.item_id)
    
    if (!availableItem) {
      console.warn(`Cart item ${cartItem.item_id} not found in available items`)
      continue
    }

    // Skip unavailable items - supports both isActive (domain) and isAvailable (VM)
    const isItemActive = availableItem.isActive ?? availableItem.isAvailable ?? false
    if (!isItemActive || availableItem.stockQuantity <= 0) {
      console.warn(`Cart item ${cartItem.item_id} is not available`)
      continue
    }

    const quantity = cartItem.quantity
    const lineNetAmount = availableItem.priceNet * quantity
    const lineVatAmount = availableItem.vatAmount * quantity
    const lineGrossAmount = availableItem.priceGross * quantity

    totalItemsCount += quantity
    totalNetAmount += lineNetAmount
    totalVatAmount += lineVatAmount
    totalGrossAmount += lineGrossAmount
  }

  return {
    total_items_count: totalItemsCount,
    total_net_amount: Math.round(totalNetAmount * 100) / 100, // Round to 2 decimal places
    total_vat_amount: Math.round(totalVatAmount * 100) / 100,
    total_gross_amount: Math.round(totalGrossAmount * 100) / 100,
    currency: 'RUB'
  }
}

/**
 * Format cart totals for UI display
 */
export function formatCartTotalsForDisplay(totals: CartTotals): CartTotalsVM {
  const currencySymbol = totals.currency === 'RUB' ? '₽' : totals.currency

  return {
    ...totals,
    total_items_count_display: formatItemsCount(totals.total_items_count),
    total_net_amount_display: formatCurrency(totals.total_net_amount, currencySymbol),
    total_vat_amount_display: formatCurrency(totals.total_vat_amount, currencySymbol),
    total_gross_amount_display: formatCurrency(totals.total_gross_amount, currencySymbol)
  }
}

/**
 * Calculate line total for a single cart item
 */
export function calculateCartItemLineTotal(
  itemId: number,
  quantity: number,
  availableItems: AvailableItem[]
): {
  line_net_total: number
  line_vat_total: number
  line_gross_total: number
  is_available: boolean
} {
  const availableItem = availableItems.find(item => item.itemId === itemId)

  // Check availability - supports both isActive (domain) and isAvailable (VM)
  const isItemActive = availableItem?.isActive ?? availableItem?.isAvailable ?? false

  if (!availableItem || !isItemActive || availableItem.stockQuantity <= 0) {
    return {
      line_net_total: 0,
      line_vat_total: 0,
      line_gross_total: 0,
      is_available: false
    }
  }

  return {
    line_net_total: Math.round(availableItem.priceNet * quantity * 100) / 100,
    line_vat_total: Math.round(availableItem.vatAmount * quantity * 100) / 100,
    line_gross_total: Math.round(availableItem.priceGross * quantity * 100) / 100,
    is_available: true
  }
}

/**
 * Validate cart against available items
 */
export function validateCartAgainstAvailableItems(
  cart: Cart,
  availableItems: AvailableItem[]
): {
  is_valid: boolean
  unavailable_items: number[]
  out_of_stock_items: number[]
  warnings: string[]
} {
  const unavailableItems: number[] = []
  const outOfStockItems: number[] = []
  const warnings: string[] = []

  const itemsMap = new Map(
    availableItems.map(item => [item.itemId, item])
  )

  for (const cartItem of cart.items) {
    const availableItem = itemsMap.get(cartItem.item_id)
    
    if (!availableItem) {
      unavailableItems.push(cartItem.item_id)
      warnings.push(`Item ${cartItem.item_id} is no longer available`)
      continue
    }

    // Check availability - supports both isActive (domain) and isAvailable (VM)
    const isItemActive = availableItem.isActive ?? availableItem.isAvailable ?? false

    if (!isItemActive) {
      unavailableItems.push(cartItem.item_id)
      warnings.push(`Item "${availableItem.nameRu}" is currently unavailable`)
      continue
    }

    if (availableItem.stockQuantity <= 0) {
      outOfStockItems.push(cartItem.item_id)
      warnings.push(`Item "${availableItem.nameRu}" is out of stock`)
      continue
    }

    if (cartItem.quantity > availableItem.stockQuantity) {
      warnings.push(
        `Only ${availableItem.stockQuantity} units of "${availableItem.nameRu}" available (requested: ${cartItem.quantity})`
      )
    }
  }

  return {
    is_valid: unavailableItems.length === 0 && outOfStockItems.length === 0,
    unavailable_items: unavailableItems,
    out_of_stock_items: outOfStockItems,
    warnings
  }
}

/**
 * Helper function to format currency amounts
 */
function formatCurrency(amount: number, currencySymbol: string): string {
  return `${amount.toLocaleString('ru-RU', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  })} ${currencySymbol}`
}

/**
 * Helper function to format items count
 */
function formatItemsCount(count: number): string {
  if (count === 0) return 'No items'
  if (count === 1) return '1 item'
  return `${count} items`
}

/**
 * Helper function to get currency symbol
 */
export function getCurrencySymbol(currencyCode: string): string {
  const currencySymbols: Record<string, string> = {
    'RUB': '₽',
    'USD': '$',
    'EUR': '€',
    '643': '₽' // ISO numeric code for RUB
  }
  
  return currencySymbols[currencyCode] || currencyCode
}

/**
 * Calculate cart summary for order placement
 */
export function calculateCartSummaryForOrder(
  cart: Cart,
  availableItems: AvailableItem[]
): {
  totals: CartTotals
  validation: ReturnType<typeof validateCartAgainstAvailableItems>
  can_place_order: boolean
} {
  const totals = calculateCartTotals(cart, availableItems)
  const validation = validateCartAgainstAvailableItems(cart, availableItems)
  
  const canPlaceOrder = validation.is_valid && 
                       totals.total_items_count > 0 && 
                       totals.total_gross_amount > 0

  return {
    totals,
    validation,
    can_place_order: canPlaceOrder
  }
}