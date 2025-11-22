import { useEffect, useState } from "react";
import styled from "styled-components";
import Sidebar from "@/components/layout/Sidebar";
import { Outlet, useLocation } from "react-router-dom";
import { useI18n } from "@/app/i18n";

export default function AppLayout() {
  useI18n();
  useLocation();

  const [collapsed, setCollapsed] = useState(false);
  // COMMENTED OUT: Banner feature removed
  // const [needProfile, setNeedProfile] = useState(false);

  /* ====== Onboarding check ====== */
  // COMMENTED OUT: No longer requiring onboarding flow
  // useEffect(() => {
  //   const onboardingCompleted = localStorage.getItem("onboardingCompleted");
  //   if (!onboardingCompleted) {
  //     navigate("/onboarding/topics", { replace: true });
  //   }
  // }, [navigate]);

  /* ====== Guard ====== */
  // COMMENTED OUT: Auth guard - no longer checking authentication or redirecting to signin
  // useEffect(() => {
  //   let alive = true;
  //   me()
  //     .then(() => {})
  //     .catch(() => {
  //       try { sessionStorage.removeItem("activeSessionId"); } catch {}
  //       if (alive) navigate("/signin", { replace: true });
  //     });
  //   return () => { alive = false; };
  // }, [navigate]);

  /* ====== bfcache ====== */
  // COMMENTED OUT: bfcache auth check - no longer validating session on page show
  // useEffect(() => {
  //   const onPageShow = (e: PageTransitionEvent) => {
  //     if ((e as any).persisted) {
  //       me().catch(() => {
  //         try { sessionStorage.removeItem("activeSessionId"); } catch {}
  //         navigate("/signin", { replace: true });
  //       });
  //     }
  //   };
  //   window.addEventListener("pageshow", onPageShow as any);
  //   return () => window.removeEventListener("pageshow", onPageShow as any);
  // }, [navigate]);

  /* ====== Sidebar state ====== */
  useEffect(() => {
    try { setCollapsed(localStorage.getItem("sbCollapsed") === "1"); } catch {}
  }, []);
  const toggle = () =>
    setCollapsed((v) => {
      const n = !v;
      try { localStorage.setItem("sbCollapsed", n ? "1" : "0"); } catch {}
      return n;
    });

  /* ====== Banner ====== */
  // COMMENTED OUT: Banner feature removed - no longer checking profile completeness
  // useEffect(() => {
  //   let alive = true;
  //   let timer: number | null = null;

  //   const computeNeed = (p: ProfileLite | null) => {
  //     const nameOk = !!p?.name?.toString().trim();
  //     const ageOk =
  //       p?.age != null && Number.isInteger(p.age as number) &&
  //       (p!.age as number) >= 14 && (p!.age as number) <= 100;
  //     const cityOk = !!p?.city?.toString().trim();
  //     return !(nameOk && ageOk && cityOk);
  //   };

  //   const fetchProfile = async () => {
  //     try {
  //       const p = (await getProfile()) as ProfileLite;
  //       if (alive) setNeedProfile(computeNeed(p));
  //     } catch (e: any) {
  //       const status = e?.response?.status;
  //       if (alive && (status === 404 || status === 204 || status === 401)) {
  //         setNeedProfile(true);
  //       }
  //     }
  //   };

  //   fetchProfile();
  //   const startPoll = () => { stopPoll(); timer = window.setInterval(fetchProfile, 15000); };
  //   const stopPoll = () => { if (timer != null) { clearInterval(timer); timer = null; } };

  //   const onFocus = () => fetchProfile();
  //   const onVisibility = () => { if (document.visibilityState === "visible") fetchProfile(); };
  //   const onProfileUpdated = () => fetchProfile();

  //   startPoll();
  //   window.addEventListener("focus", onFocus);
  //   document.addEventListener("visibilitychange", onVisibility);
  //   window.addEventListener("profile-updated", onProfileUpdated as EventListener);

  //   return () => {
  //     alive = false;
  //     stopPoll();
  //     window.removeEventListener("focus", onFocus);
  //     document.removeEventListener("visibilitychange", onVisibility);
  //     window.removeEventListener("profile-updated", onProfileUpdated as EventListener);
  //   };
  // }, [pathname]);

  // const goProfile = () => navigate("/profile");

  // const bannerTitle =
  //   lang === "vi" ? "Hoàn tất hồ sơ của bạn" : "Complete your profile";
  // const bannerText =
  //   lang === "vi"
  //     ? "Vui lòng cập nhật hồ sơ để ChatGOV có thể cá nhân hoá câu trả lời."
  //     : "Please fill your Full name, Age and City/District so ChatGOV can personalize answers.";
  // const bannerBtn = lang === "vi" ? "Đi tới Hồ sơ" : "Go to Profile";

  return (
    <Shell
      data-collapsed={collapsed ? "true" : "false"}
    >
      <aside className="rail">
        <Sidebar collapsed={collapsed} onToggle={toggle} />
      </aside>

      <section className="main">
        <MobileMenuButton onClick={toggle} aria-label="Menu" className="mobile-menu-btn">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 6h18M3 12h18M3 18h18"/>
          </svg>
        </MobileMenuButton>

        {/* COMMENTED OUT: Banner removed */}
        {/* {needProfile && (
          <Banner role="status" aria-live="polite">
            <div className="msg">
              <div className="icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M12 2 1 21h22L12 2z" fill="currentColor" opacity=".12" />
                  <path d="M12 8a1 1 0 1 0-1-1 1 1 0 0 0 1 1Zm-1 3h2v7h-2z" fill="currentColor" />
                </svg>
              </div>
              <div className="text">
                <div className="title">{bannerTitle}</div>
                <div className="desc">{bannerText}</div>
              </div>
            </div>
            <button className="go" onClick={goProfile}>{bannerBtn}</button>
          </Banner>
        )} */}

        <div className="content">
          <Outlet />
        </div>
      </section>
    </Shell>
  );
}

