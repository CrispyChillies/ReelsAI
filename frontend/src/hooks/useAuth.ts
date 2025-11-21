import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { authService } from '@/services/authService';
import { getRefreshToken } from '@/lib/axios';
import type { SignInRequest, RegisterRequest, User } from '@/types/auth';
import { useToast } from '@/app/toast';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { notify } = useToast();

  // Check if user is authenticated
  const isAuthenticated = !!getRefreshToken();

  // Get current user query - this will also refresh access token if needed
  const {
    data: user,
    isLoading: isLoadingUser,
    error: userError,
  } = useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
    enabled: isAuthenticated,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  });

  // On mount, if we have refresh token but no access token in memory,
  // the getCurrentUser query will automatically refresh it via axios interceptor
  useEffect(() => {
    if (isAuthenticated && !user && userError) {
      // If we have refresh token but can't get user, tokens might be invalid
      console.error('Authentication error:', userError);
    }
  }, [isAuthenticated, user, userError]);

  // Sign in mutation
  const signInMutation = useMutation({
    mutationFn: (data: SignInRequest) => authService.signIn(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      notify({ title: 'Login successful!', tone: 'success' });
      // Delay navigation to show toast (1 second)
      setTimeout(() => navigate('/app'), 1000);
    },
    onError: (error: any) => {
      console.log('Login error - NO NAVIGATION SHOULD HAPPEN:', error);
      const message = error.response?.data?.error || 'Login failed!';
      notify({ title: 'Login failed', content: message, tone: 'error' });
      // DO NOT NAVIGATE ON ERROR - just show toast
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: (data) => {
      notify({ title: data.message || 'Registration successful!', content: 'Please check your email.', tone: 'success' });
      // Delay navigation to show toast (1 second)
      setTimeout(() => navigate('/auth/check-email'), 1000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || 'Registration failed!';
      notify({ title: 'Registration failed', content: message, tone: 'error' });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: authService.logout,
    onSuccess: () => {
      // Clear all queries and cache
      queryClient.clear();
      notify({ title: 'Logout successful!', tone: 'success' });
      // Delay navigation to show toast (800ms for logout)
      setTimeout(() => navigate('/auth/sign-in', { replace: true }), 800);
    },
    onError: () => {
      // Even if logout fails on server, clear client tokens and cache
      queryClient.clear();
      notify({ title: 'Logged out locally', tone: 'info' });
      // Delay navigation to show toast (800ms for logout)
      setTimeout(() => navigate('/auth/sign-in', { replace: true }), 800);
    },
  });

  // Request password reset mutation
  const requestPasswordResetMutation = useMutation({
    mutationFn: (email: string) =>
      authService.requestPasswordReset({ email }),
    onSuccess: (data) => {
      notify({ title: data.message, tone: 'success' });
      // Navigate to check-email page after successful request
      setTimeout(() => navigate('/auth/check-email'), 1000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || 'Failed to send reset email!';
      notify({ title: 'Reset email failed', content: message, tone: 'error' });
    },
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: ({ uidb64, token, password }: { uidb64: string; token: string; password: string }) =>
      authService.resetPassword(uidb64, token, { password }),
    onSuccess: (data) => {
      notify({ title: data.message, tone: 'success' });
      // Delay navigation to show toast (1 second)
      setTimeout(() => navigate('/auth/sign-in'), 1000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || 'Password reset failed!';
      notify({ title: 'Password reset failed', content: message, tone: 'error' });
    },
  });

  return {
    user,
    isAuthenticated,
    isLoadingUser,
    userError,
    signIn: signInMutation.mutate,
    isSigningIn: signInMutation.isPending,
    register: registerMutation.mutate,
    isRegistering: registerMutation.isPending,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
    requestPasswordReset: requestPasswordResetMutation.mutate,
    isRequestingPasswordReset: requestPasswordResetMutation.isPending,
    resetPassword: resetPasswordMutation.mutate,
    isResettingPassword: resetPasswordMutation.isPending,
  };
};
