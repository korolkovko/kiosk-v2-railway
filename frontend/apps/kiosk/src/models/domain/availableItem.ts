// File: src/models/domain/availableItem.ts
//
// Purpose:
// Domain model for available menu items in kiosk.
// Represents business entity with properly typed numeric values.
// Clean, framework-agnostic model for business logic.

/**
 * AvailableItem
 * Domain model for a menu item available for ordering in kiosk.
 * Prices are converted to numbers for calculations.
 */
export interface AvailableItem {
  itemId: number;
  nameRu: string;
  nameEng: string | null;
  descriptionRu: string;
  descriptionEng: string | null;
  unitMeasure: string;
  foodCategory: string;
  priceNet: number;
  vatRate: number | null;
  vatAmount: number;
  priceGross: number;
  isActive: boolean;
  promoted: boolean;
  stockQuantity: number;

  // Menu display fields
  displayOrder: number;
  startAt: string | null; // Time in HH:MM:SS format or null (all day)
  endAt: string | null;   // Time in HH:MM:SS format or null (all day)
}
