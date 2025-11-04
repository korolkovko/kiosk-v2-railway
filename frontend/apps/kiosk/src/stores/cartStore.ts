// File: src/stores/cartStore.ts
//
// Purpose:
// Zustand store for cart state management in kiosk.
// Provides fast, reactive cart operations for UI interactions.
// Handles cart items, navigation, and integrates with calculation services.

import { create } from 'zustand'
import type { Cart, CartItem } from '../models/domain/cart'
import type { CartVM, CartItemUpdateRequest } from '../models/view/cart.vm'
import {
  generateCartViewModel,
  addItemToCart as addItemToCartService,
  updateCartItem as updateCartItemService,
  clearCart as clearCartService,
  validateCartItemOperation
} from '../services/cartItemManagement.service'
import { CartLifecycleHelpers } from '../services/cartLifecycleManagement.service'

interface CartState {
  // Cart data
  cart: Cart
  cartVM: CartVM | null
  
  // Navigation state for fast cart item browsing
  activeCartItemIndex: number
  isCartNavigationActive: boolean
  
  // UI state
  isLoading: boolean
  lastError: string | null
}

interface CartActions {
  // Cart item management (now accept availableItems parameter)
  addItemToCart: (itemId: number, quantity?: number, wishes?: string | null, availableItems?: any[]) => void
  updateCartItem: (request: CartItemUpdateRequest, availableItems?: any[]) => void
  removeItemFromCart: (itemId: number, availableItems?: any[]) => void
  clearCart: () => void

  // Cart navigation (for keyboard/mouse interactions)
  setActiveCartItemIndex: (index: number) => void
  navigateCartItems: (direction: 'up' | 'down') => void
  activateCartNavigation: () => void
  deactivateCartNavigation: () => void

  // Cart operations (now accept availableItems parameter)
  refreshCartVM: (availableItems?: any[]) => Promise<void>
  validateCartItems: (availableItems?: any[]) => Promise<boolean>
  
  // Lifecycle management
  initializeEmptyCart: () => void
  resetCartState: () => void
  
  // Error handling
  setError: (error: string | null) => void
  clearError: () => void
}

type CartStore = CartState & CartActions

const initialCart: Cart = {
  items: [],
  created_at: new Date(),
  updated_at: new Date()
}

const initialState: CartState = {
  cart: initialCart,
  cartVM: null,
  activeCartItemIndex: 0,
  isCartNavigationActive: false,
  isLoading: false,
  lastError: null
}

