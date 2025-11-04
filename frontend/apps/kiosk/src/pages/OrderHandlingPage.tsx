// OrderHandlingPage.tsx
// Dedicated page for handling order processing status display
// Isolates order processing logic from MainScreen for better code organization

import { FunctionComponent, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import OrderProcessingStatusesHandle from '../components/OrderProcessingStatusesHandle';
import { useOrder } from '../contexts/OrderContext';
import { useCartItems, useCartActions } from '../stores/cartStore';
import { useNavigationStore } from '../stores/navigationStore';
import { useCategories as useCategoriesContext } from '../contexts/CategoriesContext';
import { orderProcessingCleanupService } from '../services/orderProcessingCleanup.service';

const OrderHandlingPage: FunctionComponent = () => {
  const navigate = useNavigate();
  const { currentOrder, clearCurrentOrder } = useOrder();
  const cartItems = useCartItems();
  const { clearCart } = useCartActions();
  const { setActiveCategory, setNavigationMode } = useNavigationStore();
  const { categories } = useCategoriesContext();

  // Get promoted category name from first category
  const promotedCategoryName = categories.length > 0 ? categories[0].name : 'promoted';

  // Prevent page refresh/navigation during order processing
  // Shows browser warning: "Leave site? Changes you made may not be saved"
  // Triggers on: F5, Ctrl+R, tab close, browser back/forward, manual URL navigation
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = ''; // Modern browsers require this for the warning to show
      return ''; // Some browsers use the return value
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  // Redirect to main if no order exists (e.g., page refresh or direct navigation)
  useEffect(() => {
    if (!currentOrder) {
      console.log('⚠️ OrderHandlingPage: No order found, redirecting to /main');
      navigate('/main', { replace: true });
    }
  }, [currentOrder, navigate]);

  // When order processing completes successfully (after 5-second countdown)
  const handleComplete = useCallback(() => {
    console.log('📦 OrderHandlingPage: Order processing completed, performing cleanup');

    // Perform complete cleanup
    orderProcessingCleanupService.performCompleteCleanup(
      currentOrder,
      cartItems,
      {
        clearCart,
        clearCurrentOrder,
        setActiveCategory,
        setNavigationMode,
        showScreenSaver: () => {
          // Navigate back to main screen which will show screensaver
          navigate('/main', { replace: true });
        }
      },
      promotedCategoryName
    );
  }, [currentOrder, cartItems, clearCart, clearCurrentOrder, setActiveCategory, setNavigationMode, navigate, promotedCategoryName]);

  // When order processing fails (after 5-second countdown)
  const handleError = useCallback((error: string) => {
    console.error('❌ OrderHandlingPage: Order processing error:', error);

    // Perform error cleanup
    orderProcessingCleanupService.performErrorCleanup(
      currentOrder,
      {
        clearCart,
        clearCurrentOrder,
        setActiveCategory,
        setNavigationMode,
        showScreenSaver: () => {
          // Navigate back to main screen which will show screensaver
          navigate('/main', { replace: true });
        }
      },
      promotedCategoryName
    );
  }, [currentOrder, clearCart, clearCurrentOrder, setActiveCategory, setNavigationMode, navigate, promotedCategoryName]);

  return (
    <OrderProcessingStatusesHandle
      onComplete={handleComplete}
      onError={handleError}
    />
  );
};

export default OrderHandlingPage;
