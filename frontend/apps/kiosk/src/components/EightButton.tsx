// File: src/components/EightButton.tsx
//
// Purpose:
// "8" button component for entering cart editing mode.
// Styled consistently with Plus/Minus buttons.
// Used for keyboard and touch interface.

import { FunctionComponent } from "react";

export type EightButtonType = {
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
};

const EightButton: FunctionComponent<EightButtonType> = ({
  className = "",
  onClick,
  disabled = false
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`cursor-pointer bg-[transparent] border-none flex items-center justify-center hover:opacity-70 disabled:opacity-30 disabled:cursor-not-allowed ${className}`}
    >
      <div className="text-[5rem] font-bold font-['PT_Sans'] text-[#a7a7a7] leading-none">
        8
      </div>
    </button>
  );
};

export default EightButton;
