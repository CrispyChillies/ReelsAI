import styled from "styled-components";
import { useI18n } from "@/app/i18n";
// COMMENTED OUT: Backend API calls
// import { logout as apiLogout, me } from "@/services/auth";
import { useNavigate, useLocation } from "react-router-dom";
import { useToast } from "@/app/toast";
import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import SessionList, {
  type Session,
} from "@/components/common/chat/SessionList";
// COMMENTED OUT: Backend session API
// import {
//   listSessions,
//   renameSession as apiRename,
//   deleteSession as apiDelete,
//   type ChatSession,
// } from "@/services/sessions";
import SearchSessionsModal from "@/components/common/chat/SearchSessionsModal";

// DEMO: Local ChatSession type definition
type ChatSession = {
  session_id: string;
  user_id: string;
  title?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  messages_count: number;
};

type Props = { collapsed: boolean; onToggle: () => void };

// /public
const SIDEBAR_BG = "/banner.jpg";
const LOGO = "/logo.png";

export default function Sidebar({ collapsed, onToggle }: Props) {
  const { t } = useI18n();
  const nav = useNavigate();
  const location = useLocation() as any;
  const { pathname, state } = location;
  const { notify } = useToast();

  // COMMENTED OUT: No user auth needed
  // const [userId, setUserId] = useState<string | null>(null);
  
  // DEMO: Use localStorage for sessions persistence
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const stored = localStorage.getItem("demo-sessions");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [openSearch, setOpenSearch] = useState(false);

  // --- Active session id: ưu tiên location.state, fallback sessionStorage
  const activeIdFromState = state?.sessionId ?? null;
  const [activeId, setActiveId] = useState<string | null>(
    activeIdFromState || sessionStorage.getItem("activeSessionId")
  );

  // --- MODAL STATES: rename / delete
  const [renameTarget, setRenameTarget] = useState<{
    id: string;
    value: string;
  } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Sync active id và title khi location.state thay đổi
  useEffect(() => {
    if (activeIdFromState) {
      sessionStorage.setItem("activeSessionId", activeIdFromState);
      setActiveId(activeIdFromState);

      // Update title in local state immediately when it changes
      const newTitle = location?.state?.title;
      if (newTitle) {
        setSessions((prev) => {
          const updated = prev.map((s) =>
            s.session_id === activeIdFromState ? { ...s, title: newTitle } : s
          );
          // Save to localStorage
          localStorage.setItem("demo-sessions", JSON.stringify(updated));
          return updated;
        });
      }
    }
  }, [activeIdFromState, location?.state?.title]);

  // COMMENTED OUT: No auth check needed
  // useEffect(() => {
  //   me()
  //     .then((u) => setUserId(u.id))
  //     .catch(() => {});
  // }, []);

  // DEMO: Create demo session if needed
  useEffect(() => {
    const sid = location?.state?.sessionId;
    if (sid && !sessions.find(s => s.session_id === sid)) {
      const newSession: ChatSession = {
        session_id: sid,
        user_id: "demo-user",
        title: location?.state?.title || t("newChat") || "New chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages_count: 0
      };
      setSessions(prev => {
        const updated = [newSession, ...prev];
        localStorage.setItem("demo-sessions", JSON.stringify(updated));
        return updated;
      });
    }
  }, [location?.state?.sessionId, location?.state?.title, sessions, t]);

  // COMMENTED OUT: Backend session loading
  // // Refresh sessions when location state changes (for auto-naming)
  // const locationTitle = location?.state?.title;
  // useEffect(() => {
  //   if (!userId) return;
  //   listSessions()
  //     .then(setSessions)
  //     .catch((e) => {
  //       console.error(e);
  //     });
  // }, [userId, pathname, activeId, locationTitle]);

  const items: Session[] = useMemo(() => {
    return sessions.map((s) => ({
      id: s.session_id,
      title: s.title || t("newChat") || "New chat",
      active: s.session_id === activeId,
    }));
  }, [sessions, t, activeId]);

  // DEMO: Logout just clears local data (no backend call)
  const handleLogout = async () => {
    try {
      // Clear local demo data
      sessionStorage.clear();
      localStorage.removeItem("demo-sessions");
      
      notify({ title: "Demo", content: "Local data cleared (no real logout)", tone: "info" });
      
      // Just refresh the page or stay on home
      nav("/", { replace: true });
    } catch (e: any) {
      notify({
        title: t("error"),
        content: e?.message || "Error clearing data",
        tone: "error",
      });
    }
  };

  // COMMENTED OUT: Real backend logout
  // const handleLogout = async () => {
  //   try {
  //     await apiLogout();
  //     try {
  //       sessionStorage.clear();
  //       localStorage.removeItem("me");
  //     } catch {}
  //     notify({ title: t("signin"), content: t("signedOut"), tone: "info" });
  //     nav("/signin", { replace: true });
  //   } catch (e: any) {
  //     notify({
  //       title: t("error"),
  //       content: e?.response?.data?.detail || e?.message,
  //       tone: "error",
  //     });
  //   }
  // };
  const go = (to: string) => () => nav(to);

  const onNewChat = () => {
    sessionStorage.removeItem("activeSessionId");
    setActiveId(null);
    nav({ pathname: "/chat", search: "?new=1" });
  };

  const onSearch = () => setOpenSearch(true);

  const onSelect = (id: string) => {
    sessionStorage.setItem("activeSessionId", id);
    setActiveId(id);
    nav("/chat", { state: { sessionId: id } });
  };

  // --- mở modal rename
  const onRename = async (id: string) => {
    const current = sessions.find((s) => s.session_id === id)?.title || "";
    setRenameTarget({ id, value: current });
  };

  // --- mở modal xác nhận xoá
  const onDelete = async (id: string) => {
    // DEMO: No user check needed
    setDeleteTarget(id);
  };

  // --- SUBMIT RENAME (DEMO - localStorage only)
  const submitRename = async () => {
    if (!renameTarget) return;
    const next = renameTarget.value.trim();
    if (!next) return;
    try {
      setBusy(true);
      
      // DEMO: Update in localStorage instead of backend
      setSessions((prev) => {
        const updated = prev.map((s) =>
          s.session_id === renameTarget.id ? { ...s, title: next } : s
        );
        localStorage.setItem("demo-sessions", JSON.stringify(updated));
        return updated;
      });
      
      setRenameTarget(null);
      notify({ title: "Success", content: "Session renamed", tone: "success" });
    } catch (e: any) {
      notify({
        title: t("error"),
        content: e?.message || "Error renaming session",
        tone: "error",
      });
    } finally {
      setBusy(false);
    }
  };

  // COMMENTED OUT: Real backend rename
  // const submitRename = async () => {
  //   if (!renameTarget) return;
  //   const next = renameTarget.value.trim();
  //   if (!next) return;
  //   try {
  //     setBusy(true);
  //     await apiRename(renameTarget.id, next);
  //     setSessions((prev) =>
  //       prev.map((s) =>
  //         s.session_id === renameTarget.id ? { ...s, title: next } : s
  //       )
  //     );
  //     setRenameTarget(null);
  //   } catch (e: any) {
  //     notify({
  //       title: t("error"),
  //       content: e?.response?.data?.detail || e?.message,
  //       tone: "error",
  //     });
  //   } finally {
  //     setBusy(false);
  //   }
  // };

  // --- CONFIRM DELETE (DEMO - localStorage only)
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setBusy(true);
      
      // DEMO: Delete from localStorage instead of backend
      setSessions((prev) => {
        const updated = prev.filter((s) => s.session_id !== deleteTarget);
        localStorage.setItem("demo-sessions", JSON.stringify(updated));
        return updated;
      });
      
      if (activeId === deleteTarget) {
        sessionStorage.removeItem("activeSessionId");
        setActiveId(null);
        nav({ pathname: "/chat", search: "?new=1" });
      }
      setDeleteTarget(null);
      notify({ title: "Success", content: "Session deleted", tone: "success" });
    } catch (e: any) {
      notify({
        title: t("error"),
        content: e?.message || "Error deleting session",
        tone: "error",
      });
    } finally {
      setBusy(false);
    }
  };

  // COMMENTED OUT: Real backend delete
  // const confirmDelete = async () => {
  //   if (!deleteTarget || !userId) return;
  //   try {
  //     setBusy(true);
  //     await apiDelete(deleteTarget);
  //     setSessions((prev) => prev.filter((s) => s.session_id !== deleteTarget));
  //     if (activeId === deleteTarget) {
  //       sessionStorage.removeItem("activeSessionId");
  //       setActiveId(null);
  //       nav({ pathname: "/app", search: "?new=1" });
  //     }
  //     setDeleteTarget(null);
  //   } catch (e: any) {
  //     notify({
  //       title: t("error"),
  //       content: e?.response?.data?.detail || e?.message,
  //       tone: "error",
  //     });
  //   } finally {
  //     setBusy(false);
  //   }
  // };

  return (
    <Wrap data-collapsed={collapsed ? "true" : "false"} $bg={SIDEBAR_BG}>
      {/* Header */}
      <div className="head">
        <button className="logo" onClick={go("/")} aria-label="Home">
          <img src={LOGO} alt="Logo" className="logo-img" />
          <span className="brand-name">ReelsAI</span>
        </button>
        <button
          className="toggle"
          onClick={onToggle}
          title={collapsed ? t("expand") : t("collapse")}
          aria-label="Toggle sidebar"
        >
          <svg
            className="toggle-ic"
            data-rot={collapsed ? "1" : "0"}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="11 17 6 12 11 7"></polyline>
            <polyline points="18 17 13 12 18 7"></polyline>
          </svg>
        </button>
      </div>

      <div className="body">
        {/* Quick actions */}
        <div className="quick">
          <QuickBtn onClick={onNewChat} title={t("newChat")}>
            <SvgPen className="qicon" />
            <span className="qlabel">{t("newChat")}</span>
          </QuickBtn>
          <QuickBtn onClick={onSearch} title={t("searchChats")}>
            <SvgSearch className="qicon" />
            <span className="qlabel">{t("searchChats")}</span>
          </QuickBtn>
        </div>

        {/* Chats block */}
        <div className="sessionsWrap">
          <div className="sectionTitle">{t("chats")}</div>
          <div className="sessionsArea">
            <SessionList
              items={items}
              onSelect={onSelect}
              onRename={onRename}
              onDelete={onDelete}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <nav className="footer">
        <NavBtn
          onClick={go("/feed")}
          data-active={pathname === "/" || pathname === "/feed" ? "true" : "false"}
          title={t("feed")}
        >
          <SvgHome className="icon" />
          <span className="label">{t("feed")}</span>
        </NavBtn>

        <NavBtn
          onClick={go("/saved")}
          data-active={pathname === "/saved" ? "true" : "false"}
          title={t("contentStorage")}
        >
          <SvgBookmark className="icon" />
          <span className="label">{t("saved")}</span>
        </NavBtn>

        <NavBtn
          onClick={go("/profile")}
          data-active={pathname.startsWith("/profile") ? "true" : "false"}
          title={t("profile")}
        >
          <SvgUser className="icon" />
          <span className="label">{t("profile")}</span>
        </NavBtn>

        <NavBtn onClick={handleLogout} title={t("logout")}>
          <SvgLogout className="icon" />
          <span className="label">{t("logout")}</span>
        </NavBtn>
      </nav>

      {/* Search modal */}
      <SearchSessionsModal
        open={openSearch}
        onClose={() => setOpenSearch(false)}
        sessions={sessions}
        onChoose={(sid) => {
          sessionStorage.setItem("activeSessionId", sid);
          setActiveId(sid);
          nav("/chat", { state: { sessionId: sid } });
        }}
      />

      {/* --- MODAL RENAME --- */}
      {renameTarget && createPortal(
        <ModalOverlay onClick={() => !busy && setRenameTarget(null)}>
          <ModalCard onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <h4>{t("rename") || "Đổi tên"}</h4>
              <button
                onClick={() => !busy && setRenameTarget(null)}
                aria-label="Đóng"
              >
                ✕
              </button>
            </ModalHeader>
            <ModalBody>
              <label className="label">{t("rename")}</label>
              <input
                autoFocus
                placeholder={t("rename")}
                value={renameTarget.value}
                onChange={(e) =>
                  setRenameTarget((p) =>
                    p ? { ...p, value: e.target.value } : p
                  )
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") submitRename();
                  if (e.key === "Escape") setRenameTarget(null);
                }}
              />
            </ModalBody>
            <ModalActions>
              <button
                className="ghost"
                onClick={() => setRenameTarget(null)}
                disabled={busy}
              >
                {t("cancel")}
              </button>
              <button
                className="primary"
                onClick={submitRename}
                disabled={busy || !renameTarget.value.trim()}
              >
                {t("save")}
              </button>
            </ModalActions>
          </ModalCard>
        </ModalOverlay>,
        document.body
      )}

      {/* --- MODAL DELETE --- */}
      {deleteTarget && createPortal(
        <ModalOverlay onClick={() => !busy && setDeleteTarget(null)}>
          <ModalCard onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <h4>{t("confirmDelete")}</h4>
              <button
                onClick={() => !busy && setDeleteTarget(null)}
                aria-label={t("cancel")}
              >
                ✕
              </button>
            </ModalHeader>
            <ModalBody>
              <p style={{ margin: 0 }}>
                {t("deleteWarning")}
              </p>
            </ModalBody>
            <ModalActions>
              <button
                className="ghost"
                onClick={() => setDeleteTarget(null)}
                disabled={busy}
              >
                {t("cancel")}
              </button>
              <button
                className="danger"
                onClick={confirmDelete}
                disabled={busy}
              >
                {t("delete")}
              </button>
            </ModalActions>
          </ModalCard>
        </ModalOverlay>,
        document.body
      )}
    </Wrap>
  );
}

