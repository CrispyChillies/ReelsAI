import React, { useEffect, useState } from "react";
import styled from "styled-components";
// COMMENTED OUT: Backend reset password API
// import { resetPasswordWithRecoveryToken } from "@/services/auth";
import { useToast } from "@/app/toast";
import { useI18n } from "@/app/i18n";
import LoaderPage from "@/components/common/loaders/LoaderPage";
import { useNavigate } from "react-router-dom";
import Button from "@/components/common/buttons/Button";
import PwField from "@/components/common/inputs/PwField";
// COMMENTED OUT: Error formatter
// import { formatError } from "@/utils/formatError";

// ảnh trong /public
const bg = "/forgot-reset-bg.jpg";

export default function ResetPassword() {
  const { notify } = useToast();
  const { t } = useI18n();
  const nav = useNavigate();

  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  // const [recoveryToken, setRecoveryToken] = useState<string>("");

  useEffect(() => {
    // DEMO: Skip token validation in demo mode
    // Just set ready to true to show the form
    setReady(true);
    
    // COMMENTED OUT: Real token validation
    // const url = new URL(window.location.href);
    // const hashParams = new URLSearchParams(
    //   (window.location.hash || "").replace(/^#/, "")
    // );
    // const qParams = url.searchParams;

    // const type = (
    //   hashParams.get("type") ||
    //   qParams.get("type") ||
    //   ""
    // ).toLowerCase();
    // const token =
    //   hashParams.get("access_token") || qParams.get("access_token") || "";

    // if (type === "recovery" && token) {
    //   setRecoveryToken(token);
    //   setReady(true);
    //   return;
    // }

    // notify({
    //   title: t("error"),
    //   content: t("missingOrInvalidResetToken") || "Missing or invalid reset token",
    //   tone: "error",
    // });
    // nav("/signin");
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pw.length < 8) {
      notify({
        title: t("error"),
        content: t("passwordTooShort"),
        tone: "error",
      });
      return;
    }
    if (pw !== pw2) {
      notify({
        title: t("error"),
        content: t("confirmPassword"),
        tone: "error",
      });
      return;
    }

    // DEMO: Simulate password reset without backend
    setLoading(true);
    setTimeout(() => {
      notify({ title: "Demo", content: "Password reset successfully (simulated)", tone: "success" });
      setLoading(false);
      nav("/signin");
    }, 1000);

    // COMMENTED OUT: Real backend password reset
    // try {
    //   setLoading(true);
    //   await resetPasswordWithRecoveryToken(recoveryToken, pw);
    //   window.history.replaceState({}, document.title, window.location.pathname);
    //   notify({ title: t("passwordUpdated"), tone: "success" });
    //   nav("/signin");
    // } catch (err: any) {
    //   notify({ title: t("error"), content: formatError(err), tone: "error" });
    // } finally {
    //   setLoading(false);
    // }
  };

  if (!ready)
    return (
      <Wrap $bg={bg}>
        <LoaderPage />
      </Wrap>
    );

  return (
    <Wrap $bg={bg}>
      <section className="container">
        <header>{t("setNewPassword")}</header>
        <form className="form" onSubmit={submit}>
          <PwField
            label={t("newPassword")}
            value={pw}
            onChange={setPw}
            autoComplete="new-password"
            required
          />
          <PwField
            label={t("confirmPassword")}
            value={pw2}
            onChange={setPw2}
            autoComplete="new-password"
            required
          />
          <Button type="submit" wfull size="md" disabled={loading}>
            {t("updatePassword")}
          </Button>
        </form>
      </section>
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
  .form {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  @media (max-width: 480px) {
    padding: 16px;
    background-position: 70% center;
  }
`;
