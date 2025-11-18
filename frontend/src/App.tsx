import { Routes, Route, Navigate } from "react-router-dom";
// Auth pages - UI accessible for editing (backend calls commented inside)
import SignIn from "@/pages/auth/SignIn";
import SignUp from "@/pages/auth/SignUp";
import Forgot from "@/pages/auth/ForgotPassword";
import ResetPassword from "@/pages/auth/ResetPassword";
import CheckEmailPage from "./pages/auth/CheckEmailPage";
import OnboardingTopics from "@/pages/OnboardingTopics";

import AppLayout from "@/components/layout/AppLayout";
import NewsfeedPage from "@/pages/NewsfeedPage";
import ChatPage from "@/pages/ChatPage";
import Profile from "@/pages/Profile";
import SavedContent from "@/pages/SavedContent";

// COMMENTED OUT: Supabase redirect hook (not needed in demo)
// import useSupabaseRedirect from "@/hooks/useSupabaseRedirect";

export default function App() {
  // COMMENTED OUT: Supabase redirect handling (not needed in demo)
  // useSupabaseRedirect();

  return (
    <Routes>
      {/* ===== Auth routes - UI accessible, no backend required ===== */}
      <Route path="/signin" element={<SignIn />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="/forgot" element={<Forgot />} />
      <Route path="/reset" element={<ResetPassword />} />
      <Route path="/check-email" element={<CheckEmailPage />} />

      {/* ===== Onboarding ===== */}
      <Route path="/onboarding/topics" element={<OnboardingTopics />} />

      {/* ===== App routes with sidebar ===== */}
      <Route element={<AppLayout />}>
        <Route path="/" element={<NewsfeedPage />} />
        <Route path="/feed" element={<NewsfeedPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/saved" element={<SavedContent />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      {/* fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
