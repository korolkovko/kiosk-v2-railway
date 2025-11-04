// File: src/components/InactivityOverlay.tsx
//
// Purpose:
// Full-screen overlay shown when kiosk detects user inactivity.
// Displays countdown and allows user to cancel by pressing any button.
// Yellow background with red text in multiple languages.

import { FunctionComponent, useEffect, useRef } from "react";

export type InactivityOverlayProps = {
  isVisible: boolean;
  countdown: number;
  onCancel: () => void;
  onReset?: () => void; // Optional: Called when user presses Enter to reset to screensaver
};

const InactivityOverlay: FunctionComponent<InactivityOverlayProps> = ({
  isVisible,
  countdown,
  onCancel,
  onReset
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Auto-focus overlay when it appears
  useEffect(() => {
    if (isVisible && overlayRef.current) {
      overlayRef.current.focus();
    }
  }, [isVisible]);

  // Listen for key press - distinguish Enter from other keys
  useEffect(() => {
    if (!isVisible) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      e.preventDefault();

      // Enter key → Reset to screensaver (if handler provided)
      if (e.key === 'Enter' && onReset) {
        onReset();
      } else {
        // Any other key → Cancel countdown
        onCancel();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [isVisible, onCancel, onReset]);

  if (!isVisible) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[9999] bg-[#FFD700] flex items-center justify-center cursor-pointer"
      onClick={onCancel}
      onTouchStart={onCancel}
      tabIndex={0}
    >
      {/* Centered content */}
      <div className="flex items-center justify-center pointer-events-none">
        <div className="flex flex-col items-center gap-[6rem]">
          {/* Multilingual inactivity text */}
          <div className="flex flex-col items-center gap-[1rem]">
            <h1 className="m-0 text-[5rem] font-bold font-['PT_Sans'] text-[#ff0000] uppercase tracking-wider">
              НЕАКТИВНОСТЬ
            </h1>
            <h1 className="m-0 text-[5rem] font-bold font-['PT_Sans'] text-[#ff0000] uppercase tracking-wider">
              INACTIVITY
            </h1>
            <h1 className="m-0 text-[5rem] font-bold font-['PT_Sans'] text-[#ff0000] uppercase tracking-wider">
              INÄKTIVITÄT
            </h1>
          </div>

          {/* Countdown number */}
          <div className="text-[16rem] font-bold font-['PT_Sans'] text-[#ff0000] leading-none">
            {countdown}
          </div>

          {/* Continue instructions */}
          <div className="flex flex-col items-center gap-[1rem]">
            <h2 className="m-0 text-[4rem] font-bold font-['PT_Sans'] text-[#ff0000] uppercase tracking-wider">
              PRESS ANY BUTTON TO CONTINUE
            </h2>
            <h2 className="m-0 text-[4rem] font-bold font-['PT_Sans'] text-[#ff0000] uppercase tracking-wider">
              OR PRESS ENTER TO START FROM THE VERY BEGINNING
            </h2>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InactivityOverlay;
