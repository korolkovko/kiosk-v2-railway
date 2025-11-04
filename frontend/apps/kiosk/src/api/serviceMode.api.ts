// serviceMode.api.ts
//
// Purpose:
// Transport-only client for Kiosk Service Mode endpoints.
// - GET current kiosk service mode status for authenticated kiosk user
// Strictly HTTP + DTO parsing; business logic handled elsewhere.

import { fetchWithAuth, handleApiResponse, ApiError } from './apiHttpClient'
import { KIOSK_SERVICE_MODE_STATUS_SELF } from '../config/constants'

/**
 * KioskServiceModeStatusSelf
 * DTO returned by backend [Python.get_kiosk_status_for_kiosk_user()](backend/app/api/KioskServiceModeEndpoint.py:64)
 */
export interface KioskServiceModeStatusSelf {
  kiosk_username: string
  is_service_mode: boolean
  service_picture_name: string | null
  message: string
}

/**
 * getKioskServiceModeStatusForSelf()
 * Transport call to GET [/kiosk/service-mode/kiosk-status-for-kiosk-user](frontend/apps/kiosk/src/config/constants.ts:21)
 * Returns raw DTO from backend without transformations.
 */
export async function getKioskServiceModeStatusForSelf(): Promise<KioskServiceModeStatusSelf> {
  try {
    const response = await fetchWithAuth(KIOSK_SERVICE_MODE_STATUS_SELF, {
      method: 'GET'
    })
    return await handleApiResponse<KioskServiceModeStatusSelf>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError('Failed to fetch service mode status', 'unknown')
  }
}