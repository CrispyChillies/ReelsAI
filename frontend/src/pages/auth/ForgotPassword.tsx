import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import ForgotForm from "@/components/forms/ForgotPasswordForm";
import { useAuth } from "@/hooks/useAuth";

// ảnh trong /public
const bg = "/forgot-reset-bg.jpg";

export default function ForgotPage() {
  const { requestPasswordReset, isRequestingPasswordReset } = useAuth();
  const { t } = useI18n();

  const handleSubmit = (data: { email: string }) => {
    requestPasswordReset(data.email);
  };

  return (
    <Wrap $bg={bg}>
      <div className="panel">
        <ForgotForm onSubmit={handleSubmit} loading={isRequestingPasswordReset} />
        <div className="links">
          <span className="muted">{t("haveAccount")}</span>
          <a className="cta" href="/auth/sign-in">
            {t("signin")}
          </a>
          <span className="dot">•</span>
          <span className="muted">{t("needAccount")}</span>
          <a className="cta" href="/auth/sign-up">
            {t("signup")}
          </a>
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

  .links {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .muted {
    color: ${({ theme }) => theme.colors.primary};
    font-size: 0.96rem;
  }
  .dot {
    color: ${({ theme }) => theme.colors.primary};
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
