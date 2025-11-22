import React, { useState } from "react";
import styled from "styled-components";
import { useForm } from "react-hook-form";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";
import type { SignInRequest } from "@/types/auth";

type Props = {
  onSubmit: (data: SignInRequest) => void;
  loading?: boolean;
};

const LoginForm: React.FC<Props> = ({ onSubmit, loading }) => {
  const { t } = useI18n();
  const [password, setPassword] = useState("");
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<SignInRequest>({
    defaultValues: {
      username: "",
      password: "",
    },
  });

  return (
    <StyledWrapper>
      <section className="container">
        <header>{t("signin")}</header>

        <form className="form" onSubmit={handleSubmit(onSubmit)}>
          <div className="input-box">
            <label>Username</label>
            <input
              type="text"
              placeholder="Your username"
              {...register("username", {
                required: "Username is required",
              })}
            />
            {errors.username && (
              <span className="error">{errors.username.message}</span>
            )}
          </div>

          <div className="input-box">
            <PwField
              label="Password"
              value={password}
              onChange={(v) => {
                setPassword(v);
                setValue("password", v, { shouldValidate: true });
              }}
              placeholder="Your password"
              autoComplete="current-password"
              disabled={loading}
            />
            {errors.password && (
              <span className="error">{errors.password.message}</span>
            )}
          </div>

          <Button type="submit" wfull size="md" loading={loading} disabled={loading}>
            {t("login")}
          </Button>
        </form>
      </section>
    </StyledWrapper>
  );
};

export default LoginForm;

/* ===================== styles ===================== */
const StyledWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;

  .container {
    max-width: 420px;
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
  .form {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .input-box {
    width: 100%;
    margin-top: 10px;
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
`;
