// File: src/components/PlusToCartButton.tsx
//
// Purpose:
// "+" button component for adding active item to cart.
// Triggers cart add operation via onClick handler.
// Used for touch interface testing without keyboard.

import { FunctionComponent } from "react";

export type PlusToCartButtonType = {
  className?: string;
  onClick?: () => void;
};

const PlusToCartButton: FunctionComponent<PlusToCartButtonType> = ({
  className = "",
  onClick
}) => {
  return (
    <button
      onClick={onClick}
      className={`cursor-pointer bg-[transparent] border-none flex items-center justify-center hover:opacity-70 ${className}`}
    >
      <div className="text-[5rem] font-bold font-['PT_Sans'] text-[#a7a7a7] leading-none">
        +
      </div>
    </button>
  );
};

export default PlusToCartButton;
