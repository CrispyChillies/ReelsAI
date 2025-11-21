import React, { useState } from "react";
import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";

type Props = {
  onSubmit: (p: { email: string; password: string; username: string }) => void;
  loading?: boolean;
};

const SignupForm: React.FC<Props> = ({ onSubmit, loading }) => {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [name, setName] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pw !== pw2) {
      alert(`${t("error")}: ${t("confirmPassword")}`);
      return;
    }
    onSubmit({ email: email.trim(), password: pw, username: name.trim() });
  };

  return (
    <StyledWrapper>
      <section className="container">
        <header>{t("signup")}</header>

        <form className="form" onSubmit={submit}>
          <div className="input-box">
            <label>Username</label>
            <input
              required
              placeholder="Your username"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="input-box">
            <label>Email</label>
            <input
              required
              type="email"
              placeholder="Your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="column">
            <PwField
              label="Password"
              value={pw}
              onChange={setPw}
              autoComplete="new-password"
              required
            />
            <PwField
              label="Confirm Password"
              value={pw2}
              onChange={setPw2}
              autoComplete="new-password"
              required
            />
          </div>

          <Button type="submit" wfull size="md" disabled={!!loading}>
            {loading ? t("creating") : t("createAccount")}
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
