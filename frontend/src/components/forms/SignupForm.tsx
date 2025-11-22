import React, { useState } from "react";
import styled from "styled-components";
import { useForm } from "react-hook-form";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";
import type { RegisterRequest } from "@/types/auth";

type Props = {
  onSubmit: (data: RegisterRequest) => void;
  loading?: boolean;
};

type SignupFormData = RegisterRequest & {
  password2: string;
};

const SignupForm: React.FC<Props> = ({ onSubmit, loading }) => {
  const { t } = useI18n();
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<SignupFormData>();

  const handleFormSubmit = (data: SignupFormData) => {
    if (password !== password2) {
      return;
    }
    const { password2: _, ...registerData } = data;
    onSubmit(registerData);
  };

  return (
    <StyledWrapper>
      <section className="container">
        <header>{t("signup")}</header>

        <form className="form" onSubmit={handleSubmit(handleFormSubmit)}>
          <div className="input-box">
            <label>Username</label>
            <input
              type="text"
              placeholder="Your username"
              {...register("username", {
                required: "Username is required",
                minLength: {
                  value: 3,
                  message: "Username must be at least 3 characters",
                },
              })}
            />
            {errors.username && (
              <span className="error">{errors.username.message}</span>
            )}
          </div>

          <div className="input-box">
            <label>Email</label>
            <input
              type="email"
              placeholder="Your email"
              {...register("email", {
                required: "Email is required",
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: "Invalid email address",
                },
              })}
            />
            {errors.email && (
              <span className="error">{errors.email.message}</span>
            )}
          </div>

          <div className="column">
            <div className="input-box">
              <PwField
                label="Password"
                value={password}
                onChange={(v) => {
                  setPassword(v);
                  setValue("password", v, { shouldValidate: true });
                }}
                placeholder="Password"
                autoComplete="new-password"
                disabled={loading}
              />
              {errors.password && (
                <span className="error">{errors.password.message}</span>
              )}
            </div>

            <div className="input-box">
              <PwField
                label="Confirm Password"
                value={password2}
                onChange={(v) => {
                  setPassword2(v);
                  setValue("password2", v, { shouldValidate: true });
                }}
                placeholder="Confirm"
                autoComplete="new-password"
                disabled={loading}
              />
              {password2 && password !== password2 && (
                <span className="error">Passwords do not match</span>
              )}
            </div>
          </div>

          <Button type="submit" wfull size="md" loading={loading} disabled={loading}>
            {t("createAccount")}
          </Button>
        </form>
      </section>
    </StyledWrapper>
  );
};

export default SignupForm;

/* ===================== styles ===================== */
const StyledWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;

  .container {
    max-width: 560px;
    width: 100%;
    background: ${({ theme }) => theme.colors.surface};
    padding: 24px;
    border-radius: 12px;
    border: 1px solid ${({ theme }) => theme.colors.border};
    box-shadow: ${({ theme }) => theme.shadow};
  }
  .container header {
    font-size: 1.2rem;
    color: ${({ theme }) => theme.colors.accent};
    font-weight: 700;
    text-align: center;
    margin-bottom: 4px;
  }
  .container .form {
    margin-top: 14px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .form .input-box {
    width: 100%;
    margin-top: 10px;
  }
  .input-box label {
    color: ${({ theme }) => theme.colors.primary};
    font-weight: 600;
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

  .form .column {
    display: flex;
    column-gap: 12px;
  }
  @media (max-width: 520px) {
    .form .column {
      flex-direction: column;
      row-gap: 10px;
    }
  }
`;
