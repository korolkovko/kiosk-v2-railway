// File: src/services/mappers/getAvailableItems.mappers.ts
//
// Purpose:
// Pure mapper functions for transforming available items data through layers.
// DTO → Domain: Parse strings to numbers, normalize field names
// Domain → ViewModel: Format for display, add computed properties

import type { GetAvailableItemsResponseDto, GetAvailableItemDto } from '../../models/dto/getAvailableItems.dto'
import type { AvailableItem } from '../../models/domain/availableItem'
import type { AvailableItemVM } from '../../models/view/availableItem.vm'
import { getStorageProvider } from '../storage/storageFactory'
import { MediaType } from '../storage/types/mediaTypes.types'

/**
 * mapGetAvailableItemsDtoToDomain
 * Transform DTO array to Domain array
 * - Convert kopecks (integers) to rubles (decimals)
 * - Convert snake_case to camelCase
 */
export function mapGetAvailableItemsDtoToDomain(dtos: GetAvailableItemsResponseDto): AvailableItem[] {
  return dtos.map(mapGetAvailableItemDtoToDomain)
}

/**
 * mapGetAvailableItemDtoToDomain
 * Transform single DTO to Domain
 * Converts kopecks (integers) from backend to rubles (decimals) for domain layer
 */
function mapGetAvailableItemDtoToDomain(dto: GetAvailableItemDto): AvailableItem {
  // Backend now sends kopecks (integers), convert to rubles (decimals) for domain layer
  const priceNetRubles = dto.price_net_kopecks / 100;
  const vatAmountRubles = dto.vat_amount_kopecks / 100;
  const priceGrossRubles = dto.price_gross_kopecks / 100;

  return {
    itemId: dto.item_id,
    nameRu: dto.name_ru,
    nameEng: dto.name_eng,
    descriptionRu: dto.description_ru,
    descriptionEng: dto.description_eng,
    unitMeasure: dto.unit_measure_name_eng,
    foodCategory: dto.food_category_name,
    priceNet: priceNetRubles,
    vatRate: dto.vat_rate ? parseFloat(dto.vat_rate) : null,
    vatAmount: vatAmountRubles,
    priceGross: priceGrossRubles,
    isActive: dto.is_active,
    isAvailable: dto.is_active, // Compatibility alias (same as isActive for domain)
    promoted: dto.promoted,
    stockQuantity: dto.stock_quantity,

    // Menu display fields
    displayOrder: dto.display_order,
    startAt: dto.start_at,
    endAt: dto.end_at,
  }
}

/**
 * mapGetAvailableItemsDomainToVM
 * Transform Domain array to ViewModel array
 * - Format prices for display
 * - Add computed UI properties
 */
export function mapGetAvailableItemsDomainToVM(domainItems: AvailableItem[]): AvailableItemVM[] {
  return domainItems.map(mapGetAvailableItemDomainToVM)
}

/**
 * mapGetAvailableItemDomainToVM
 * Transform single Domain to ViewModel
 */
function mapGetAvailableItemDomainToVM(domain: AvailableItem): AvailableItemVM {
  const storageProvider = getStorageProvider()

  // Build poster path using storage provider (base path without extension)
  const posterPath = storageProvider.getBasePath(MediaType.ITEMS) + '/' + domain.itemId

  return {
    itemId: domain.itemId,
    nameRu: domain.nameRu,
    nameEng: domain.nameEng,
    descriptionRu: domain.descriptionRu,
    descriptionEng: domain.descriptionEng,
    unitMeasure: domain.unitMeasure,
    foodCategory: domain.foodCategory,

    // Formatted display strings
    priceGrossDisplay: `${domain.priceGross.toFixed(2)} ₽`,
    priceNetDisplay: `${domain.priceNet.toFixed(2)} ₽`,
    vatRateDisplay: domain.vatRate !== null ? `${domain.vatRate.toFixed(0)}%` : null,

    // Raw numeric values
    priceGross: domain.priceGross,
    priceNet: domain.priceNet,
    vatRate: domain.vatRate,

    promoted: domain.promoted,
    stockQuantity: domain.stockQuantity,
    isActive: domain.isActive, // Compatibility alias
    isAvailable: domain.stockQuantity > 0 && domain.isActive,

    // Menu display fields
    displayOrder: domain.displayOrder,
    startAt: domain.startAt,
    endAt: domain.endAt,

    // Poster path (auto-detection will find .png, .mp4, .webm, etc.)
    posterPath,
  }
}
