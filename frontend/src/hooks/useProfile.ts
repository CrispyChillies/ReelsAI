import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/app/toast';
import * as profileService from '@/services/profileService';
import { authService } from '@/services/authService';
import { clearTokens } from '@/lib/axios';
import type { UpdateProfileRequest, ChangePasswordRequest } from '@/services/profileService';

export const useProfile = () => {
  const queryClient = useQueryClient();
  const { notify } = useToast();

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: UpdateProfileRequest) => profileService.updateProfile(data),
    onSuccess: (data) => {
      // Update the currentUser query cache
      queryClient.setQueryData(['currentUser'], data);
      notify({ title: 'Profile updated successfully', tone: 'success' });
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to update profile';
      notify({ title: 'Update failed', content: message, tone: 'error' });
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: ChangePasswordRequest) => profileService.changePassword(data),
    onSuccess: () => {
      notify({ title: 'Password changed successfully. Logging out...', tone: 'success' });
      
      // Logout after 1 second
      setTimeout(async () => {
        try {
          await authService.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Always clear cache and tokens
          queryClient.clear();
          clearTokens();
          // Use window.location for hard redirect to clear all state
          window.location.href = '/auth/sign-in';
        }
      }, 1000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || error.message || 'Failed to change password';
      notify({ title: 'Password change failed', content: message, tone: 'error' });
    },
  });

  return {
    updateProfile: updateProfileMutation.mutate,
    isUpdatingProfile: updateProfileMutation.isPending,
    changePassword: changePasswordMutation.mutate,
    isChangingPassword: changePasswordMutation.isPending,
  };
};