/* ============================= styles ============================= */
const Wrap = styled.aside<{ $bg: string }>`
  --sep: ${({ theme }) => theme.colors.border};

  height: 100%;
  display: grid;
  grid-template-rows: auto 1fr auto; /* header - body (scroll area bên trong) - footer */
  position: relative;
  perspective: 1500px;
  transform-style: preserve-3d;

  /* 3D Animated gradient background with depth */
  background: 
    linear-gradient(135deg, 
      rgba(13, 148, 136, 0.03) 0%, 
      rgba(255, 255, 255, 0.98) 35%,
      rgba(255, 255, 255, 0.95) 65%,
      rgba(13, 148, 136, 0.05) 100%
    );
  border-right: 1px solid rgba(13, 148, 136, 0.15);
  box-shadow: 
    4px 0 20px rgba(13, 148, 136, 0.08),
    inset -1px 0 0 rgba(13, 148, 136, 0.05);
  
  /* Animated gradient */
  background-size: 200% 200%;
  animation: gradientShift 15s ease infinite;

  @keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
  }

  /* 3D depth effect overlay */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(
      ellipse at top left,
      rgba(13, 148, 136, 0.08) 0%,
      transparent 60%
    );
    pointer-events: none;
    z-index: 0;
    animation: pulseGlow 8s ease-in-out infinite;
  }

  @keyframes pulseGlow {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  .head {
    position: sticky;
    top: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 10px 8px 10px;
    height: 52px;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.98) 0%,
      rgba(255, 255, 255, 0.95) 50%,
      rgba(13, 148, 136, 0.08) 100%
    );
    backdrop-filter: blur(12px);
    transform-style: preserve-3d;
    border-bottom: 1px solid rgba(13, 148, 136, 0.12);
    box-shadow: 0 2px 12px rgba(13, 148, 136, 0.08);
  }

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: auto;
    height: 44px;
    border: none;
    background: none;
    padding: 4px;
    cursor: pointer;
    transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
  }
  .logo:hover {
    transform: translateX(4px) translateZ(20px) rotateY(-5deg);
  }
  .logo-img {
    width: 44px;
    height: 44px;
    object-fit: contain;
    transition: transform 0.4s ease;
    filter: drop-shadow(0 2px 8px rgba(13, 148, 136, 0.3));
  }
  .logo:hover .logo-img {
    transform: rotateY(360deg) scale(1.1);
  }
  .brand-name {
    font-size: 20px;
    font-weight: 800;
    background: linear-gradient(135deg, ${({ theme }) => theme.colors.accent} 0%, ${({ theme }) => theme.colors.accent2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    text-shadow: 0 4px 12px rgba(13, 148, 136, 0.2);
  }

  .toggle {
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: ${({ theme }) => theme.colors.accent2};
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
  }
  .toggle:hover {
    transform: translateZ(10px) scale(1.15);
    background: rgba(13, 148, 136, 0.1);
    color: ${({ theme }) => theme.colors.accent};
  }
  .toggle-ic {
    width: 22px;
    height: 22px;
    transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }
  .toggle:hover .toggle-ic {
    transform: translateX(-2px) scale(1.1);
  }
  .toggle-ic[data-rot="1"] {
    transform: rotate(180deg);
  }
  .toggle:hover .toggle-ic[data-rot="1"] {
    transform: rotate(180deg) translateX(2px) scale(1.1);
  }

  &[data-collapsed="true"] {
    .head {
      justify-content: center;
      padding: 12px 10px;
    }
    .toggle {
      opacity: 0;
      pointer-events: none;
      position: absolute;
      right: 50%;
      transform: translateX(50%);
    }
    .logo {
      opacity: 1;
      width: 100%;
    }
    .brand-name {
      display: none;
    }
    .head:hover .toggle {
      opacity: 1;
      pointer-events: auto;
    }
    .head:hover .logo {
      opacity: 0;
    }

    .sessionsWrap {
      display: none;
    }
    .label {
      display: none;
    }
  }

  .body {
    z-index: 1;
    min-height: 0; /* để vùng giữa co được trong grid */
    display: grid;
    grid-template-rows: auto 1fr;
    gap: 10px;
    padding: 6px 10px;
    transform-style: preserve-3d;
  }

  .quick {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    perspective: 1000px;
  }

  .sessionsWrap {
    display: grid;
    grid-template-rows: auto 1fr;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--sep);
    min-height: 0; /* cho phép co trong grid */
    perspective: 1000px;
  }

  /* VÙNG CUỘN CỦA DANH SÁCH với 3D effect */
  .sessionsArea {
    min-height: 0;
    overflow: auto; /* <-- chỉ nơi này cuộn */
    padding-right: 4px;
    transform-style: preserve-3d;
  }

  .sectionTitle {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: ${({ theme }) => theme.colors.accent};
    margin: 6px 4px 8px;
    opacity: 0.7;
    text-shadow: 0 2px 8px rgba(13, 148, 136, 0.15);
  }

  .footer {
    z-index: 1;
    padding: 8px 10px 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    border-top: 1px solid var(--sep);
    background: linear-gradient(
      to top,
      rgba(255, 255, 255, 0.98),
      rgba(255, 255, 255, 0.85)
    );
    backdrop-filter: blur(10px);
    transform-style: preserve-3d;
    box-shadow: 0 -4px 12px rgba(13, 148, 136, 0.06);
  }

  /* Scrollbar gọn cho vùng sessionsArea với 3D styling */
  .sessionsArea::-webkit-scrollbar {
    width: 10px;
  }
  .sessionsArea::-webkit-scrollbar-track {
    background: rgba(13, 148, 136, 0.05);
    border-radius: 10px;
    box-shadow: inset 0 0 6px rgba(13, 148, 136, 0.1);
  }
  .sessionsArea::-webkit-scrollbar-thumb {
    background: linear-gradient(
      180deg,
      ${({ theme }) => theme.colors.accent},
      ${({ theme }) => theme.colors.accent2}
    );
    border-radius: 10px;
    border: 2px solid transparent;
    background-clip: content-box;
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.3);
    transition: all 0.3s ease;
  }
  .sessionsArea::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(
      180deg,
      ${({ theme }) => theme.colors.accent2},
      ${({ theme }) => theme.colors.accent}
    );
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.5);
  }
  .sessionsArea {
    scrollbar-width: thin;
    scrollbar-color: ${({ theme }) => theme.colors.accent} rgba(13, 148, 136, 0.05);
  }

  @media (max-width: 920px) {
    background-position: center;
  }
`;

