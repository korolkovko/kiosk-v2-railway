// File: src/services/auth.service.ts
//
// Purpose:
// Authentication service orchestrating transport calls, mapping DTO→Domain→ViewModel,
// token management, and session persistence. No UI or transport-specific logic here.
//
// Responsibilities:
// - Coordinate API calls (login, refresh, logout)
// - Map API DTOs to Domain and to ViewModel
// - Manage access token via HTTP client helpers
// - Persist session to storage (expire-aware)
// - Expose clear, self-descriptive methods for consumers (contexts/hooks/pages)
//
// Notes:
// - All functions are named exports (no default).
// - Consumers at UI level should prefer methods returning ViewModels.
// - Validation can be added at boundaries (e.g., zod) if/when needed.

import type {
  LoginRequestDto,
  LoginResponseDto,
  RefreshResponseDto,
} from '../models/dto/auth.dto';
import type { AuthSession } from '../models/domain/auth';
import type { AuthSessionVM } from '../models/view/auth.vm';

import * as authApi from '../api/authApi';
import { setAccessToken, clearAccessToken, setRefreshToken, clearRefreshToken, getRefreshToken } from '../api/apiHttpClient';
import { saveSession, loadSession, clearSession } from '../utils/storage';
import {
  mapLoginResponseDtoToDomainSession,
  mapAuthSessionDomainToVM,
} from './mappers/auth.mappers';

/**
 * loginWithPassword()
 * - Calls transport API to authenticate
 * - Maps DTO → Domain
 * - Stores token in memory and session in storage
 * - Returns ViewModel for UI consumption
 */
export async function loginWithPassword(
  credentials: LoginRequestDto,
): Promise<AuthSessionVM> {
  // Transport call
  const dto: LoginResponseDto = await authApi.login(credentials);

  // DTO → Domain
  const session: AuthSession =
    mapLoginResponseDtoToDomainSession(dto);

  // Side-effects: set tokens and persist session
  setAccessToken(session.accessToken);
  setRefreshToken(dto.refresh_token); // Save refresh token to localStorage (survives browser restart)
  saveSession<AuthSession>(session, session.expiresIn);

  // Domain → ViewModel
  return mapAuthSessionDomainToVM(session);
}

/**
 * refreshAccessTokenAndGetSession()
 * - Exchanges refresh token for new access token via transport API
 * - Updates in-memory token and storage if session exists
 * - Returns updated Domain session or null when no existing session
 */
export async function refreshAccessTokenAndGetSession(): Promise<AuthSession | null> {
  const existing = loadSession<AuthSession>();
  const storedRefreshToken = getRefreshToken();

  if (!storedRefreshToken) {
    // No refresh token available
    return null;
  }

  const refreshed: RefreshResponseDto = await authApi.refresh(storedRefreshToken);

  // Update tokens in memory and storage
  setAccessToken(refreshed.access_token);
  if (refreshed.refresh_token) {
    setRefreshToken(refreshed.refresh_token);
  }

  if (!existing) {
    // No persisted session; just return null (UI may redirect to login)
    return null;
  }

  const updated: AuthSession = {
    ...existing,
    accessToken: refreshed.access_token,
    // Keep same expiresIn semantics if backend doesn't return it on refresh
    // Storage save below will reuse the remaining time logic; if needed, compute remaining TTL here.
    expiresIn: existing.expiresIn,
  };

  // Persist updated session (reuse previous TTL semantics)
  saveSession<AuthSession>(updated, updated.expiresIn);

  return updated;
}

/**
 * refreshAccessTokenAndGetSessionVM()
 * - Same as refreshAccessTokenAndGetSession() but returns VM for UI
 */
export async function refreshAccessTokenAndGetSessionVM(): Promise<AuthSessionVM | null> {
  const session = await refreshAccessTokenAndGetSession();
  return session ? mapAuthSessionDomainToVM(session) : null;
}

/**
 * logoutAndClearSession()
 * - Calls transport API logout
 * - Clears token and storage regardless of transport result
 */
export async function logoutAndClearSession(): Promise<void> {
  try {
    await authApi.logout();
  } finally {
    clearAccessToken();
    clearRefreshToken();
    clearSession();
  }
}

/**
 * getPersistedSession()
 * - Load persisted Domain session (if not expired) from storage
 */
export function getPersistedSession(): AuthSession | null {
  return loadSession<AuthSession>();
}

/**
 * getPersistedSessionVM()
 * - Load persisted session and map to ViewModel (for UI)
 */
export function getPersistedSessionVM(): AuthSessionVM | null {
  const session = getPersistedSession();
  return session ? mapAuthSessionDomainToVM(session) : null;
}
