// File: src/hooks/useScreenSaver.ts
//
// Purpose:
// Hook for managing screensaver visibility state.
// Simple show/hide mechanism for DOS-style screensaver overlay.
// Used after login and after inactivity timeout.

import { useState, useCallback } from 'react';

export interface UseScreenSaverResult {
  isScreenSaverVisible: boolean;
  showScreenSaver: () => void;
  hideScreenSaver: () => void;
}

/**
 * useScreenSaver
 *
 * Manages screensaver visibility state.
 * Provides show/hide functions for triggering screensaver overlay.
 *
 * @param showOnMount - If true, screensaver is visible on mount (default: false)
 * @returns Object with visibility state and control functions
 *
 * @example
 * const { isScreenSaverVisible, showScreenSaver, hideScreenSaver } = useScreenSaver(true)
 *
 * // After inactivity timeout
 * onTimeout: () => {
 *   clearCart()
 *   showScreenSaver()
 * }
 *
 * // User presses button
 * <ScreenSaver isVisible={isScreenSaverVisible} onDismiss={hideScreenSaver} />
 */
export function useScreenSaver(showOnMount: boolean = false): UseScreenSaverResult {
  const [isScreenSaverVisible, setIsScreenSaverVisible] = useState(showOnMount);

  /**
   * Show screensaver overlay
   */
  const showScreenSaver = useCallback(() => {
    console.log('🖥️ Showing screensaver');
    setIsScreenSaverVisible(true);
  }, []);

  /**
   * Hide screensaver overlay
   */
  const hideScreenSaver = useCallback(() => {
    console.log('🖥️ Hiding screensaver');
    setIsScreenSaverVisible(false);
  }, []);

  return {
    isScreenSaverVisible,
    showScreenSaver,
    hideScreenSaver
  };
}