const QuickBtn = styled.button`
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(13, 148, 136, 0.2);
  color: ${({ theme }) => theme.colors.accent2};
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 2px 8px rgba(13, 148, 136, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);

  /* 3D shimmer effect */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
      120deg,
      transparent 0%,
      rgba(13, 148, 136, 0.1) 50%,
      transparent 100%
    );
    transform: translateX(-100%) skewX(-15deg);
    transition: transform 0.6s ease;
  }

  .qicon {
    width: 18px;
    height: 18px;
    color: ${({ theme }) => theme.colors.accent};
    transition: transform 0.3s ease;
    filter: drop-shadow(0 2px 4px rgba(13, 148, 136, 0.3));
  }
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    border-color: ${({ theme }) => theme.colors.accent};
    transform: translateX(4px) translateZ(15px) rotateY(-3deg);
    box-shadow: 
      -4px 6px 20px rgba(13, 148, 136, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 1);
  }
  
  &:hover::before {
    transform: translateX(100%) skewX(-15deg);
  }
  
  &:hover .qicon {
    transform: rotate(360deg) scale(1.2);
  }
  
  &:active {
    transform: translateX(2px) translateZ(5px) scale(0.98);
  }

  [data-collapsed="true"] & {
    justify-content: center;
    padding: 12px;
  }
  [data-collapsed="true"] & .qlabel {
    display: none;
  }
  [data-collapsed="true"] & .qicon {
    margin: 0;
  }
`;

