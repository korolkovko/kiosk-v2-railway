// File: src/services/getAvailableItems.service.ts
//
// Purpose:
// Business orchestration for "Get Available Items" in kiosk menu.
// - Calls transport API
// - Maps DTO → Domain → ViewModel via pure mappers
// - Exposes clear, self-descriptive functions for consumers (hooks/pages)
// No UI/transport details here; no React state in this layer.

import { getAvailableItems } from '../api/getAvailableItems.api'
import type { GetAvailableItemsResponseDto } from '../models/dto/getAvailableItems.dto'
import type { AvailableItem } from '../models/domain/availableItem'
import type { AvailableItemVM } from '../models/view/availableItem.vm'
import {
  mapGetAvailableItemsDtoToDomain,
  mapGetAvailableItemsDomainToVM,
} from './mappers/getAvailableItems.mappers'

/**
 * getAvailableItemsVM()
 * Fetch available menu items and return UI-friendly ViewModels.
 * Fail-fast mapping: assumes API-level validation already performed.
 */
export async function getAvailableItemsVM(): Promise<AvailableItemVM[]> {
  // Fetch transport-layer data
  const dtos: GetAvailableItemsResponseDto = await getAvailableItems()

  // Map DTO → Domain
  const domainItems: AvailableItem[] = mapGetAvailableItemsDtoToDomain(dtos)

  // Map Domain → ViewModel
  return mapGetAvailableItemsDomainToVM(domainItems)
}

/**
 * getAvailableItemsDomain()
 * Fetch available items and return domain models if consumers need domain shape.
 */
export async function getAvailableItemsDomain(): Promise<AvailableItem[]> {
  const dtos: GetAvailableItemsResponseDto = await getAvailableItems()
  return mapGetAvailableItemsDtoToDomain(dtos)
}
