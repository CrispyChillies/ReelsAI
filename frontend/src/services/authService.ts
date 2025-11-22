import axiosInstance, {
  setAccessToken,
  setRefreshToken,
  getRefreshToken,
  clearTokens,
} from '@/lib/axios';
import type {
  User,
  SignInRequest,
  SignInResponse,
  RegisterRequest,
  RegisterResponse,
  RequestPasswordResetRequest,
  RequestPasswordResetResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  LogoutResponse,
} from '@/types/auth';

export const authService = {
  // Sign in
  async signIn(data: SignInRequest): Promise<SignInResponse> {
    const response = await axiosInstance.post<SignInResponse>('/auth/signin/', data);
    
    // Store tokens
    setAccessToken(response.data.access);
    setRefreshToken(response.data.refresh);
    
    return response.data;
  },

  // Register
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await axiosInstance.post<RegisterResponse>('/auth/register/', data);
    return response.data;
  },

  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await axiosInstance.get<User>('/auth/me/');
    return response.data;
  },

  // Logout
  async logout(): Promise<LogoutResponse> {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        const response = await axiosInstance.post<LogoutResponse>('/auth/logout/', {
          refresh_token: refreshToken,
        });
        clearTokens();
        return response.data;
      } catch (error) {
        console.error('Logout error:', error);
        clearTokens();
        throw error;
      }
    }
    clearTokens();
    return { message: 'Logged out successfully' };
  },

  // Request password reset
  async requestPasswordReset(data: RequestPasswordResetRequest): Promise<RequestPasswordResetResponse> {
    const response = await axiosInstance.post<RequestPasswordResetResponse>(
      '/auth/request-reset-password/',
      data
    );
    return response.data;
  },

  // Reset password
  async resetPassword(uidb64: string, token: string, data: ResetPasswordRequest): Promise<ResetPasswordResponse> {
    const response = await axiosInstance.post<ResetPasswordResponse>(
      `/auth/reset-password/${uidb64}/${token}/`,
      data
    );
    return response.data;
  },
};
