import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoaderPage from '@/components/common/loaders/LoaderPage';

export const ProtectedRoute = () => {
  const { isAuthenticated, isLoadingUser, userError } = useAuth();

  // Show loader while checking authentication
  if (isAuthenticated && isLoadingUser) {
    return <LoaderPage />;
  }

  // If we have refresh token but got error fetching user, redirect to login
  if (isAuthenticated && userError) {
    return <Navigate to="/auth/sign-in" replace />;
  }

  // If no refresh token at all, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/auth/sign-in" replace />;
  }

  // User is authenticated and data is loaded
  return <Outlet />;
};