const NavBtn = styled.button`
  --r: 999px;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 14px;
  border-radius: var(--r);
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(13, 148, 136, 0.2);
  color: ${({ theme }) => theme.colors.accent2};
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 2px 10px rgba(13, 148, 136, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);

  /* 3D depth layer */
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--r);
    background: radial-gradient(
      circle at center,
      rgba(13, 148, 136, 0.1) 0%,
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .icon {
    width: 20px;
    height: 20px;
    color: ${({ theme }) => theme.colors.accent};
    transition: all 0.3s ease;
    filter: drop-shadow(0 2px 4px rgba(13, 148, 136, 0.3));
  }
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    border-color: ${({ theme }) => theme.colors.accent};
    transform: translateX(6px) translateZ(20px) rotateY(-5deg);
    box-shadow: 
      -6px 8px 24px rgba(13, 148, 136, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 1);
  }
  
  &:hover::after {
    opacity: 1;
  }
  
  &:hover .icon {
    transform: rotateY(360deg) scale(1.15);
    color: ${({ theme }) => theme.colors.accent2};
  }
  
  &:active {
    transform: translateX(3px) translateZ(10px) scale(0.97);
  }
  
  &:focus-visible,
  &[data-active="true"] {
    outline: none;
    background: linear-gradient(
      90deg,
      ${({ theme }) => theme.colors.accent},
      ${({ theme }) => theme.colors.accent2}
    );
    border: 2px solid transparent;
    background-clip: padding-box;
    position: relative;
    color: #fff;
    transform: translateZ(15px);
    box-shadow: 
      0 8px 28px ${({ theme }) => `${theme.colors.accent}50`},
      inset 0 2px 4px rgba(255, 255, 255, 0.3);
  }

  &:focus-visible::before,
  &[data-active="true"]::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: var(--r);
    padding: 2px;
    background: linear-gradient(
      90deg,
      ${({ theme }) => theme.colors.accent},
      ${({ theme }) => theme.colors.accent2}
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    z-index: -1;
  }
  
  &:focus-visible .icon,
  &[data-active="true"] .icon {
    color: #fff;
    filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.3));
  }
  
  [data-collapsed="true"] & {
    justify-content: center;
    padding: 12px;
    border-radius: 12px;
  }
  [data-collapsed="true"] & .label {
    display: none;
  }
  [data-collapsed="true"] & .icon {
    margin: 0;
  }
`;

