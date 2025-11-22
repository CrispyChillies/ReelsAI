import { axiosInstance } from '@/lib/axios';
import type { User } from '@/types/auth';

export interface UpdateProfileRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface MessageResponse {
  message: string;
}

/**
 * Update user profile
 */
export const updateProfile = async (data: UpdateProfileRequest): Promise<User> => {
  const response = await axiosInstance.patch<User>('/auth/profile/', data);
  return response.data;
};

/**
 * Change password
 */
export const changePassword = async (data: ChangePasswordRequest): Promise<MessageResponse> => {
  const response = await axiosInstance.post<MessageResponse>('/auth/change-password/', data);
  return response.data;
};
