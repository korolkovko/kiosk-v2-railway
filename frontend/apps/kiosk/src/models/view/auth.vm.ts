// File: src/models/view/auth.vm.ts
//
// Purpose:
// View-layer models for the authentication feature.
// These types are tailored for the UI (components/pages) and should contain
// only the data and naming that the UI needs, after domain mapping.
// No transport (API) concerns and no business logic should be placed here.

/**
 * UserVM
 * View-model representation of the user entity for UI consumption.
 * Naming is optimized for direct use in components.
 */
export interface UserVM {
  id: number;
  username: string;
  displayName: string;
  roleName: string;
  email: string;
  isActive: boolean;
}

/**
 * AuthSessionVM
 * View-model representation of an authenticated session for UI consumption.
 */
export interface AuthSessionVM {
  user: UserVM;
  accessToken: string;
}
