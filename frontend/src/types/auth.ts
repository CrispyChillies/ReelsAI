// User type from /api/auth/me/ (needs to be created on backend)
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
}

// Register request
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Register response
export interface RegisterResponse {
  message: string;
}

// Sign in request
export interface SignInRequest {
  username: string;
  password: string;
}

// Sign in response
export interface SignInResponse {
  access: string;
  refresh: string;
  message: string;
}

// Request password reset request
export interface RequestPasswordResetRequest {
  email: string;
}

// Request password reset response
export interface RequestPasswordResetResponse {
  message: string;
}

// Reset password request
export interface ResetPasswordRequest {
  password: string;
}

// Reset password response
export interface ResetPasswordResponse {
  message: string;
}

// Logout request
export interface LogoutRequest {
  refresh_token: string;
}

// Logout response
export interface LogoutResponse {
  message: string;
}

// Error response
export interface ErrorResponse {
  error: string;
  detail?: string;
}
