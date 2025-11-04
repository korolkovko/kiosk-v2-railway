// File: src/components/Cart.tsx
//
// Purpose:
// Display cart contents with items list, totals, and action buttons.
// Uses CartVM from cart store for reactive display of cart state.

import { FunctionComponent, useRef, useEffect } from "react";
import CartItem from "./CartItem";
import { useCartVM } from "../stores/cartStore";
import { useNavigationStore } from "../stores/navigationStore";

export type CartType = {
  className?: string;
  onCartItemHover?: (index: number) => void;
  isCartItemActive?: (index: number) => boolean;
};

const Cart: FunctionComponent<CartType> = ({
  className = "",
  onCartItemHover,
  isCartItemActive
}) => {
  const cartVM = useCartVM();
  const { navigationMode, activeCartItemIndex } = useNavigationStore();

  const items = cartVM?.items || [];
  const totals = cartVM?.totals;
  const isEmpty = cartVM?.is_empty ?? true;

  // Refs for cart items to enable auto-scrolling
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Auto-scroll to active item when navigating with keyboard
  useEffect(() => {
    if (navigationMode === 'cart' && activeCartItemIndex >= 0 && itemRefs.current[activeCartItemIndex]) {
      itemRefs.current[activeCartItemIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }, [activeCartItemIndex, navigationMode]);

  return (
    <section
      className={`h-[67.5rem] w-[28.5rem] bg-[#000] overflow-hidden flex flex-col items-start py-[1.875rem] px-[1.25rem] box-border gap-[0.937rem] max-w-full text-left text-[1.5rem] text-[#fff] font-['PT_Sans'] mq900:pt-[1.25rem] mq900:pb-[1.25rem] mq900:box-border ${className}`}
    >
      <div className="self-stretch h-[2.563rem] flex items-start text-[2.063rem]">
        <h2 className="m-0 relative text-[length:inherit] font-bold font-[inherit] mq900:text-[1.625rem] mq450:text-[1.25rem]">
          You Order
        </h2>
      </div>

      {/* Scrollable cart items section */}
      <div className="self-stretch flex-1 flex flex-col items-start overflow-y-auto text-[1.25rem] text-[#a7a7a7]">
        {isEmpty ? (
          <div className="self-stretch flex items-center justify-center py-[2rem] text-[#a7a7a7]">
            No items in cart yet
          </div>
        ) : (
          items.map((item, index) => {
            const isActive = isCartItemActive ? isCartItemActive(index) : false;
            const canHover = navigationMode === 'cart';

            return (
              <div
                key={item.item_id}
                ref={(el) => (itemRefs.current[index] = el)}
                className={`w-full ${isActive ? 'bg-[#ffffff1a]' : ''} ${canHover ? 'hover:bg-[#ffffff0d] cursor-pointer' : ''}`}
                onMouseEnter={() => canHover && onCartItemHover && onCartItemHover(index)}
              >
                <CartItem cartItem={item} />
              </div>
            );
          })
        )}
      </div>

      <div className="self-stretch h-[3.25rem] flex items-center justify-end py-[0.687rem] px-[0rem] box-border text-right">
        <h3 className="m-0 relative text-[length:inherit] font-bold font-[inherit] mq450:text-[1.188rem]">
          Итого {totals?.total_gross_amount_display || '0 ₽'}
        </h3>
      </div>

      <div className="self-stretch flex flex-col items-start gap-[0.625rem] text-center">
        <button className="cursor-pointer border-[#a7a7a7] border-solid border-[2px] py-[0.437rem] px-[0rem] bg-[transparent] self-stretch flex items-center justify-center hover:bg-[rgba(117,117,117,0.09)] hover:border-[#757575] hover:border-solid hover:hover:border-[2px] hover:box-border">
          <div className="flex-1 relative text-[1.5rem] font-medium font-['PT_Sans'] text-[#fff] text-center mq450:text-[1.188rem]">
            <p className="m-0">Press 9 to make order</p>
            <p className="m-0">or 8 to edit cart</p>
          </div>
        </button>
        <h3 className="m-0 self-stretch relative text-[length:inherit] font-medium font-[inherit] mq450:text-[1.188rem]">
          Basic people can't tell what it is®
        </h3>
      </div>
    </section>
  );
};

export default Cart;
