import styled from "styled-components";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useParams, Link, Navigate } from "react-router-dom";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";
import { useAuth } from "@/hooks/useAuth";

// ảnh trong /public
const bg = "/forgot-reset-bg.jpg";

type ResetPasswordFormData = {
  password: string;
  password2: string;
};

export default function ResetPassword() {
  useI18n();
  const { uidb64, token } = useParams<{ uidb64: string; token: string }>();
  const { resetPassword, isResettingPassword } = useAuth();
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const {
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ResetPasswordFormData>();

  const onSubmit = (data: ResetPasswordFormData) => {
    if (!uidb64 || !token) {
      return;
    }
    if (password !== password2) {
      return;
    }
    resetPassword({
      uidb64,
      token,
      password: data.password,
    });
  };

  // Invalid token/uidb64
  if (!uidb64 || !token) {
    return <Navigate to="/auth/sign-in" replace />;
  }

  return (
    <Wrap $bg={bg}>
      <div className="panel">
        <div className="container">
          <header>Reset Password</header>
          <p className="description">Enter your new password below.</p>

          <form className="form" onSubmit={handleSubmit(onSubmit)}>
            <div className="input-box">
              <PwField
                label="New Password"
                value={password}
                onChange={(v) => {
                  setPassword(v);
                  setValue("password", v, { shouldValidate: true });
                }}
                placeholder="Enter new password"
                autoComplete="new-password"
                disabled={isResettingPassword}
              />
              {errors.password && (
                <span className="error">{errors.password.message}</span>
              )}
            </div>

            <div className="input-box">
              <PwField
                label="Confirm New Password"
                value={password2}
                onChange={(v) => {
                  setPassword2(v);
                  setValue("password2", v, { shouldValidate: true });
                }}
                placeholder="Confirm new password"
                autoComplete="new-password"
                disabled={isResettingPassword}
              />
              {password2 && password !== password2 && (
                <span className="error">Passwords do not match</span>
              )}
            </div>

            <Button
              type="submit"
              wfull
              size="md"
              loading={isResettingPassword}
              disabled={isResettingPassword}
            >
              Reset Password
            </Button>
          </form>

          <div className="links">
            <Link to="/auth/sign-in" className="cta">
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </Wrap>
  );
}

const Wrap = styled.div<{ $bg: string }>`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;

  /* Background full fill (chung với Forgot) */
  background-image: url(${(p) => p.$bg});
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-color: ${({ theme }) => theme.colors.bg};

  .panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    width: min(100%, 640px);
  }

  .container {
    max-width: 520px;
    width: 100%;
    background: ${({ theme }) => theme.colors.surface};
    border: 1px solid ${({ theme }) => theme.colors.border};
    border-radius: ${({ theme }) => theme.radii.md};
    padding: 24px;
    box-shadow: ${({ theme }) => theme.shadow};
  }

  header {
    text-align: center;
    font-weight: 700;
    font-size: 1.2rem;
    color: ${({ theme }) => theme.colors.accent};
  }

  .description {
    text-align: center;
    color: ${({ theme }) => theme.colors.secondary};
    margin-top: 12px;
    font-size: 0.95rem;
  }

  .form {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .input-box {
    width: 100%;
  }

  .input-box label {
    font-weight: 600;
    color: ${({ theme }) => theme.colors.primary};
  }

  .form :where(.input-box input) {
    height: 38px;
    width: 100%;
    outline: none;
    font-size: 1rem;
    color: ${({ theme }) => theme.colors.primary};
    margin-top: 6px;
    border: 1px solid ${({ theme }) => theme.colors.border};
    border-radius: 10px;
    padding: 0 12px;
    background: #fff;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .input-box input::placeholder {
    color: ${({ theme }) => theme.colors.secondary};
    opacity: 0.8;
  }

  .input-box input:focus {
    border-color: ${({ theme }) => theme.colors.accent};
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2);
  }

  .error {
    display: block;
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 4px;
  }

  .links {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }

  .cta {
    color: ${({ theme }) => theme.colors.accent};
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
    font-size: 0.96rem;
  }

  .cta:hover {
    color: ${({ theme }) => theme.colors.accent2};
  }

  .cta:focus-visible {
    outline: 3px solid rgba(206, 122, 88, 0.35);
    outline-offset: 2px;
  }

  @media (max-width: 480px) {
    padding: 16px;
    background-position: 70% center;
  }
`;
