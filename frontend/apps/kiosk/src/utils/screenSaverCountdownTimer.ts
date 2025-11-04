// File: src/utils/screenSaverCountdownTimer.ts
//
// Purpose:
// Countdown timer calculation for ScreenSaver component.
// Calculates time remaining until "3I/ATLAS ENCOUNTER" on Dec 19, 2025.
// Format: DD.HH.MM.SS.MS (days, hours, minutes, seconds, centiseconds)

/**
 * Target date for Atlas Encounter: December 19, 2025 00:00:00 UTC
 */
export const ATLAS_ENCOUNTER_DATE = new Date('2025-12-19T00:00:00Z');

/**
 * Countdown result with formatted string and individual components
 */
export interface AtlasCountdown {
  formatted: string // "245.13.42.07.45"
  days: number
  hours: number
  minutes: number
  seconds: number
  centiseconds: number
  isExpired: boolean
}

/**
 * Calculate countdown to Atlas Encounter (Dec 19, 2025)
 *
 * @returns Countdown in format DD.HH.MM.SS.MS
 *
 * @example
 * const countdown = getAtlasEncounterCountdown()
 * console.log(countdown.formatted) // "245.13.42.07.45"
 * console.log(countdown.days)      // 245
 * console.log(countdown.isExpired) // false
 */
export function getAtlasEncounterCountdown(): AtlasCountdown {
  const now = new Date();
  const diff = ATLAS_ENCOUNTER_DATE.getTime() - now.getTime();

  // Check if target date has passed
  if (diff <= 0) {
    return {
      formatted: '00.00.00.00.00',
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      centiseconds: 0,
      isExpired: true
    };
  }

  // Calculate time components
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);
  const centiseconds = Math.floor((diff % 1000) / 10); // 2 digits (00-99)

  // Format: DD.HH.MM.SS.MS
  const formatted = `${pad(days, 2)}.${pad(hours, 2)}.${pad(minutes, 2)}.${pad(seconds, 2)}.${pad(centiseconds, 2)}`;

  return {
    formatted,
    days,
    hours,
    minutes,
    seconds,
    centiseconds,
    isExpired: false
  };
}

/**
 * Pad number with leading zeros
 *
 * @param num - Number to pad
 * @param size - Desired string length
 * @returns Padded string
 *
 * @example
 * pad(7, 2)   // "07"
 * pad(245, 2) // "245"
 * pad(3, 3)   // "003"
 */
function pad(num: number, size: number): string {
  return String(num).padStart(size, '0');
}

/**
 * Get days remaining until Atlas Encounter
 */
export function getDaysUntilAtlasEncounter(): number {
  return getAtlasEncounterCountdown().days;
}

/**
 * Check if Atlas Encounter date has passed
 */
export function isAtlasEncounterExpired(): boolean {
  return getAtlasEncounterCountdown().isExpired;
}
