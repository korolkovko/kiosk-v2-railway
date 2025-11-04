// File: src/services/cartItemManagement.service.ts
//
// Purpose:
// Service for cart item management operations (add, remove, update, clear).
// Handles cart item business logic and integrates with available items validation.
// Provides clean interface for cart store and components.

import type { Cart } from '../models/domain/cart'
import type { CartVM, CartItemVM, CartItemUpdateRequest } from '../models/view/cart.vm'
import { 
  calculateCartTotals, 
  formatCartTotalsForDisplay, 
  calculateCartItemLineTotal,
  validateCartAgainstAvailableItems,
  getCurrencySymbol
} from './cartTotalPriceCalculation.service'

/**
 * Add item to cart or update quantity if item already exists
 */
export function addItemToCart(
  cart: Cart,
  itemId: number,
  quantity: number,
  wishes: string | null,
  availableItems: any[] // Accept both AvailableItem and AvailableItemVM
): {
  updatedCart: Cart
  success: boolean
  message: string
} {
  // Validate item availability
  const availableItem = availableItems.find(item => item.itemId === itemId)

  if (!availableItem) {
    return {
      updatedCart: cart,
      success: false,
      message: `Item ${itemId} not found`
    }
  }

  // Check availability - supports both isActive (domain) and isAvailable (VM)
  const isItemActive = availableItem.isActive ?? availableItem.isAvailable ?? false

  if (!isItemActive) {
    return {
      updatedCart: cart,
      success: false,
      message: `Item "${availableItem.nameRu}" is currently unavailable`
    }
  }

  if (availableItem.stockQuantity <= 0) {
    return {
      updatedCart: cart,
      success: false,
      message: `Item "${availableItem.nameRu}" is out of stock`
    }
  }

  // Check if item already exists in cart
  const existingItemIndex = cart.items.findIndex(item => item.item_id === itemId)
  const updatedItems = [...cart.items]

  if (existingItemIndex >= 0) {
    // Update existing item
    const existingItem = updatedItems[existingItemIndex]
    const newQuantity = existingItem.quantity + quantity

    // Check stock availability for new quantity
    if (newQuantity > availableItem.stockQuantity) {
      return {
        updatedCart: cart,
        success: false,
        message: `Only ${availableItem.stockQuantity} units of "${availableItem.nameRu}" available`
      }
    }

    updatedItems[existingItemIndex] = {
      ...existingItem,
      quantity: newQuantity,
      wishes: wishes || existingItem.wishes
    }
  } else {
    // Add new item
    if (quantity > availableItem.stockQuantity) {
      return {
        updatedCart: cart,
        success: false,
        message: `Only ${availableItem.stockQuantity} units of "${availableItem.nameRu}" available`
      }
    }

    updatedItems.push({
      item_id: itemId,
      quantity,
      wishes
    })
  }

  const updatedCart: Cart = {
    ...cart,
    items: updatedItems,
    updated_at: new Date()
  }

  return {
    updatedCart,
    success: true,
    message: `Added ${quantity} x "${availableItem.nameRu}" to cart`
  }
}

/**
 * Update cart item (quantity, wishes, or remove)
 */
export function updateCartItem(
  cart: Cart,
  request: CartItemUpdateRequest,
  availableItems: any[] // Accept both AvailableItem and AvailableItemVM
): {
  updatedCart: Cart
  success: boolean
  message: string
} {
  const { item_id, quantity, wishes, operation } = request
  const existingItemIndex = cart.items.findIndex(item => item.item_id === item_id)

  if (existingItemIndex === -1 && operation !== 'add') {
    return {
      updatedCart: cart,
      success: false,
      message: `Item ${item_id} not found in cart`
    }
  }

  const availableItem = availableItems.find(item => item.itemId === item_id)
  const itemName = availableItem?.nameRu || `Item ${item_id}`

  let updatedItems = [...cart.items]

  switch (operation) {
    case 'remove':
      updatedItems = updatedItems.filter(item => item.item_id !== item_id)
      break

    case 'update':
      if (existingItemIndex >= 0) {
        if (quantity === 0) {
          // Remove item if quantity is 0
          updatedItems = updatedItems.filter(item => item.item_id !== item_id)
        } else {
          // Validate new quantity
          if (availableItem && quantity && quantity > availableItem.stockQuantity) {
            return {
              updatedCart: cart,
              success: false,
              message: `Only ${availableItem.stockQuantity} units of "${itemName}" available`
            }
          }

          updatedItems[existingItemIndex] = {
            ...updatedItems[existingItemIndex],
            ...(quantity !== undefined && { quantity }),
            ...(wishes !== undefined && { wishes })
          }
        }
      }
      break

    case 'add':
      return addItemToCart(cart, item_id, quantity || 1, wishes || null, availableItems)

    default:
      return {
        updatedCart: cart,
        success: false,
        message: `Unknown operation: ${operation}`
      }
  }

  const updatedCart: Cart = {
    ...cart,
    items: updatedItems,
    updated_at: new Date()
  }

  let message = ''
  switch (operation) {
    case 'remove':
      message = `Removed "${itemName}" from cart`
      break
    case 'update':
      message = quantity === 0 
        ? `Removed "${itemName}" from cart`
        : `Updated "${itemName}" in cart`
      break
  }

  return {
    updatedCart,
    success: true,
    message
  }
}

