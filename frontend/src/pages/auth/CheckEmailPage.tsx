// src/pages/CheckEmailPage.tsx
import { useMemo } from "react";
import { useLocation, Link } from "react-router-dom";
import styled from "styled-components";
import { useI18n } from "@/app/i18n";
import Button from "@/components/common/buttons/Button";

const bg = "/notify-bg.jpg";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function CheckEmailPage() {
  const q = useQuery();
  const email = q.get("email") || "";
  const mode = (q.get("mode") || "verify") as "verify" | "reset";
  const { t } = useI18n();

  const webmailHref = useMemo(() => {
    const domain = email.split("@")[1]?.toLowerCase() || "";
    if (domain.includes("gmail")) return "https://mail.google.com/";
    if (domain.match(/outlook|hotmail|live/)) return "https://outlook.live.com/mail/";
    if (domain.includes("yahoo")) return "https://mail.yahoo.com/";
    return "https://" + (domain || "mail.google.com");
  }, [email]);

  return (
    <Wrap $bg={bg}>
      <div className="panel">
        <h1 className="title">
          {mode === "reset" ? t("resetSent") : t("signupVerify")}
        </h1>
        <p className="desc">
          {(mode === "reset" ? t("resetSentDesc") : t("verifySentDesc"))}{" "}
          <strong>{email}</strong>.
        </p>

        <a href={webmailHref} target="_blank" rel="noreferrer" className="btn-link">
          <Button wfull size="md">{t("openMailbox")}</Button>
        </a>

        <div className="assist">
          <span>{t("noEmail")}</span>
          <ul>
            <li>{t("checkSpam")}</li>
            <li>{t("waitMinute")}</li>
          </ul>
        </div>
      </div>

      <div className="auth-foot">
        <span className="muted">{t("backToSignin")}</span>
        <Link to="/signin" className="cta">{t("signin")}</Link>
      </div>
    </Wrap>
  );
}

const Wrap = styled.div<{ $bg: string }>`
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px; padding: 24px;
  background: ${({ theme }) => theme.colors.bg} url(${(p) => p.$bg}) center/cover no-repeat;

  .panel {
    width: min(100%, 500px);
    background: ${({ theme }) => theme.colors.surface};
    border: 1px solid ${({ theme }) => theme.colors.border};
    border-radius: ${({ theme }) => theme.radii.md};
    padding: 24px; box-shadow: ${({ theme }) => theme.shadow};
    text-align: center;
  }

  .title { font-size: 1.2rem; font-weight: 700; margin: 0; color: ${({ theme }) => theme.colors.accent}; }
  .desc { margin: 12px 0 18px; opacity: 0.9; }

  .btn-link { display: block; width: 100%; margin-bottom: 14px; }

  .assist { font-size: .95rem; opacity: .9; text-align: left; }
  .assist ul { margin: 6px 0 0; padding-left: 18px; }

  .auth-foot { display: flex; gap: 10px; }
  .muted {
    color: ${({ theme }) => theme.colors.primary};
    font-size: 0.96rem;
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
    outline: 3px solid ${({ theme }) => theme.colors.accent}59; /* accent + alpha */
    outline-offset: 2px;
  }

  @media (max-width: 480px) {
    padding: 16px;
    background-position: 70% center;
  }
`;
