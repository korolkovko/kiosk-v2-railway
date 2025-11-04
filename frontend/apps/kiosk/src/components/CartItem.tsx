// File: src/components/CartItem.tsx
//
// Purpose:
// Display a single cart item with name, quantity, and price.
// Uses CartItemVM for enriched display data from cart store.

import { FunctionComponent } from "react";
import type { CartItemVM } from "../models/view/cart.vm";

export type CartItemType = {
  className?: string;
  cartItem: CartItemVM;
};

const CartItem: FunctionComponent<CartItemType> = ({
  className = "",
  cartItem,
}) => {
  return (
    <div
      className={`w-[25.75rem] flex flex-col items-start text-left text-[1.25rem] text-[#a7a7a7] font-['PT_Sans'] ${className}`}
    >
      <div className="self-stretch flex items-start py-[1.25rem] px-[0rem] gap-[0.625rem]">
        <div className="flex-1 relative uppercase font-medium flex items-center">
          {cartItem.name_ru}
        </div>
        <div className="flex items-start justify-end gap-[0.312rem] shrink-0">
          <span className="uppercase font-medium">
            {cartItem.quantity}
          </span>
          <span className="font-medium">x</span>
          <span className="font-medium whitespace-nowrap">
            {cartItem.price_gross_display}
          </span>
        </div>
      </div>
      <h3 className="m-0 relative text-[length:inherit] font-medium font-[inherit]">
        ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
      </h3>
    </div>
  );
};

export default CartItem;
