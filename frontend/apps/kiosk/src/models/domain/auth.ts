// File: src/models/domain/auth.ts
//
// Purpose:
// Domain-layer models for authentication feature.
// These interfaces represent business entities used across services/hooks/UI.
// They are independent of transport (API) and view formatting concerns.

export interface User {
  userId: number;
  username: string;
  email: string;
  roleName: string;
  isActive: boolean;
}

/**
 * AuthSession
 * Represents authenticated session data within the domain layer.
 * Services may persist this using storage utilities.
 */
export interface AuthSession {
  user: User;
  accessToken: string;
  expiresIn: number;
}
