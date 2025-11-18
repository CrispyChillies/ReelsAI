import { useState } from "react";
import styled from "styled-components";
// COMMENTED OUT: Backend register API
// import { register } from "@/services/auth";
import SignupForm from "@/components/forms/SignupForm";
import { Link } from "react-router-dom";
import LoaderPage from "@/components/common/loaders/LoaderPage";
import { useToast } from "@/app/toast";
import { useI18n } from "@/app/i18n";
import ThreeDBackground from "@/components/common/ThreeDBackground";
// COMMENTED OUT: Error formatter
// import { formatError } from "@/utils/formatError";

export default function SignUp() {
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();
  const { t } = useI18n();

  const submit = async ({
    email,
    password,
    fullName,
  }: {
    email: string;
    password: string;
    fullName: string;
  }) => {
    setLoading(true);
    
    // DEMO: Simulate signup without backend
    setTimeout(() => {
      notify({ title: "Demo Signup", content: `Account created for ${fullName}`, tone: "success" });
      setLoading(false);
      // Navigate to check-email page
      window.location.href = `/check-email?mode=verify&email=${encodeURIComponent(email)}`;
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
              <p className="tagline">Join thousands of users today</p>
            </div>
          </div>

          {/* Right Side - Form */}
          <div className="rightSide">
            <div className="formContainer">
              <SignupForm onSubmit={submit} loading={loading} />
              <div className="links">
                <span className="muted">{t("haveAccount")}</span>
                <Link to="/signin" className="cta">
                  {t("signin")}
                </Link>
              </div>
            </div>
          </div>
        </>
      )}
    </Wrap>
  );
}

/* ============ styles ============ */
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
  
  /* Left Side - Animated Background */
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
    align-items: center;
    justify-content: center;
    gap: 10px;
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
