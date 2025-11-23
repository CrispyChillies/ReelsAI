import { useEffect, useLayoutEffect, useRef, useState } from "react";
import styled from "styled-components";
import PromptInput from "@/components/common/chat/PromptInput";
import ChatMessage from "@/components/common/chat/ChatMessage";
import LoaderTyping from "@/components/common/loaders/LoaderTyping";
import FloatingParticles from "@/components/common/FloatingParticles";
import { useI18n } from "@/app/i18n";
import { useLocation, useNavigate } from "react-router-dom";
import { useChatbot, useChatMessages } from "@/hooks/useChatbot";

type Msg = { id: string; role: "user" | "assistant"; content: string };

const SCROLL_DURATION_MS = 900;
const easeInOut = (t: number) =>
  t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [typing, setTyping] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const innerRef = useRef<HTMLDivElement | null>(null);

  const [autoFollow, setAutoFollow] = useState(true);
  const [, setUnread] = useState(0);

  const animIdRef = useRef<number | null>(null);
  const prevTopRef = useRef<number>(0);

  const footerRef = useRef<HTMLDivElement | null>(null);
  const [footerH, setFooterH] = useState<number>(120);

  const { t } = useI18n();
  const isEmpty = messages.length === 0;

  // session & user
  const [sessionId, setSessionId] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem("activeSessionId");
    } catch {
      return null;
    }
  });
  const location = useLocation() as any;
  const nav = useNavigate();
  
  // Use chatbot hooks
  const { sendMessage } = useChatbot();
  const { 
    messages: apiMessages, 
    fetchMessages, 
    clearMessages 
  } = useChatMessages(sessionId);

  // Load messages when session ID changes
  useEffect(() => {
    if (sessionId) {
      fetchMessages();
    } else {
      clearMessages();
    }
  }, [sessionId]);

  // Convert API messages to UI format
  useEffect(() => {
    const converted: Msg[] = apiMessages
      .filter(m => m.message_type === 'human' || m.message_type === 'ai')
      .map(m => ({
        id: m.id,
        role: m.message_type === 'human' ? 'user' : 'assistant',
        content: m.content,
        metadata: m.metadata // Include metadata for images/videos/embeds
      }));
    setMessages(converted);
  }, [apiMessages]);

  // --- Detect "new chat" bằng ?new=1 -> reset
  useEffect(() => {
    const sp = new URLSearchParams(location.search || "");
    if (sp.get("new") === "1") {
      setSessionId(null);
      setMessages([]);
      clearMessages();
      // cleanup trạng thái active đã lưu
      sessionStorage.removeItem("activeSessionId");
      // bỏ ?new=1 khỏi url (đẹp URL)
      nav(location.pathname, { replace: true });
      // scroll to bottom sau reset
      requestAnimationFrame(() => scrollToBottom(true));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  // Handle session selection from sidebar
  useEffect(() => {
    const sid = location?.state?.sessionId as string | undefined;
    if (sid && sid !== sessionId) {
      setSessionId(sid);
      sessionStorage.setItem("activeSessionId", sid);
      requestAnimationFrame(() => scrollToBottom(true));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location?.state?.sessionId]);

  const cancelAnim = () => {
    if (animIdRef.current) cancelAnimationFrame(animIdRef.current);
    animIdRef.current = null;
  };

  const animateToBottom = (duration = SCROLL_DURATION_MS) => {
    const el = scrollRef.current;
    if (!el) return;

    cancelAnim();
    const startTop = el.scrollTop;
    const startTime = performance.now();

    const step = (now: number) => {
      const target = el.scrollHeight - el.clientHeight;
      const t = Math.min(1, (now - startTime) / duration);
      el.scrollTop = startTop + (target - startTop) * easeInOut(t);

      if (t < 1) {
        animIdRef.current = requestAnimationFrame(step);
      } else {
        animIdRef.current = null;
      }
    };

    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        prevTopRef.current = el.scrollTop;
        step(performance.now());
      })
    );

    setUnread(0);
  };

  const scrollToBottom = (instant = false) => {
    const el = scrollRef.current;
    if (!el) return;
    if (instant) {
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          cancelAnim();
          el.scrollTop = el.scrollHeight;
          prevTopRef.current = el.scrollTop;
        })
      );
    } else {
      animateToBottom();
    }
    setAutoFollow(true);
    setUnread(0);
  };

  useEffect(() => {
    scrollToBottom(true);
  }, []);

  useLayoutEffect(() => {
    if (autoFollow) scrollToBottom(false);
    else if (messages.length) setUnread((n) => n + 1);
  }, [messages, typing]);

  useEffect(() => {
    if (!innerRef.current) return;
    const ro = new ResizeObserver(() => {
      if (autoFollow) scrollToBottom(false);
    });
    ro.observe(innerRef.current);
    return () => ro.disconnect();
  }, [autoFollow]);

  useEffect(() => {
    if (!footerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const h =
        entries[0]?.contentRect?.height || footerRef.current!.offsetHeight;
      setFooterH(Math.round(h));
    });
    ro.observe(footerRef.current);
    return () => ro.disconnect();
  }, []);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;

    const threshold = 60;
    const deltaToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    const atBottom = deltaToBottom < threshold;

    const prevTop = prevTopRef.current;
    const nowTop = el.scrollTop;
    const userScrolledUp = nowTop < prevTop - 1;
    prevTopRef.current = nowTop;

    if (userScrolledUp) {
      cancelAnim();
      setAutoFollow(false);
    } else if (atBottom) {
      setAutoFollow(true);
      setUnread(0);
    }
  };

  const jumpToBottom = () => {
    scrollToBottom(false);
  };

  // ---------------------- SEND MESSAGE WITH REAL API ----------------------
  const onSend = async (p: { prompt: string; rootUrl?: string }) => {
    if (!p?.prompt?.trim()) return;
    setTyping(true);

    try {
      // Add user message to UI immediately (optimistic update)
      const uid = crypto.randomUUID();
      const aid = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: uid, role: "user", content: p.prompt },
        { id: aid, role: "assistant", content: "" },
      ]);

      // Send message to backend
      const response = await sendMessage({
        message: p.prompt,
        session_id: sessionId || undefined,
      });

      if (response) {
        // Update session ID if new session created
        if (!sessionId && response.session_id) {
          setSessionId(response.session_id);
          sessionStorage.setItem("activeSessionId", response.session_id);
          nav(location.pathname, {
            state: { 
              ...location.state, 
              sessionId: response.session_id,
              title: p.prompt.slice(0, 50) + (p.prompt.length > 50 ? "..." : "")
            },
            replace: true,
          });
        }

        // Update assistant message with response
        setMessages((prev) =>
          prev.map((m) => 
            m.id === aid ? { ...m, content: response.message } : m
          )
        );

        // Reload messages to get full data from backend
        if (response.session_id) {
          await fetchMessages();
        }
      } else {
        // Error occurred - show error message
        setMessages((prev) =>
          prev.map((m) => 
            m.id === aid 
              ? { ...m, content: "Sorry, I encountered an error. Please try again." } 
              : m
          )
        );
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      // Show error in UI
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.content = "Sorry, I encountered an error. Please try again.";
        }
        return updated;
      });
    } finally {
      setTyping(false);
    }
  };
  // -----------------------------------------------------------

  return (
    <Main style={{ ["--footer-h" as any]: `${footerH}px` }}>
      {/* 3D Floating Particles Background */}
      <FloatingParticles />
      
      {isEmpty ? (
        <div className="home">
          <h1 className="hero">
            {t("heroTitle") ?? "Bạn đang cần hỗ trợ gì?"}
          </h1>
          <div className="heroComposer">
            <PromptInput onSend={onSend} maxWidth={720} compact />
          </div>
        </div>
      ) : (
        <>
          <div className="scroll" ref={scrollRef} onScroll={onScroll}>
            <div className="inner" ref={innerRef}>
              {messages.map((m, i) => {
                const isLast = i === messages.length - 1;
                const isAssistant = m.role === "assistant";
                const done = !(isLast && isAssistant && typing);
                return <ChatMessage key={m.id} msg={m as any} done={done} />;
              })}
              {typing && (
                <div className="typing">
                  <LoaderTyping />
                </div>
              )}
            </div>
          </div>

          {!autoFollow && (
            <button
              className="jump"
              onClick={jumpToBottom}
              aria-label={t("jumpToLatest") || "Jump to latest"}
              title={t("jumpToLatest") || "Jump to latest"}
            >
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path
                  d="M6 9l6 6 6-6"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}

          <footer className="input" ref={footerRef}>
            <PromptInput onSend={onSend} maxWidth={820} />
          </footer>
        </>
      )}
    </Main>
  );
}

