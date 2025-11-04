// File: src/hooks/useCartOperations.ts
//
// Purpose:
// Bridge hook between cart store (Zustand) and items context (React Context).
// Provides clean interface for cart operations with available items data.
// Handles adding active item from navigation to cart.

import { useCallback, useEffect } from 'react'
import { useItems } from '../contexts/ItemsContext'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { useCartActions, useCartStore } from '../stores/cartStore'
import { useNavigationStore } from '../stores/navigationStore'
import { getItemsForCategory } from '../services/posterLogic.service'

/**
 * Hook for cart operations that need available items data
 * Bridges Zustand cart store with React Context items data
 */
export function useCartOperations() {
  // Get available items from context
  const { items: availableItems } = useItems()
  const { categories } = useCategoriesContext()

  // Get cart state and actions from Zustand store
  const cart = useCartStore(state => state.cart)
  const { addItemToCart, updateCartItem, removeItemFromCart, clearCart, refreshCartVM, validateCartItems } = useCartActions()

  // Get navigation state from store (avoiding circular dependency)
  const {
    activeItemIndex,
    activeCartItemIndex,
    activeCategory,
    navigationMode,
    setActiveCategory,
    setNavigationMode,
    setActiveCartItemIndex
  } = useNavigationStore()

  // Get promoted category name from first category
  const promotedCategoryName = categories.length > 0 ? categories[0].name : 'promoted'

  // Get current category items for item navigation
  const currentCategoryItems = activeCategory
    ? getItemsForCategory(activeCategory, availableItems, promotedCategoryName)
    : []

  // Watch for cart becoming empty in cart mode - exit to initial state
  useEffect(() => {
    if (navigationMode === 'cart' && cart.items.length === 0) {
      console.log('🔄 Cart is empty in cart mode, returning to initial state (first category)')
      // Return to initial state: categories mode with first category active
      if (categories.length > 0) {
        setActiveCategory(categories[0].name)
      }
      setNavigationMode('categories')
    }
  }, [navigationMode, cart.items.length, categories, setActiveCategory, setNavigationMode])

  /**
   * Add currently active item from ItemList to cart
   * This is the main operation triggered by + button/key
   */
  const addActiveItemToCart = useCallback(() => {
    console.log('🛒 addActiveItemToCart called', {
      navigationMode,
      activeItemIndex,
      currentCategoryItemsCount: currentCategoryItems.length
    })

    // Only works in items navigation mode
    if (navigationMode !== 'items') {
      console.warn('⚠️ Cannot add to cart: not in items mode')
      return
    }

    // Get the active item
    const activeItem = currentCategoryItems[activeItemIndex]

    if (!activeItem) {
      console.warn('⚠️ Cannot add to cart: no active item')
      return
    }

    console.log('✅ Attempting to add item:', {
      itemId: activeItem.itemId,
      nameRu: activeItem.nameRu,
      priceGross: activeItem.priceGross,
      isActive: activeItem.isActive,
      stockQuantity: activeItem.stockQuantity
    })

    // Debug: Check all available items
    console.log('📦 All available items:', availableItems.map(item => ({
      itemId: item.itemId,
      nameRu: item.nameRu,
      isActive: item.isActive,
      stockQuantity: item.stockQuantity
    })))

    // Add to cart with quantity 1, no wishes
    // Pass availableItems to cart store action
    addItemToCart(activeItem.itemId, 1, null, availableItems)
  }, [navigationMode, activeItemIndex, currentCategoryItems, addItemToCart, availableItems])

  /**
   * Remove/decrease currently active item from cart
   * Decreases quantity by 1, removes if quantity becomes 0
   */
  const removeActiveItemFromCart = useCallback(() => {
    console.log('🛒 removeActiveItemFromCart called', {
      navigationMode,
      activeItemIndex,
      currentCategoryItemsCount: currentCategoryItems.length
    })

    // Only works in items navigation mode
    if (navigationMode !== 'items') {
      console.warn('⚠️ Cannot remove from cart: not in items mode')
      return
    }

    // Get the active item
    const activeItem = currentCategoryItems[activeItemIndex]

    if (!activeItem) {
      console.warn('⚠️ Cannot remove from cart: no active item')
      return
    }

    // Find this item in the cart
    const cartItem = cart.items.find(item => item.item_id === activeItem.itemId)

    if (!cartItem) {
      console.warn('⚠️ Item not in cart:', activeItem.nameRu)
      return
    }

    console.log('✅ Attempting to remove/decrease item:', {
      itemId: activeItem.itemId,
      nameRu: activeItem.nameRu,
      currentQuantity: cartItem.quantity
    })

    // If quantity is 1, remove the item completely
    // Otherwise, decrease quantity by 1
    const newQuantity = cartItem.quantity - 1

    if (newQuantity <= 0) {
      removeItemFromCart(activeItem.itemId, availableItems)
    } else {
      updateCartItem({
        item_id: activeItem.itemId,
        quantity: newQuantity,
        operation: 'update'
      }, availableItems)
    }
  }, [navigationMode, activeItemIndex, currentCategoryItems, cart.items, updateCartItem, removeItemFromCart, availableItems])

  /**
   * Wrapper for refreshCartVM that passes availableItems
   */
  const refreshCart = useCallback(() => {
    refreshCartVM(availableItems)
  }, [refreshCartVM, availableItems])

  /**
   * Wrapper for validateCartItems that passes availableItems
   */
  const validateCart = useCallback(() => {
    return validateCartItems(availableItems)
  }, [validateCartItems, availableItems])

  /**
   * Add item from cart (when in cart mode)
   * Increases quantity of the active cart item by 1
   */
  const addActiveCartItemToCart = useCallback(() => {
    if (navigationMode !== 'cart') {
      console.warn('⚠️ Cannot add cart item: not in cart mode')
      return
    }

    const cartItem = cart.items[activeCartItemIndex]
    if (!cartItem) {
      console.warn('⚠️ No active cart item to add')
      return
    }

    const newQuantity = cartItem.quantity + 1
    updateCartItem({
      item_id: cartItem.item_id,
      quantity: newQuantity,
      operation: 'update'
    }, availableItems)
  }, [navigationMode, activeCartItemIndex, cart.items, updateCartItem, availableItems])

  /**
   * Remove/decrease item from cart (when in cart mode)
   * Decreases quantity by 1, removes if quantity becomes 0
   */
  const removeActiveCartItemFromCart = useCallback(() => {
    if (navigationMode !== 'cart') {
      console.warn('⚠️ Cannot remove cart item: not in cart mode')
      return
    }

    const cartItem = cart.items[activeCartItemIndex]
    if (!cartItem) {
      console.warn('⚠️ No active cart item to remove')
      return
    }

    const newQuantity = cartItem.quantity - 1
    if (newQuantity <= 0) {
      // Item will be removed - adjust index if needed
      const cartLengthAfterRemoval = cart.items.length - 1
      if (activeCartItemIndex >= cartLengthAfterRemoval && cartLengthAfterRemoval > 0) {
        // Focus was on last item, move to new last item
        setActiveCartItemIndex(cartLengthAfterRemoval - 1)
      }
      removeItemFromCart(cartItem.item_id, availableItems)
    } else {
      updateCartItem({
        item_id: cartItem.item_id,
        quantity: newQuantity,
        operation: 'update'
      }, availableItems)
    }
  }, [navigationMode, activeCartItemIndex, cart.items, updateCartItem, removeItemFromCart, availableItems, setActiveCartItemIndex])

  /**
   * Delete all quantity of active cart item (Delete key)
   * Removes the item completely from cart
   */
  const deleteActiveCartItem = useCallback(() => {
    if (navigationMode !== 'cart') {
      console.warn('⚠️ Cannot delete cart item: not in cart mode')
      return
    }

    const cartItem = cart.items[activeCartItemIndex]
    if (!cartItem) {
      console.warn('⚠️ No active cart item to delete')
      return
    }

    console.log('🗑️ Deleting cart item completely:', cartItem.item_id)

    // Adjust index if needed before deleting
    const cartLengthAfterRemoval = cart.items.length - 1
    if (activeCartItemIndex >= cartLengthAfterRemoval && cartLengthAfterRemoval > 0) {
      // Focus was on last item, move to new last item
      setActiveCartItemIndex(cartLengthAfterRemoval - 1)
    }

    removeItemFromCart(cartItem.item_id, availableItems)
  }, [navigationMode, activeCartItemIndex, cart.items, removeItemFromCart, availableItems, setActiveCartItemIndex])

  return {
    // Main operations (item mode)
    addActiveItemToCart,
    removeActiveItemFromCart,

    // Cart mode operations
    addActiveCartItemToCart,
    removeActiveCartItemFromCart,
    deleteActiveCartItem,

    // Wrapped operations with availableItems
    refreshCart,
    validateCart,

    // Direct cart operations (no availableItems needed)
    clearCart,

    // State info
    hasAvailableItems: availableItems.length > 0
  }
}