/* =============== styles =============== */
const MobileMenuButton = styled.button`
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 100;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  box-shadow: 
    0 4px 16px rgba(13, 148, 136, 0.12),
    0 1px 4px rgba(0, 0, 0, 0.04),
    inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(13, 148, 136, 0.12);
  color: ${({ theme }) => theme.colors.accent};
  cursor: pointer;
  transition: all 0.2s ease;
  align-items: center;
  justify-content: center;

  &:hover {
    background: rgba(13, 148, 136, 0.05);
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }

  @media (min-width: 981px) {
    display: none !important;
  }
`;

const Shell = styled.div`
  --rail: 280px;
  --rail-collapsed: 68px;
  --topbar-h: 60px;
  --banner-h: 56px;

  height: 100vh;
  display: grid;
  grid-template-columns: var(--rail) 1fr;
  overflow: hidden;

  /* Set CSS variable for sidebar width */
  --sidebar-width: var(--rail);

  &[data-collapsed="true"] {
    grid-template-columns: var(--rail-collapsed) 1fr;
    --sidebar-width: var(--rail-collapsed);
  }

  .rail {
    height: 100%;
    overflow: hidden;
    border-right: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface};
  }

  .main {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .content {
    flex: 1;
    min-height: 0;
    overflow: auto;
    background: ${({ theme }) => theme.colors.bg};
    padding-top: 0;
  }

  /* COMMENTED OUT: Banner feature removed */
  /* &[data-banner="1"] .content {
    padding-top: calc(var(--topbar-h) + var(--banner-h));
  } */

  /* Hide menu button on desktop */
  @media (min-width: 981px) {
    .mobile-menu-btn {
      display: none !important;
    }
  }

  /* ===== MOBILE OVERLAY SIDEBAR ===== */
  @media (max-width: 980px) {
    /* grid 1 cột, không giữ cột rail rỗng */
    grid-template-columns: 1fr !important;

    .content { 
      padding-top: 64px; /* Space for hamburger button */
    }
    /* COMMENTED OUT: Banner feature removed */
    /* &[data-banner="1"] .content { 
      padding-top: 64px;
    } */

    /* Show menu button on mobile */
    .mobile-menu-btn {
      display: flex !important;
    }

    .rail {
      display: none;
      position: fixed;
      inset: 0 auto 0 0;
      width: min(86vw, 320px);
      max-width: 92vw;
      z-index: 150;
      background: transparent;
      transform: translateX(-100%);
      transition: transform 0.28s ease, visibility 0s linear 0.28s;
      will-change: transform;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      visibility: hidden;
      pointer-events: none;
    }
    &[data-collapsed="false"] .rail {
      display: block;
      transform: translateX(0);
      visibility: visible;
      pointer-events: auto;
      transition: transform 0.28s ease, visibility 0s;
    }
    &[data-collapsed="false"]::after {
      content: "";
      position: fixed;
      inset: 0;
      z-index: 140;
      background: rgba(0,0,0,0.25);
      backdrop-filter: blur(1px);
    }
  }
`;

