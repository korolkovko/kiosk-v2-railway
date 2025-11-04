// File: src/models/view/availableItem.vm.ts
//
// Purpose:
// ViewModel for available menu items optimized for UI display.
// Contains formatted strings, UI-friendly names, and display properties.

/**
 * AvailableItemVM
 * View model for rendering menu items in kiosk UI.
 * Prices formatted as display strings, convenient display properties.
 */
export interface AvailableItemVM {
  itemId: number;
  nameRu: string;
  nameEng: string | null;
  descriptionRu: string;
  descriptionEng: string | null;
  unitMeasure: string;
  foodCategory: string;

  // Formatted price strings for display
  priceGrossDisplay: string; // e.g., "150.00 ₽"
  priceNetDisplay: string;
  vatRateDisplay: string | null; // e.g., "20%"

  // Raw numeric values (for calculations if needed in UI)
  priceGross: number;
  priceNet: number;
  vatRate: number | null;

  promoted: boolean;
  stockQuantity: number;
  isAvailable: boolean; // Computed: stockQuantity > 0 && isActive

  // Menu display fields
  displayOrder: number;
  startAt: string | null; // Time in HH:MM:SS format or null (all day) - for client-side filtering
  endAt: string | null;   // Time in HH:MM:SS format or null (all day) - for client-side filtering

  // Poster media path (computed client-side from itemId)
  // Format: "/items/media/{itemId}" - auto-detection finds .png, .mp4, .webm, etc.
  posterPath: string;
}
