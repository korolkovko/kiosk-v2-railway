// File: src/components/MinusFromCartButton.tsx
//
// Purpose:
// Simple "-" button component for removing items from cart.
// Visual element only - logic will be added later.
// Used for touch interface testing without keyboard.

import { FunctionComponent } from "react";

export type MinusFromCartButtonType = {
  className?: string;
  onClick?: () => void;
};

const MinusFromCartButton: FunctionComponent<MinusFromCartButtonType> = ({
  className = "",
  onClick
}) => {
  return (
    <button
      onClick={onClick}
      className={`cursor-pointer bg-[transparent] border-none flex items-center justify-center hover:opacity-70 ${className}`}
    >
      <div className="text-[5rem] font-bold font-['PT_Sans'] text-[#a7a7a7] leading-none">
        −
      </div>
    </button>
  );
};

export default MinusFromCartButton;