export const useCartStore = create<CartStore>((set, get) => ({
  ...initialState,

  // Cart item management
  addItemToCart: (itemId: number, quantity = 1, wishes = null, availableItems = []) => {
    const { cart } = get()

    const result = addItemToCartService(cart, itemId, quantity, wishes, availableItems)

    if (result.success) {
      set({
        cart: result.updatedCart,
        lastError: null
      })

      // Track lifecycle event
      CartLifecycleHelpers.trackCartUpdate(result.updatedCart)

      // Refresh cart view model with available items
      get().refreshCartVM(availableItems)
    } else {
      set({ lastError: result.message })
      console.warn('Failed to add item to cart:', result.message)
    }
  },

  updateCartItem: (request: CartItemUpdateRequest, availableItems = []) => {
    const { cart } = get()

    const result = updateCartItemService(cart, request, availableItems)

    if (result.success) {
      set({
        cart: result.updatedCart,
        lastError: null
      })

      // Track lifecycle event
      CartLifecycleHelpers.trackCartUpdate(result.updatedCart)

      // Refresh cart view model with available items
      get().refreshCartVM(availableItems)
    } else {
      set({ lastError: result.message })
      console.warn('Failed to update cart item:', result.message)
    }
  },

  removeItemFromCart: (itemId: number, availableItems = []) => {
    get().updateCartItem({
      item_id: itemId,
      operation: 'remove'
    }, availableItems)
  },

  clearCart: () => {
    const { cart } = get()
    
    // Track lifecycle event before clearing
    CartLifecycleHelpers.trackCartClear('manual')
    
    const clearedCart = clearCartService()
    
    set({
      cart: clearedCart,
      cartVM: null,
      activeCartItemIndex: 0,
      lastError: null
    })
    
    console.log('🧹 Cart cleared manually')
  },

  // Cart navigation
  setActiveCartItemIndex: (index: number) => {
    const { cart } = get()
    const maxIndex = Math.max(0, cart.items.length - 1)
    const clampedIndex = Math.max(0, Math.min(index, maxIndex))
    
    set({ activeCartItemIndex: clampedIndex })
  },

  navigateCartItems: (direction: 'up' | 'down') => {
    const { activeCartItemIndex, cart } = get()
    const itemCount = cart.items.length
    
    if (itemCount === 0) return
    
    let newIndex: number
    if (direction === 'down') {
      newIndex = activeCartItemIndex < itemCount - 1 ? activeCartItemIndex + 1 : 0
    } else {
      newIndex = activeCartItemIndex > 0 ? activeCartItemIndex - 1 : itemCount - 1
    }
    
    get().setActiveCartItemIndex(newIndex)
  },

  activateCartNavigation: () => {
    set({ isCartNavigationActive: true })
  },

  deactivateCartNavigation: () => {
    set({ isCartNavigationActive: false })
  },

  // Cart operations with service integration
  refreshCartVM: async (availableItems = []) => {
    const { cart } = get()

    try {
      const cartVM = generateCartViewModel(cart, availableItems)

      set({
        cartVM,
        lastError: null
      })

      console.log('🔄 Cart VM refreshed:', {
        itemsCount: cartVM.items.length,
        totalGross: cartVM.totals.total_gross_amount_display
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh cart VM'
      set({ lastError: errorMessage })
      console.error('Failed to refresh cart VM:', error)
    }
  },

  validateCartItems: async (availableItems = []) => {
    const { cart } = get()

    try {
      // Validate each cart item
      for (const cartItem of cart.items) {
        const validation = validateCartItemOperation(
          cartItem.item_id,
          cartItem.quantity,
          availableItems
        )

        if (!validation.is_valid) {
          set({ lastError: validation.message })
          return false
        }
      }

      set({ lastError: null })
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Cart validation failed'
      set({ lastError: errorMessage })
      console.error('Cart validation error:', error)
      return false
    }
  },

  // Lifecycle management
  initializeEmptyCart: () => {
    const newCart: Cart = {
      items: [],
      created_at: new Date(),
      updated_at: new Date()
    }
    
    // Track lifecycle event
    CartLifecycleHelpers.initializeForCart(newCart)
    
    set({
      cart: newCart,
      cartVM: null,
      activeCartItemIndex: 0,
      isCartNavigationActive: false,
      lastError: null
    })
    
    console.log('🆕 Empty cart initialized')
  },

  resetCartState: () => {
    set(initialState)
  },

  // Error handling
  setError: (error: string | null) => {
    set({ lastError: error })
  },

  clearError: () => {
    set({ lastError: null })
  }
}))

// Selector hooks for optimized component subscriptions
export const useCartItems = () => useCartStore(state => state.cart.items)
export const useCartVM = () => useCartStore(state => state.cartVM)
export const useCartNavigation = () => useCartStore(state => ({
  activeCartItemIndex: state.activeCartItemIndex,
  isCartNavigationActive: state.isCartNavigationActive,
  navigateCartItems: state.navigateCartItems,
  setActiveCartItemIndex: state.setActiveCartItemIndex,
  activateCartNavigation: state.activateCartNavigation,
  deactivateCartNavigation: state.deactivateCartNavigation
}))
export const useCartActions = () => useCartStore(state => ({
  addItemToCart: state.addItemToCart,
  updateCartItem: state.updateCartItem,
  removeItemFromCart: state.removeItemFromCart,
  clearCart: state.clearCart,
  refreshCartVM: state.refreshCartVM,
  validateCartItems: state.validateCartItems
}))