// File: src/components/NineButton.tsx
//
// Purpose:
// Button component for placing orders. Styled consistently with Plus/Minus/Eight buttons.
// Displays "9" and is only enabled when cart has items.

import { FunctionComponent } from "react";

export type NineButtonType = {
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  isLoading?: boolean;
};

const NineButton: FunctionComponent<NineButtonType> = ({
  className = "",
  onClick,
  disabled = false,
  isLoading = false
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`cursor-pointer bg-[transparent] border-none flex items-center justify-center hover:opacity-70 disabled:opacity-30 disabled:cursor-not-allowed ${className}`}
      title="Place Order (Press 9)"
    >
      <div className="text-[5rem] font-bold font-['PT_Sans'] text-[#a7a7a7] leading-none">
        {isLoading ? '...' : '9'}
      </div>
    </button>
  );
};

export default NineButton;
