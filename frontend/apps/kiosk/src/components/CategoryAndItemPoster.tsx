// File: src/components/CategoryAndItemPoster.tsx
//
// Purpose:
// Dynamic poster component that displays both category and item posters.
// - Shows category poster when navigating categories
// - Shows item poster when navigating items within a category

import { FunctionComponent } from 'react'
import { useItems } from '../contexts/ItemsContext'
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext'
import { useNavigationStore } from '../stores/navigationStore'
import { useCartItems } from '../stores/cartStore'
import { getItemsForCategory } from '../services/posterLogic.service'
import MediaDisplay from './MediaDisplay'

export type CategoryAndItemPosterType = {
  className?: string
  activeCategory: string | null
}

const CategoryAndItemPoster: FunctionComponent<CategoryAndItemPosterType> = ({
  className = "",
  activeCategory
}) => {
  const { items: availableItems } = useItems()
  const { categories } = useCategoriesContext()
  const { navigationMode, activeItemIndex, activeCartItemIndex } = useNavigationStore()
  const cartItems = useCartItems()

  // Get promoted category name from first category
  const promotedCategoryName = categories.length > 0 ? categories[0].name : 'promoted'

  // Get current category items
  const currentCategoryItems = activeCategory
    ? getItemsForCategory(activeCategory, availableItems, promotedCategoryName)
    : []

  // Get selected item based on navigation mode
  let selectedItem = null

  if (navigationMode === 'items' && activeItemIndex !== null && currentCategoryItems[activeItemIndex]) {
    selectedItem = currentCategoryItems[activeItemIndex]
  } else if (navigationMode === 'cart' && activeCartItemIndex !== null && cartItems[activeCartItemIndex]) {
    // In cart mode, get item from cart, then find it in available items
    const cartItem = cartItems[activeCartItemIndex]
    selectedItem = availableItems.find(item => item.itemId === cartItem.item_id) || null
  }

  // Determine cache key based on what we're showing
  // Priority: selected item > category poster
  let cacheKey: string
  let altText: string

  if (selectedItem) {
    // Show item poster
    cacheKey = `item_${selectedItem.itemId}`
    altText = selectedItem.nameRu
  } else {
    // Show category poster - check if items are available to determine which variant
    const category = activeCategory || promotedCategoryName
    const categoryLower = category.toLowerCase()

    // Promoted category always uses regular poster (no unavailable variant)
    if (categoryLower === promotedCategoryName.toLowerCase()) {
      cacheKey = `category_${category}`
      altText = 'Promoted items'
    } else {
      // Check if category has available items
      const hasAvailableItems = currentCategoryItems.some(item =>
        item.isAvailable && item.stockQuantity > 0
      )

      // Use regular or unavailable variant based on availability
      cacheKey = hasAvailableItems
        ? `category_${category}`
        : `category_${category}_unavailable`

      altText = hasAvailableItems
        ? `${category} category`
        : `${category} category - currently unavailable`
    }
  }

  return (
    <MediaDisplay
      cacheKey={cacheKey}
      className={`h-[67.5rem] flex-1 relative max-w-full overflow-hidden object-cover min-w-[27.188rem] mq900:min-w-full ${className}`}
      loading="lazy"
      alt={altText}
    />
  )
}

export default CategoryAndItemPoster