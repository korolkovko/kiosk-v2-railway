// File: src/services/mappers/auth.mappers.ts
//
// Purpose:
// Pure mapping functions for the Authentication feature.
// - DTO → Domain: clean/normalize API transport data
// - Domain → ViewModel: shape/format data for UI
// - ViewModel → Domain/DTO: (optional) when sending data back
//
// Notes:
// - No side-effects. No I/O. Deterministic and testable.
// - Business rules/orchestration live in services (e.g. src/services/auth.service.ts).
// - Validation schemas (zod/valibot) can be applied at API boundary; mappers assume valid input.

import type { UserDto, LoginResponseDto, LoginRequestDto, RefreshResponseDto } from '../../models/dto/auth.dto';
import type { User, AuthSession } from '../../models/domain/auth';
import type { UserVM, AuthSessionVM } from '../../models/view/auth.vm';

/**
 * mapUserDtoToDomain()
 * Convert API UserDto -> domain User
 */
export function mapUserDtoToDomain(dto: UserDto): User {
  return {
    userId: dto.user_id,
    username: dto.username,
    email: dto.email,
    roleName: dto.role_name,
    isActive: dto.is_active,
  };
}

/**
 * mapLoginResponseDtoToDomainSession()
 * Convert API LoginResponseDto -> domain AuthSession
 */
export function mapLoginResponseDtoToDomainSession(dto: LoginResponseDto): AuthSession {
  return {
    user: mapUserDtoToDomain(dto.user),
    accessToken: dto.access_token,
    expiresIn: dto.expires_in,
  };
}

/**
 * mapUserDomainToVM()
 * Convert domain User -> UI-friendly UserVM
 */
export function mapUserDomainToVM(user: User): UserVM {
  return {
    id: user.userId,
    username: user.username,
    displayName: user.username, // no distinct display name provided by backend; reuse username
    roleName: user.roleName,
    email: user.email,
    isActive: user.isActive,
  };
}

/**
 * mapAuthSessionDomainToVM()
 * Convert domain AuthSession -> UI-friendly AuthSessionVM
 */
export function mapAuthSessionDomainToVM(session: AuthSession): AuthSessionVM {
  return {
    user: mapUserDomainToVM(session.user),
    accessToken: session.accessToken,
  };
}

/**
 * mapLoginRequestVMToDto()
 * If UI ever provides a VM for login (now it doesn't), this would convert it to DTO.
 * Here we keep a simple pass-through for current shape.
 */
export function mapLoginRequestToDto(input: { username: string; password: string }): LoginRequestDto {
  return {
    username: input.username,
    password: input.password,
  };
}

/**
 * passthroughRefreshResponseDto()
 * Keep for parity and clarity; useful if we add schema validation or transform later.
 */
export function passthroughRefreshResponseDto(dto: RefreshResponseDto): RefreshResponseDto {
  return dto;
}
