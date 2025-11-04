// File: src/pages/MainScreen.tsx
import { FunctionComponent, useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import CategoryItem from "../components/CategoryItem";
import CategoryAndItemPoster from "../components/CategoryAndItemPoster";
import DividersVertical from "../components/DividersVertical";
import ItemList from "../components/ItemList";
import Cart from "../components/Cart";
import PlusToCartButton from "../components/PlusToCartButton";
import MinusFromCartButton from "../components/MinusFromCartButton";
import EightButton from "../components/EightButton";
import NineButton from "../components/NineButton";
import InactivityOverlay from "../components/InactivityOverlay";
import ScreenSaver from "../components/ScreenSaver";
import { useItems } from "../contexts/ItemsContext";
import { useKioskNavigation } from "../hooks/useKioskNavigation";
import { useCartOperations } from "../hooks/useCartOperations";
import { useInactivityDetection } from "../hooks/useInactivityDetection";
import { useScreenSaver } from "../hooks/useScreenSaver";
import { useCartItems, useCartActions, useCartVM } from "../stores/cartStore";
import { useNavigationStore } from "../stores/navigationStore";
import { useOrder } from "../contexts/OrderContext";
import { useOrderProcessingLifecycle } from "../hooks/useOrderProcessingLifecycle";
import { useKioskCleanup } from "../hooks/useKioskCleanup";

const MainScreen: FunctionComponent = () => {
  // Get auth context for order progress tracking
  const { setOrderInProgress } = useAuth();

  // Mount/unmount tracepoints to validate timer cleanup on navigation
  useEffect(() => {
    console.log('🟢 MainScreen mounted');
    return () => {
      console.log('🔴 MainScreen unmounted');
    };
  }, []);

  // Get available items from context (single source of truth)
  const { connectionStatus } = useItems();

  // Get cart items and cart VM for order placement
  const cartItems = useCartItems();
  const cartVM = useCartVM();

  // Cart operations hook (bridges cart store with items context)
  const {
    addActiveItemToCart,
    removeActiveItemFromCart,
    addActiveCartItemToCart,
    removeActiveCartItemFromCart,
    deleteActiveCartItem
  } = useCartOperations();

  // React Router navigation
  const navigate = useNavigate();

  // Get navigationMode from store first (needed for callbacks)
  const { navigationMode, navigateToCart, navigateBackFromCart, navigateBackFromOrderProcessing, setActiveCategory, setNavigationMode } = useNavigationStore();

  // Get cart actions for clearing
  const { clearCart } = useCartActions();

  // Order context for managing current order
  const { clearCurrentOrder } = useOrder();

  // Screen saver state (shown on mount and after inactivity timeout)
  const { isScreenSaverVisible, showScreenSaver, hideScreenSaver } = useScreenSaver(true); // true = show on mount

  // Navigate to order handling page
  const navigateToOrderHandling = useCallback(() => {
    navigate('/order-handling');
  }, [navigate]);

  // Order processing lifecycle hook (extracted from MainScreen)
  const {
    isPlacingOrder,
    handlePlaceOrder: handlePlaceOrderFromHook
  } = useOrderProcessingLifecycle({
    clearCart,
    clearCurrentOrder,
    setActiveCategory,
    setNavigationMode,
    showScreenSaver,
    navigateBackFromOrderProcessing,
    navigateToOrderProcessing: navigateToOrderHandling,
    setOrderInProgress
  });

  // Proxy for wiring live resetActivity into useKioskCleanup without changing hooks order
  const inactivityResetRef = useRef<() => void>(() => {});
  // Kiosk cleanup hook (extracted from MainScreen)
  const {
    handleInactivityTimeout,
    handleInactivityReset
  } = useKioskCleanup({
    clearCart,
    clearCurrentOrder,
    setActiveCategory,
    setNavigationMode,
    showScreenSaver,
    navigateBackFromOrderProcessing
  }, () => inactivityResetRef.current()); // use live resetActivity when available
  // Create wrapper functions to bridge hook interfaces with component interfaces
  const handlePlaceOrder = useCallback(async () => {
    if (cartItems.length === 0) return;
    await handlePlaceOrderFromHook(cartItems, cartVM);
  }, [cartItems, cartVM, handlePlaceOrderFromHook]);

  // Toggle cart mode handler
  const handleToggleCartMode = useCallback(() => {
    if (navigationMode === 'cart') {
      navigateBackFromCart();
    } else if (cartItems.length > 0) {
      navigateToCart();
    }
  }, [navigationMode, cartItems.length, navigateBackFromCart, navigateToCart]);

  // Handler for +/- operations (works in both items and cart mode)
  const handlePlusKey = useCallback(() => {
    if (navigationMode === 'items') {
      addActiveItemToCart();
    } else if (navigationMode === 'cart') {
      addActiveCartItemToCart();
    }
  }, [navigationMode, addActiveItemToCart, addActiveCartItemToCart]);

  const handleMinusKey = useCallback(() => {
    if (navigationMode === 'items') {
      removeActiveItemFromCart();
    } else if (navigationMode === 'cart') {
      removeActiveCartItemFromCart();
    }
  }, [navigationMode, removeActiveItemFromCart, removeActiveCartItemFromCart]);

  // Navigation hook for kiosk interactions
  const {
    activeCategory,
    categories,
    handleCategoryHover,
    handleCategorySelect,
    handleCartItemHover,
    isCategoryActive,
    isCartItemActive
  } = useKioskNavigation(
    handlePlusKey,
    handleMinusKey,
    deleteActiveCartItem,
    handleToggleCartMode,
    handlePlaceOrder  // Pass order placement handler for "9" key
  );


  // Inactivity detection - always active (even at start state)
  // This ensures screensaver acts as attract screen, drawing customers back
  // IMPORTANT: Disabled when screensaver is visible OR during order processing
  const { isInactive, countdown, resetActivity } = useInactivityDetection({
    idleTimeout: 20000, // 20 seconds
    countdownDuration: 10, // 10 seconds countdown
    onTimeout: handleInactivityTimeout,
    disabled: isScreenSaverVisible || navigationMode === 'order_processing' // Pause during order processing
  });

  // Wire the real resetActivity into the cleanup hook via ref
  useEffect(() => {
    inactivityResetRef.current = resetActivity;
  }, [resetActivity]);


  // Order processing is now handled by OrderHandlingPage (separate route)
  // No need to render anything special here - navigation handles it

  return (
    <div className="w-full relative bg-[#fff] overflow-hidden flex items-center flex-wrap content-center gap-[0rem] leading-[normal] tracking-[normal] [row-gap:20px]">
      <section className="h-[67.5rem] bg-[#000] overflow-hidden flex flex-col items-start pt-[1.875rem] pb-[0rem] pl-[1.875rem] pr-[0.625rem] box-border gap-[27.75rem] text-left text-[2.063rem] text-[#fff] font-['PT_Sans'] mq450:gap-[13.875rem]">
        <div className="flex flex-col items-start gap-[1.25rem]">
          <div className="overflow-hidden flex items-center justify-center py-[0rem] pl-[0rem] pr-[1.25rem] z-[2]">
            <h1 className="m-0 relative text-[length:inherit] font-bold font-[inherit] mq900:text-[1.625rem] mq450:text-[1.25rem]">
              Zero Culture®
            </h1>
          </div>
          <div className="w-[16.25rem] flex flex-col items-start z-[1] text-[1.625rem]">
            {/* Dynamic categories from backend with navigation */}
            {categories.map((category) => (
              <CategoryItem
                key={category.name}
                categoryName={category.name}
                categoryItemText={category.displayName}
                categoryItemWidth="auto"
                isActive={isCategoryActive(category.name)}
                onHover={handleCategoryHover}
                onClick={handleCategorySelect}
                disableInteraction={navigationMode === 'cart'}
              />
            ))}
            <div className="self-stretch flex flex-col items-start pt-[0rem] px-[0rem] pb-[0.625rem] gap-[0.625rem] text-[#a7a7a7]">
              <div className="self-stretch relative font-medium mq450:text-[1.313rem]">
                ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
              </div>
              <div className="self-stretch relative font-medium mq450:text-[1.313rem]">
                ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
              </div>
              <div className="self-stretch relative font-medium mq450:text-[1.313rem]">
                ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
              </div>
            </div>
            <CategoryItem
              property1="Default"
              categoryItemWidth="8.625rem"
              categoryItemText="[8] Edit cart"
            />
            <CategoryItem
              property1="Default"
              categoryItemWidth="10.688rem"
              categoryItemText="[9] Make order"
            />
          </div>
        </div>
        {/* SSE Connection Status Indicator */}
        <div className="w-[15.5rem] flex flex-col items-start gap-[0.5rem] text-[0.875rem]">
          <div className={`px-[0.5rem] py-[0.25rem] rounded ${
            connectionStatus.connected
              ? 'bg-green-600 text-white'
              : connectionStatus.reconnecting
                ? 'bg-yellow-600 text-white'
                : 'bg-red-600 text-white'
          }`}>
            {connectionStatus.connected
              ? '● Live Updates Active'
              : connectionStatus.reconnecting
                ? '⟳ Reconnecting...'
                : '● Offline Mode'}
          </div>
        </div>
        <div className="w-[15.5rem] flex flex-col items-start justify-end py-[1.875rem] px-[0rem] box-border gap-[0.312rem] z-[1] text-[1.5rem]">
          <h3 className="m-0 self-stretch relative text-[length:inherit] font-medium font-[inherit] mq450:text-[1.188rem]">
            Press [9] to make order
          </h3>
          <h3 className="m-0 self-stretch relative text-[length:inherit] font-medium font-[inherit] mq450:text-[1.188rem]">
            Press [8] to edit cart
          </h3>
        </div>
      </section>
      <DividersVertical />
      <ItemList disableInteraction={navigationMode === 'cart'} />
      <DividersVertical />
      <div className="h-[67.5rem] flex-1 relative min-w-[27.188rem] mq900:min-w-full">
        <CategoryAndItemPoster activeCategory={activeCategory} />
        {/* Cart control buttons positioned at bottom center of poster section */}
        <div className="absolute bottom-[2.5rem] left-0 right-0 flex items-center justify-center gap-[1rem]">
          <NineButton
            onClick={handlePlaceOrder}
            disabled={cartItems.length === 0}
            isLoading={isPlacingOrder}
          />
          <EightButton
            onClick={handleToggleCartMode}
            disabled={cartItems.length === 0}
          />
          <MinusFromCartButton onClick={handleMinusKey} />
          <PlusToCartButton onClick={handlePlusKey} />
        </div>
      </div>
      <DividersVertical />
      <Cart
        onCartItemHover={handleCartItemHover}
        isCartItemActive={isCartItemActive}
      />

      {/* Inactivity overlay - shown after idle timeout */}
      <InactivityOverlay
        isVisible={isInactive}
        countdown={countdown}
        onCancel={resetActivity}
        onReset={handleInactivityReset}
      />

      {/* Screen saver - shown on mount (after login) and after inactivity timeout */}
      <ScreenSaver
        isVisible={isScreenSaverVisible}
        onDismiss={() => {
          hideScreenSaver();
          resetActivity(); // Reset inactivity timer when screensaver is dismissed

          // Reset navigation to first category (promoted) for fresh start
          // Ensures consistent behavior: screensaver dismissal = fresh start from promoted items
          if (categories.length > 0) {
            setActiveCategory(categories[0].name);
          }
          setNavigationMode('categories');
        }}
      />
    </div>
  );
};

export default MainScreen;
