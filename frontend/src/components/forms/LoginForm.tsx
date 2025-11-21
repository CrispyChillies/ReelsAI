import React, { useState } from "react";
import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";

type Props = {
  onSubmit: (username: string, password: string) => void;
  loading?: boolean;
};

const LoginForm: React.FC<Props> = ({ onSubmit, loading }) => {
  const [username, setUsername] = useState("");
  const [pw, setPw] = useState("");
  const { t } = useI18n();

  return (
    <StyledWrapper>
      <section className="container">
        <header>{t("signin")}</header>

        <form
          className="form"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(username.trim(), pw);
          }}
        >
          <div className="input-box">
            <label>Username</label>
            <input
              required
              placeholder="Your username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <PwField
            label="Password"
            value={pw}
            onChange={setPw}
            autoComplete="current-password"
            required
          />

          <Button type="submit" wfull size="md" disabled={!!loading}>
            {loading ? t("loggingIn") : t("login")}
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
`;