/* COMMENTED OUT: Topbar and Banner components - no longer used */
/* const Topbar = styled.header`
  position: absolute;
  inset: 0 0 auto 0;
  height: var(--topbar-h);
  z-index: 5;
  pointer-events: none;

  .chrome {
    height: var(--topbar-h);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 0 16px;
    background: transparent;
    border-bottom: 0;
    backdrop-filter: none;
    color: ${({ theme }) => theme.colors.accent2};
    font-weight: 800;
    pointer-events: none;
  }

  .title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 60vw;
    pointer-events: none;
  }

  .menuBtn {
    display: none;
    border: none;
    background: transparent;
    width: 40px;
    height: 40px;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    cursor: pointer;
    color: ${({ theme }) => theme.colors.primary};
    pointer-events: auto;
  }
  .menuBtn:active { transform: scale(0.98); }

  @media (max-width: 980px) {
    position: sticky;
    top: 0;
    pointer-events: auto;
    .chrome {
      pointer-events: auto;
      background: rgba(255, 255, 255, 0.85);
      backdrop-filter: saturate(150%) blur(10px);
      border-bottom: 1px solid ${({ theme }) => theme.colors.border};
    }
    .menuBtn { display: flex; }
  }
`; */

/* COMMENTED OUT: Banner component - no longer used
const Banner = styled.div\`
  --r: 14px;
  position: absolute;
  top: var(--topbar-h);
  left: 0;
  right: 0;
  height: var(--banner-h);
  z-index: 6;

  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 10px 12px 10px 14px;

  background: linear-gradient(90deg, rgba(206,122,88,0.95), rgba(143,56,42,0.95));
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);

  .msg { display: flex; gap: 10px; align-items: center; min-width: 0; }
  .icon { width: 22px; height: 22px; display: grid; place-items: center; opacity: .9; flex: 0 0 auto; }
  .icon svg { width: 22px; height: 22px; fill: currentColor; }
  .text { min-width: 0; }
  .title { font-weight: 800; line-height: 1.1; }
  .desc { opacity: .96; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .go {
    height: 36px; padding: 0 14px; border-radius: var(--r); border: none; cursor: pointer;
    font-weight: 800; color: #fff; background: rgba(255,255,255,.18);
    box-shadow: 0 4px 14px rgba(0,0,0,.15) inset; transition: filter .15s, transform .06s;
  }
  .go:hover { filter: brightness(1.05); }
  .go:active { transform: translateY(1px); }

  @media (max-width: 980px) {
    position: sticky;
    top: var(--topbar-h);
    height: auto;
    grid-template-columns: 1fr;
    align-items: start;
    gap: 8px;
    padding: 10px 12px;

    .msg { align-items: flex-start; }
    .desc {
      white-space: normal;
      overflow: visible;
      text-overflow: clip;
    }
    .go {
      width: 100%;
      height: 40px;
      border-radius: 12px;
      justify-self: end;
    }
  }
\`;
*/