const Main = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  
  /* Clean white base */
  background: #ffffff;

  /* Refined Grid Pattern with Radial Fade */
  &::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    background-image: 
      linear-gradient(to right, rgba(13, 148, 136, 0.15) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(13, 148, 136, 0.15) 1px, transparent 1px);
    background-size: 40px 40px;
    mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    -webkit-mask-image: radial-gradient(ellipse 100% 100% at 50% 0%, rgba(0,0,0,0.6) 0%, transparent 85%);
    pointer-events: none;
  }
  
  /* Subtle teal glow at top */
  &::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200px;
    background: radial-gradient(ellipse 80% 50% at 50% 0%, rgba(13, 148, 136, 0.03), transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  /* Ensure content is above background */
  > * {
    position: relative;
    z-index: 1;
  }

  .home {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 18px;
    flex: 1;
  }
  .hero {
    font-size: clamp(28px, 4vw, 48px);
    margin: 0;
    text-align: center;
    font-weight: 800;
    background: linear-gradient(135deg, 
      ${({ theme }) => theme.colors.accent} 0%, 
      ${({ theme }) => theme.colors.accent2} 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    line-height: 1.2;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  .heroComposer {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .scroll {
    flex: 1;
    overflow: auto;
    padding: 24px 32px;
    padding-bottom: calc(var(--footer-h, 120px) + 24px);
    background: transparent; /* Let gradient show through */
  }
  .inner {
    max-width: 1000px;
    margin: 0 auto;
  }
  .typing {
    padding: 10px 0;
  }

  .input {
    position: sticky;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px 18px 16px;
    background: transparent;
    border-top: none;
    z-index: 2;
  }
  .disclaimer {
    margin: 2px 0 6px;
    font-size: 11px;
    color: ${({ theme }) => theme.colors.accent};
    text-align: center;
    opacity: 0.5;
    font-weight: 500;
  }

  .jump {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: calc(var(--footer-h, 120px) + 12px);
    width: 40px;
    height: 40px;
    border-radius: 999px;
    border: 1px solid ${({ theme }) => theme.colors.border};
    display: grid;
    place-items: center;
    color: #fff;
    background: linear-gradient(
      90deg,
      ${({ theme }) => theme.colors.accent2},
      ${({ theme }) => theme.colors.accent}
    );
    box-shadow: 0 10px 24px rgba(206, 122, 88, 0.25);
    cursor: pointer;
    transition: filter 0.15s, transform 0.15s;
    z-index: 3;
  }
  .jump:hover {
    filter: brightness(0.96);
  }
  .jump:active {
    transform: translateX(-50%) scale(0.98);
  }

  .scroll::-webkit-scrollbar {
    width: 12px;
  }
  .scroll::-webkit-scrollbar-thumb {
    background: #d0d0d0;
    border-radius: 10px;
    border: 3px solid transparent;
    background-clip: content-box;
  }
  .scroll {
    scrollbar-width: thin;
    scrollbar-color: #d0d0d0 transparent;
  }

  /* Small screens: tighter paddings & fit input */
  @media (max-width: 640px) {
    .home { padding: 16px; gap: 12px; }
    .hero { text-align: center; }
    .desc { font-size: 0.95rem; text-align: center; }

    .content {
      padding: 8px 10px 10px 10px;
    }

    .composer {
      padding: 8px 10px;
    }

    .jump {
      bottom: calc(var(--footer-h) + 12px);
    }
  }`;
