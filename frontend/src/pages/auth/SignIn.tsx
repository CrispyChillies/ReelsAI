import { useState } from "react";
import styled from "styled-components";
import LoginForm from "@/components/forms/LoginForm";
import { Link, useNavigate } from "react-router-dom";
import LoaderPage from "@/components/common/loaders/LoaderPage";
import { useToast } from "@/app/toast";
import { useI18n } from "@/app/i18n";
import ThreeDBackground from "@/components/common/ThreeDBackground";
// COMMENTED OUT: Backend login API
// import { login } from "@/services/auth";
// COMMENTED OUT: Error formatter
// import { formatError } from "@/utils/formatError";

export default function SignIn() {
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();
  const { t } = useI18n();

  const submit = async (email: string, password: string) => {
    setLoading(true);
    
    // DEMO: Simulate login without backend
    setTimeout(() => {
      notify({ title: "Demo Login", content: "Navigating to app (no real auth)", tone: "success" });
      setLoading(false);
      nav("/app");
    }, 1000);
  };

  return (
    <Wrap>
      {loading ? (
        <div className="loaderWrapper">
          <LoaderPage />
        </div>
      ) : (
        <>
          {/* Left Side - 3D Interactive Background */}
          <div className="leftSide">
            <ThreeDBackground />
            <div className="content">
              <h1 className="brand">ReelsAI</h1>
              <p className="tagline">Your AI-powered assistant for Reels</p>
            </div>
          </div>

          {/* Right Side - Form */}
          <div className="rightSide">
            <div className="formContainer">
              <LoginForm onSubmit={submit} loading={loading} />
              <div className="links">
                <div className="row">
                  <span className="muted">{t("needAccount")}</span>
                  <Link to="/signup" className="cta">
                    {t("signup")}
                  </Link>
                </div>
                <div className="row">
                  <Link to="/forgot" className="cta">
                    {t("forgot")}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </Wrap>
  );
}

const Wrap = styled.div`
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  
  /* Loader Wrapper - Full screen centered */
  .loaderWrapper {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
  }
  
  /* Left Side - 3D Interactive Background */
  .leftSide {
    position: relative;
    background: linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .content {
    position: relative;
    z-index: 1;
    text-align: center;
    color: white;
    padding: 40px;
  }

  .brand {
    font-size: clamp(36px, 5vw, 56px);
    font-weight: 800;
    margin: 0 0 16px 0;
    background: linear-gradient(to bottom, #ffffff, rgba(255, 255, 255, 0.7));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .tagline {
    font-size: clamp(16px, 2vw, 20px);
    margin: 0;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }

  /* Right Side - Form */
  .rightSide {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: #ffffff;
  }

  .formContainer {
    width: 100%;
    max-width: 420px;
    animation: slideInRight 0.6s ease-out;
  }

  @keyframes slideInRight {
    from {
      opacity: 0;
      transform: translateX(30px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .links {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .row {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .muted {
    color: ${({ theme }) => theme.colors.secondary};
    font-size: 0.96rem;
  }

  .cta {
    color: ${({ theme }) => theme.colors.accent};
    font-weight: 700;
    text-decoration: none;
    font-size: 0.96rem;
    transition: color 0.2s ease;
    position: relative;
  }

  .cta::after {
    content: "";
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: ${({ theme }) => theme.colors.accent};
    transform: scaleX(0);
    transition: transform 0.2s ease;
  }

  .cta:hover {
    color: ${({ theme }) => theme.colors.accent2};
  }

  .cta:hover::after {
    transform: scaleX(1);
  }

  /* Mobile Responsive */
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    
    .leftSide {
      display: none;
    }

    .rightSide {
      padding: 24px;
    }
  }
`;
