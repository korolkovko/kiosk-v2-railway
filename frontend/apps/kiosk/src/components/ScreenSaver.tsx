// File: src/components/ScreenSaver.tsx
//
// Purpose:
// DOS-style screensaver overlay for kiosk system.
// Shows Zero Culture ASCII logo and countdown to "3I/ATLAS ENCOUNTER" (Dec 19, 2025).
// Triggered after login or after inactivity timeout expires.
// Press any button to dismiss and continue.

import { FunctionComponent, useEffect, useRef, useState } from "react";
import { getAtlasEncounterCountdown } from "../utils/screenSaverCountdownTimer";
import MediaDisplay from "./MediaDisplay";

export type ScreenSaverProps = {
  isVisible: boolean;
  onDismiss: () => void;
};

/**
 * Zero Culture ASCII logo (DOS-style)
 * Uses box-drawing characters for retro aesthetic
 */
const ZERO_CULTURE_ASCII_LOGO = `
 ███████╗███████╗██████╗  ██████╗
 ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗
   ███╔╝ █████╗  ██████╔╝██║   ██║
  ███╔╝  ██╔══╝  ██╔══██╗██║   ██║
 ███████╗███████╗██║  ██║╚██████╔╝
 ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝

   ██████╗ ██╗   ██╗██╗     ████████╗██╗   ██╗██████╗ ███████╗
   ██╔════╝██║   ██║██║     ╚══██╔══╝██║   ██║██╔══██╗██╔════╝
 ██║     ██║   ██║██║        ██║   ██║   ██║██████╔╝█████╗
 ██║     ██║   ██║██║        ██║   ██║   ██║██╔══██╗██╔══╝
   ╚██████╗╚██████╔╝███████╗   ██║   ╚██████╔╝██║  ██║███████╗
    ╚═════╝ ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝
`;

/**
 * ScreenSaver Component
 *
 * DOS-style black screen with green phosphor text.
 * Shows countdown to Atlas Encounter and prompts user to continue.
 * Dismisses on any keyboard/mouse/touch interaction.
 */
const ScreenSaver: FunctionComponent<ScreenSaverProps> = ({
  isVisible,
  onDismiss
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const [countdown, setCountdown] = useState(getAtlasEncounterCountdown().formatted);

  // Update countdown every 10ms for smooth milliseconds animation
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      const newCountdown = getAtlasEncounterCountdown();
      setCountdown(newCountdown.formatted);
    }, 10); // Update 100 times per second for smooth centiseconds display

    return () => clearInterval(interval);
  }, [isVisible]);

  // Auto-focus overlay when it appears
  useEffect(() => {
    if (isVisible && overlayRef.current) {
      overlayRef.current.focus();
    }
  }, [isVisible]);

  // Listen for any key press globally
  useEffect(() => {
    if (!isVisible) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      e.preventDefault();
      onDismiss();
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [isVisible, onDismiss]);

  if (!isVisible) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[10000] bg-black flex flex-col items-center justify-between cursor-pointer select-none overflow-hidden py-[4rem]"
      onClick={onDismiss}
      onTouchStart={onDismiss}
      tabIndex={0}
    >
      {/* Background media layer (video or image) */}
      <MediaDisplay
        cacheKey="screensaver_screensaver"
        alt="Screensaver background"
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        loading="eager"
      />

      {/* Dark overlay for text readability */}
      <div className="absolute inset-0 bg-black/60 pointer-events-none" />

      {/* Optional: CRT scanlines effect */}
      <div className="absolute inset-0 pointer-events-none scanlines opacity-20" />

      {/* Top spacer */}
      <div className="flex-shrink-0 relative z-10"></div>

      {/* Main content container - centered */}
      <div className="flex flex-col items-center gap-[3rem] pointer-events-none relative z-10">

        {/* ASCII Logo - Centered for 1920px width */}
        <pre
          className="text-[1.5rem] leading-tight text-[#c0c0c0] font-mono whitespace-pre text-center"
          style={{
            width: '1920px',
            maxWidth: '100vw'
          }}
        >
          {ZERO_CULTURE_ASCII_LOGO}
        </pre>

        {/* Countdown section - grouped together */}
        <div className="flex flex-col items-start gap-[1rem]">
          {/* Atlas Encounter Countdown */}
          <div className="text-[2.5rem] font-mono text-[#c0c0c0] tracking-wider">
            3I/ATLAS ENCOUNTER: <span className="font-bold text-[3rem] text-[#ffff00]">{countdown}</span> TO TERRA
          </div>

          {/* Basic people message - left-aligned with left edge of countdown line above */}
          <div className="text-[1.75rem] font-mono text-[#c0c0c0] tracking-wide">
            Basic people can't tell what it is
          </div>
        </div>
      </div>

      {/* Blinking prompt - positioned at bottom */}
      <div className="text-[2.5rem] font-mono text-[#c0c0c0] uppercase tracking-wide animate-blink pointer-events-none flex-shrink-0 relative z-10">
        HURRY UP TO PLACE YOUR ORDER. PRESS ANY BUTTON TO CONTINUE
      </div>
    </div>
  );
};

export default ScreenSaver;