/* --- MODAL styles --- */
const ModalOverlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: grid;
  place-items: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

const ModalCard = styled.div`
  width: min(520px, 92vw);
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.primary};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 16px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(13, 148, 136, 0.1);
  display: grid;
  grid-template-rows: auto 1fr auto;
  animation: slideUp 0.3s ease;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid ${({ theme }) => theme.colors.border};

  h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 800;
    color: ${({ theme }) => theme.colors.accent2};
  }
  button {
    min-width: 32px;
    height: 32px;
    border-radius: 8px;
    cursor: pointer;
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface2};
    color: ${({ theme }) => theme.colors.secondary};
  }
  button:hover {
    color: ${({ theme }) => theme.colors.accent2};
    border-color: ${({ theme }) => theme.colors.accent};
    background: ${({ theme }) => `${theme.colors.accent}20`};
  }
`;

const ModalBody = styled.div`
  padding: 14px;

  .label {
    display: block;
    font-size: 12px;
    color: ${({ theme }) => theme.colors.secondary};
    margin-bottom: 6px;
  }
  input {
    width: 100%;
    background: ${({ theme }) => theme.colors.surface2};
    border: 1px solid ${({ theme }) => theme.colors.border};
    color: ${({ theme }) => theme.colors.primary};
    border-radius: ${({ theme }) => theme.radii.md};
    padding: 10px 12px;
    outline: none;
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
  }
  input:focus {
    border-color: ${({ theme }) => theme.colors.accent};
    box-shadow: 0 0 0 3px ${({ theme }) => `${theme.colors.accent}30`};
  }
  p {
    color: ${({ theme }) => theme.colors.primary};
  }
`;

