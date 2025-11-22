import styled from "styled-components";
import SignupForm from "@/components/forms/SignupForm";
import { Link } from "react-router-dom";
import { useI18n } from "@/app/i18n";
import ThreeDBackground from "@/components/common/ThreeDBackground";
import { useAuth } from "@/hooks/useAuth";
import type { RegisterRequest } from "@/types/auth";

export default function SignUp() {
  const { register: registerUser, isRegistering } = useAuth();
  const { t } = useI18n();

  const handleSubmit = (data: RegisterRequest) => {
    registerUser(data);
  };

  return (
    <Wrap>
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
          <SignupForm onSubmit={handleSubmit} loading={isRegistering} />
          <div className="links">
            <span className="muted">{t("haveAccount")}</span>
            <Link to="/auth/sign-in" className="cta">
              {t("signin")}
            </Link>
          </div>
        </div>
      </div>
    </Wrap>
  );
}

/* ============ styles ============ */
const Wrap = styled.div`
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  
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