/**
 * Remove item from cart completely
 */
export function removeItemFromCart(
  cart: Cart,
  itemId: number,
  availableItems: any[] // Accept both AvailableItem and AvailableItemVM
): {
  updatedCart: Cart
  success: boolean
  message: string
} {
  return updateCartItem(cart, {
    item_id: itemId,
    operation: 'remove'
  }, availableItems)
}

/**
 * Clear all items from cart
 */
export function clearCart(): Cart {
  return {
    items: [],
    created_at: new Date(),
    updated_at: new Date()
  }
}

/**
 * Generate CartVM from Cart domain model
 */
export function generateCartViewModel(
  cart: Cart,
  availableItems: any[] // Accept both AvailableItem and AvailableItemVM
): CartVM {
  // Generate cart items view models
  const cartItemsVM: CartItemVM[] = cart.items.map(cartItem => {
    const availableItem = availableItems.find(item => item.itemId === cartItem.item_id)
    
    if (!availableItem) {
      // Handle missing item gracefully
      return {
        item_id: cartItem.item_id,
        quantity: cartItem.quantity,
        wishes: cartItem.wishes,
        name_ru: `Unknown Item ${cartItem.item_id}`,
        name_eng: null,
        description_ru: 'Item not found',
        unit_measure: 'pcs',
        price_net: 0,
        vat_rate: null,
        vat_amount: 0,
        price_gross: 0,
        price_gross_display: '0.00 ₽',
        line_total_display: '0.00 ₽',
        is_available: false,
        stock_quantity: 0
      }
    }

    const lineTotal = calculateCartItemLineTotal(
      cartItem.item_id,
      cartItem.quantity,
      availableItems
    )

    const currencySymbol = getCurrencySymbol('RUB')

    return {
      item_id: cartItem.item_id,
      quantity: cartItem.quantity,
      wishes: cartItem.wishes,
      name_ru: availableItem.nameRu,
      name_eng: availableItem.nameEng,
      description_ru: availableItem.descriptionRu,
      unit_measure: availableItem.unitMeasure,
      price_net: availableItem.priceNet,
      vat_rate: availableItem.vatRate,
      vat_amount: availableItem.vatAmount,
      price_gross: availableItem.priceGross,
      price_gross_display: `${availableItem.priceGross.toFixed(2)} ${currencySymbol}`,
      line_total_display: `${lineTotal.line_gross_total.toFixed(2)} ${currencySymbol}`,
      is_available: lineTotal.is_available,
      stock_quantity: availableItem.stockQuantity
    }
  })

  // Calculate totals
  const totals = calculateCartTotals(cart, availableItems)
  const totalsVM = formatCartTotalsForDisplay(totals)

  // Validate cart
  const validation = validateCartAgainstAvailableItems(cart, availableItems)

  // Generate time displays
  const now = new Date()
  const timeDiff = Math.floor((now.getTime() - cart.updated_at.getTime()) / 1000)
  const lastUpdatedDisplay = formatTimeAgo(timeDiff)

  return {
    items: cartItemsVM,
    totals: totalsVM,
    is_empty: cart.items.length === 0,
    has_unavailable_items: !validation.is_valid,
    can_place_order: validation.is_valid && totals.total_items_count > 0,
    created_at: cart.created_at,
    updated_at: cart.updated_at,
    last_updated_display: lastUpdatedDisplay
  }
}

/**
 * Validate cart item before adding/updating
 */
export function validateCartItemOperation(
  itemId: number,
  quantity: number,
  availableItems: any[] // Accept both AvailableItem and AvailableItemVM
): {
  is_valid: boolean
  message: string
  available_item?: any
} {
  if (quantity <= 0) {
    return {
      is_valid: false,
      message: 'Quantity must be greater than 0'
    }
  }

  const availableItem = availableItems.find(item => item.itemId === itemId)

  if (!availableItem) {
    return {
      is_valid: false,
      message: `Item ${itemId} not found`
    }
  }

  // Check availability - supports both isActive (domain) and isAvailable (VM)
  const isItemActive = availableItem.isActive ?? availableItem.isAvailable ?? false

  if (!isItemActive) {
    return {
      is_valid: false,
      message: `Item "${availableItem.nameRu}" is currently unavailable`
    }
  }

  if (availableItem.stockQuantity <= 0) {
    return {
      is_valid: false,
      message: `Item "${availableItem.nameRu}" is out of stock`
    }
  }

  if (quantity > availableItem.stockQuantity) {
    return {
      is_valid: false,
      message: `Only ${availableItem.stockQuantity} units of "${availableItem.nameRu}" available`
    }
  }

  return {
    is_valid: true,
    message: 'Valid',
    available_item: availableItem
  }
}

/**
 * Helper function to format time ago
 */
function formatTimeAgo(seconds: number): string {
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  return `${Math.floor(seconds / 86400)} days ago`
}

/**
 * Get cart summary for display
 */
export function getCartSummary(cart: Cart): {
  total_items: number
  unique_items: number
  is_empty: boolean
} {
  return {
    total_items: cart.items.reduce((sum, item) => sum + item.quantity, 0),
    unique_items: cart.items.length,
    is_empty: cart.items.length === 0
  }
}