const ModalActions = styled.div`
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 12px 14px;
  border-top: 1px solid ${({ theme }) => theme.colors.border};

  button {
    min-width: 84px;
    height: 36px;
    padding: 0 14px;
    border-radius: 10px;
    cursor: pointer;
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface2};
    color: ${({ theme }) => theme.colors.secondary};
    transition: all 0.12s ease;
  }
  button:hover:not(:disabled) {
    color: ${({ theme }) => theme.colors.accent2};
    border-color: ${({ theme }) => theme.colors.accent};
    background: ${({ theme }) => `${theme.colors.accent}20`};
  }
  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .primary {
    background: linear-gradient(
      90deg,
      ${({ theme }) => theme.colors.accent},
      ${({ theme }) => theme.colors.accent2}
    );
    color: #fff;
    border-color: transparent;
  }
  .primary:hover:not(:disabled) {
    filter: brightness(0.97);
  }
  .danger {
    background: #ffebe8;
    color: #b42318;
    border-color: #ffd0cb;
  }
  .danger:hover:not(:disabled) {
    background: #ffe0db;
    border-color: #ffb7af;
    color: #b42318;
  }
  .ghost {
  }
`;

/* SVGs */
const SvgHome = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);

const SvgChat = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const SvgPen = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" {...p}>
    <path d="M12 20h9" strokeWidth="2" />
    <path
      d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"
      strokeWidth="2"
    />
  </svg>
);
const SvgSearch = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" {...p}>
    <circle cx="11" cy="11" r="7" strokeWidth="2" />
    <path d="M20 20l-3.5-3.5" strokeWidth="2" />
  </svg>
);
const SvgUser = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" {...p}>
    <path d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Z" strokeWidth="2" />
    <path d="M3 20a9 6 0 0 1 18 0v1H3z" strokeWidth="2" />
  </svg>
);

const SvgBookmark = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);

// const SvgSetting = (p: React.SVGProps<SVGSVGElement>) => (
//   <svg
//     viewBox="0 0 24 24"
//     fill="none"
//     stroke="currentColor"
//     strokeWidth={2}
//     strokeLinecap="round"
//     strokeLinejoin="round"
//     {...p}
//   >
//     <circle cx="12" cy="12" r="3" />
//     <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09c.7 0 1.31-.4 1.51-1a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06c.51.51 1.23.66 1.82.33.46-.26 1-.81 1-1.51V3a2 2 0 0 1 4 0v.09c0 .7.4 1.31 1 1.51.59.33 1.31.18 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06c-.36.36-.48.9-.33 1.82.2.59.81 1 1.51 1H21a2 2 0 0 1 0 4h-.09c-.7 0-1.31.4-1.51 1Z" />
//   </svg>
// );

const SvgLogout = (p: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" {...p}>
    <path
      d="M10 7V4a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2v-3"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path d="M15 12H3m4-4-4 4 4 4" stroke="currentColor" strokeWidth="2" />
  </svg>
);
