import { Routes, Route, Navigate } from "react-router-dom";
import SignIn from "@/pages/auth/SignIn";
import SignUp from "@/pages/auth/SignUp";
import Forgot from "@/pages/auth/ForgotPassword";
import ResetPassword from "@/pages/auth/ResetPassword";
import CheckEmailPage from "./pages/auth/CheckEmailPage";

import AppLayout from "@/components/layout/AppLayout";
import NewsfeedPage from "@/pages/NewsfeedPage";
import ChatPage from "@/pages/ChatPage";
import Profile from "@/pages/Profile";
import SavedContent from "@/pages/SavedContent";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* ===== Auth routes ===== */}
      <Route path="/auth/sign-in" element={<SignIn />} />
      <Route path="/auth/sign-up" element={<SignUp />} />
      <Route path="/auth/forgot-password" element={<Forgot />} />
      <Route
        path="/auth/reset-password/:uidb64/:token"
        element={<ResetPassword />}
      />
      <Route path="/auth/check-email" element={<CheckEmailPage />} />

      {/* Legacy auth routes - redirect to new routes */}
      <Route path="/signin" element={<Navigate to="/auth/sign-in" replace />} />
      <Route path="/signup" element={<Navigate to="/auth/sign-up" replace />} />
      <Route path="/forgot" element={<Navigate to="/auth/forgot-password" replace />} />
      <Route path="/reset" element={<Navigate to="/auth/sign-in" replace />} />
      <Route path="/check-email" element={<Navigate to="/auth/check-email" replace />} />

      {/* ===== Protected app routes with sidebar ===== */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/app" element={<NewsfeedPage />} />
          <Route path="/feed" element={<NewsfeedPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/saved" element={<SavedContent />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
      </Route>

      {/* fallback */}
      <Route path="*" element={<Navigate to="/auth/sign-in" replace />} />
    </Routes>
  );
}
