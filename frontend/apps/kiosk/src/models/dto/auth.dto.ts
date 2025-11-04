// File: src/models/dto/auth.dto.ts
//
// Purpose:
// Transport-layer DTOs for authentication endpoints.
// These interfaces reflect the exact JSON shape exchanged with the backend.
// Do NOT place domain or UI (ViewModel) concerns here.

/**
 * LoginRequestDto
 * Payload sent to POST /api/kiosk/auth/login
 */
export interface LoginRequestDto {
  username: string;
  password: string;
}

/**
 * UserDto
 * User object returned by backend within LoginResponseDto
 */
export interface UserDto {
  user_id: number;
  username: string;
  email: string;
  role_name: string;
  is_active: boolean;
}

/**
 * LoginResponseDto
 * Response returned by POST /api/kiosk/auth/login
 */
export interface LoginResponseDto {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserDto;
}

/**
 * RefreshResponseDto
 * Response returned by POST /api/kiosk/auth/refresh
 */
export interface RefreshResponseDto {
  access_token: string;
  refresh_token?: string;
}
