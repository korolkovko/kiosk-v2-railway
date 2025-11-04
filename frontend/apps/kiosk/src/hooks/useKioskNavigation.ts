// File: src/hooks/useKioskNavigation.ts
//
// Purpose:
// Custom hook for handling kiosk keyboard and mouse navigation.
// Manages arrow keys, enter, mouse interactions for category and item navigation.
// Works with navigation store and available data from contexts.

import { useEffect, useCallback } from 'react'
import { useNavigationStore } from '../stores/navigationStore'
import { useCategories } from './useCategories'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { useItems } from '../contexts/ItemsContext'
import { useCartItems } from '../stores/cartStore'
import { getItemsForCategory } from '../services/posterLogic.service'

export function useKioskNavigation(
  onPlusKeyPressed?: () => void,
  onMinusKeyPressed?: () => void,
  onDeleteKeyPressed?: () => void,
  onEightKeyPressed?: () => void,
  onNineKeyPressed?: () => void
) {
  const {
    activeCategory,
    activeItemIndex,
    activeCartItemIndex,
    navigationMode,
    setActiveCategory,
    setActiveItemIndex,
    setActiveCartItemIndex,
    navigateToItems,
    navigateBackToCategories,
    navigateToCart,
    navigateBackFromCart
  } = useNavigationStore()

  const { categories } = useCategories()
  const { categories: allCategories } = useCategoriesContext()
  const { items: availableItems } = useItems()
  const cartItems = useCartItems()

  // Get promoted category name from first category
  const promotedCategoryName = allCategories.length > 0 ? allCategories[0].name : 'promoted'

  // Get current category items for item navigation
  const currentCategoryItems = activeCategory
    ? getItemsForCategory(activeCategory, availableItems, promotedCategoryName)
    : []

  /**
   * Navigate up/down in categories
   */
  const navigateCategories = useCallback((direction: 'up' | 'down') => {
    if (categories.length === 0) return

    const currentIndex = categories.findIndex(cat => cat.name === activeCategory)
    let newIndex: number

    if (direction === 'down') {
      newIndex = currentIndex < categories.length - 1 ? currentIndex + 1 : 0
    } else {
      newIndex = currentIndex > 0 ? currentIndex - 1 : categories.length - 1
    }

    setActiveCategory(categories[newIndex].name)
  }, [categories, activeCategory, setActiveCategory])

  /**
   * Navigate up/down in items within current category
   */
  const navigateItems = useCallback((direction: 'up' | 'down') => {
    if (currentCategoryItems.length === 0) return

    let newIndex: number

    if (direction === 'down') {
      newIndex = activeItemIndex < currentCategoryItems.length - 1
        ? activeItemIndex + 1
        : 0
    } else {
      newIndex = activeItemIndex > 0
        ? activeItemIndex - 1
        : currentCategoryItems.length - 1
    }

    setActiveItemIndex(newIndex)
  }, [currentCategoryItems.length, activeItemIndex, setActiveItemIndex])

  /**
   * Navigate up/down in cart items
   */
  const navigateCartItems = useCallback((direction: 'up' | 'down') => {
    if (cartItems.length === 0) return

    let newIndex: number

    if (direction === 'down') {
      newIndex = activeCartItemIndex < cartItems.length - 1
        ? activeCartItemIndex + 1
        : 0
    } else {
      newIndex = activeCartItemIndex > 0
        ? activeCartItemIndex - 1
        : cartItems.length - 1
    }

    setActiveCartItemIndex(newIndex)
  }, [cartItems.length, activeCartItemIndex, setActiveCartItemIndex])

  /**
   * Handle keyboard events
   */
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault()
        if (navigationMode === 'categories') {
          navigateCategories('up')
        } else if (navigationMode === 'items') {
          navigateItems('up')
        } else if (navigationMode === 'cart') {
          navigateCartItems('up')
        }
        break

      case 'ArrowDown':
        event.preventDefault()
        if (navigationMode === 'categories') {
          navigateCategories('down')
        } else if (navigationMode === 'items') {
          navigateItems('down')
        } else if (navigationMode === 'cart') {
          navigateCartItems('down')
        }
        break

      case 'ArrowRight':
        event.preventDefault()
        if (navigationMode === 'categories' && activeCategory) {
          // Only allow navigation to items if category has items
          if (currentCategoryItems.length > 0) {
            navigateToItems()
          }
        }
        break

      case 'Enter':
        event.preventDefault()
        if (navigationMode === 'categories' && activeCategory) {
          // Only allow navigation to items if category has items
          if (currentCategoryItems.length > 0) {
            navigateToItems()
          }
        } else if (navigationMode === 'items' && onPlusKeyPressed) {
          // In items mode, Enter adds to cart (same as +)
          onPlusKeyPressed()
        }
        break

      case 'ArrowLeft':
        event.preventDefault()
        if (navigationMode === 'items') {
          navigateBackToCategories()
        }
        break

      case 'Escape':
        event.preventDefault()
        if (navigationMode === 'cart') {
          navigateBackFromCart()
        } else {
          navigateBackToCategories()
        }
        break

      case '+':
      case '=': // + key without shift
        event.preventDefault()
        if (navigationMode === 'items' && onPlusKeyPressed) {
          onPlusKeyPressed()
        } else if (navigationMode === 'cart' && onPlusKeyPressed) {
          onPlusKeyPressed()
        }
        break

      case '-':
      case '_': // - key with shift
        event.preventDefault()
        if (navigationMode === 'items' && onMinusKeyPressed) {
          onMinusKeyPressed()
        } else if (navigationMode === 'cart' && onMinusKeyPressed) {
          onMinusKeyPressed()
        }
        break

      case 'Delete':
      case 'Backspace':
        event.preventDefault()
        if (navigationMode === 'cart' && onDeleteKeyPressed) {
          // In cart mode, Delete removes item completely
          onDeleteKeyPressed()
        } else if (navigationMode === 'items' && onMinusKeyPressed) {
          // In items mode, Delete removes from cart (same as -)
          onMinusKeyPressed()
        }
        break

      case '8':
        event.preventDefault()
        if (onEightKeyPressed) {
          onEightKeyPressed()
        }
        break

      case '9':
        event.preventDefault()
        if (onNineKeyPressed) {
          onNineKeyPressed()
        }
        break
    }
  }, [
    navigationMode,
    activeCategory,
    navigateCategories,
    navigateItems,
    navigateCartItems,
    navigateToItems,
    navigateBackToCategories,
    navigateBackFromCart,
    onPlusKeyPressed,
    onMinusKeyPressed,
    onDeleteKeyPressed,
    onEightKeyPressed,
    onNineKeyPressed
  ])

  /**
   * Handle category hover (mouse navigation)
   */
  const handleCategoryHover = useCallback((categoryName: string) => {
    // Only allow hover in categories mode, not in items or cart mode
    if (navigationMode === 'categories') {
      setActiveCategory(categoryName)
    }
  }, [navigationMode, setActiveCategory])

  /**
   * Handle category click/selection
   */
  const handleCategorySelect = useCallback((categoryName: string) => {
    if (navigationMode === 'cart') return // Disable in cart mode
    setActiveCategory(categoryName)

    // Check if the selected category has items before navigating
    const categoryItems = getItemsForCategory(categoryName, availableItems, promotedCategoryName)
    if (categoryItems.length > 0) {
      navigateToItems()
    }
  }, [navigationMode, setActiveCategory, navigateToItems, availableItems, promotedCategoryName])

  /**
   * Handle item hover (mouse navigation)
   */
  const handleItemHover = useCallback((itemIndex: number) => {
    if (navigationMode === 'items') {
      setActiveItemIndex(itemIndex)
    }
  }, [navigationMode, setActiveItemIndex])

  /**
   * Handle cart item hover (mouse navigation)
   */
  const handleCartItemHover = useCallback((cartItemIndex: number) => {
    if (navigationMode === 'cart') {
      setActiveCartItemIndex(cartItemIndex)
    }
  }, [navigationMode, setActiveCartItemIndex])

  // Set up keyboard event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  // Initialize with first category if none selected
  useEffect(() => {
    if (!activeCategory && categories.length > 0) {
      setActiveCategory(categories[0].name)
    }
  }, [activeCategory, categories, setActiveCategory])

  return {
    // Current state
    activeCategory,
    activeItemIndex,
    activeCartItemIndex,
    navigationMode,
    currentCategoryItems,
    categories, // Expose categories for components that need the full list

    // Navigation handlers
    handleCategoryHover,
    handleCategorySelect,
    handleItemHover,
    handleCartItemHover,
    navigateBackToCategories,
    navigateToCart,
    navigateBackFromCart,

    // Utility functions
    isCategoryActive: (categoryName: string) => categoryName === activeCategory && navigationMode !== 'cart',
    isItemActive: (itemIndex: number) => itemIndex === activeItemIndex && navigationMode === 'items',
    isCartItemActive: (cartItemIndex: number) => cartItemIndex === activeCartItemIndex && navigationMode === 'cart'
  }
}