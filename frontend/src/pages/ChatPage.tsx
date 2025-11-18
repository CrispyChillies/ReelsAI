import { useEffect, useLayoutEffect, useRef, useState } from "react";
import styled from "styled-components";
import PromptInput from "@/components/common/chat/PromptInput";
import ChatMessage from "@/components/common/chat/ChatMessage";
import LoaderTyping from "@/components/common/loaders/LoaderTyping";
import FloatingParticles from "@/components/common/FloatingParticles";
import { useI18n } from "@/app/i18n";
// COMMENTED OUT: Backend API calls
// import { me } from "@/services/auth";
// import { startSession, streamChat, getHistory, autoNameSession } from "@/services/sessions";
import { useLocation, useNavigate } from "react-router-dom";

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
  const [sessionId, setSessionId] = useState<string | null>(null);
  // COMMENTED OUT: User auth
  // const [userId, setUserId] = useState<string | null>(null);
  const location = useLocation() as any;
  const nav = useNavigate();

  // COMMENTED OUT: Auth guard - no longer redirecting to signin
  // --- Lấy user id + guard auth: nếu 401 thì về signin (replace:true để tránh quay lại bằng Back)
  // useEffect(() => {
  //   let alive = true;
  //   me()
  //     .then((u) => { if (alive) setUserId(u.id); })
  //     .catch(() => {
  //       try { sessionStorage.removeItem("activeSessionId"); } catch {}
  //       nav("/signin", { replace: true });
  //     });
  //   return () => { alive = false; };
  // }, []);


  // --- Detect "new chat" bằng ?new=1 -> reset
  useEffect(() => {
    const sp = new URLSearchParams(location.search || "");
    if (sp.get("new") === "1") {
      setSessionId(null);
      setMessages([]);
      // cleanup trạng thái active đã lưu
      sessionStorage.removeItem("activeSessionId");
      // bỏ ?new=1 khỏi url (đẹp URL)
      nav(location.pathname, { replace: true });
      // scroll to bottom sau reset
      requestAnimationFrame(() => scrollToBottom(true));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  // COMMENTED OUT: Load history from backend when selecting session
  // --- Nhận sessionId từ location.state khi chọn session
  // useEffect(() => {
  //   const sid = location?.state?.sessionId as string | undefined;
  //   if (sid && sid !== sessionId) {
  //     setSessionId(sid);
  //     sessionStorage.setItem("activeSessionId", sid);
  //     getHistory(sid)
  //       .then(({ messages }) =>
  //         setMessages(
  //           messages.map((m) => ({
  //             id: crypto.randomUUID(),
  //             role: m.role,
  //             content: m.content,
  //           }))
  //         )
  //       )
  //       .catch(() => {});
  //     requestAnimationFrame(() => scrollToBottom(true));
  //   }
  //   // eslint-disable-next-line react-hooks/exhaustive-deps
  // }, [location?.state?.sessionId]);

  // DEMO: Handle session selection from sidebar (just update UI)
  useEffect(() => {
    const sid = location?.state?.sessionId as string | undefined;
    if (sid && sid !== sessionId) {
      setSessionId(sid);
      sessionStorage.setItem("activeSessionId", sid);
      // Clear messages for demo (or you can load from localStorage if you want persistence)
      setMessages([]);
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

  // ---------------------- SEND & STREAM (DEMO MODE - NO BACKEND) ----------------------
  const onSend = async (p: { prompt: string; rootUrl?: string }) => {
    if (!p?.prompt?.trim()) return;
    setTyping(true);

    try {
      // DEMO: Create session ID if needed (client-side only)
      let sid = sessionId;
      if (!sid) {
        // Generate a random session ID for demo
        sid = `demo-session-${crypto.randomUUID()}`;
        setSessionId(sid);
        sessionStorage.setItem("activeSessionId", sid);
        nav(location.pathname, {
          state: { ...location.state, sessionId: sid },
          replace: true,
        });
      }

      // Add user message immediately
      const uid = crypto.randomUUID();
      const aid = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: uid, role: "user", content: p.prompt },
        { id: aid, role: "assistant", content: "" },
      ]);

      // DEMO: Simulate AI response with typing effect (no backend)
      const lowerPrompt = p.prompt.toLowerCase();
      
      // Check if user is asking for TikTok videos
      const isTikTokRequest = 
        lowerPrompt.includes("tiktok") || 
        lowerPrompt.includes("video") ||
        lowerPrompt.includes("recommend") ||
        lowerPrompt.includes("suggest") ||
        lowerPrompt.includes("show") ||
        lowerPrompt.includes("trending") ||
        lowerPrompt.includes("gợi ý") ||
        lowerPrompt.includes("giới thiệu");

      let demoResponse = "";
      
      if (isTikTokRequest) {
        demoResponse = `Hey there! 👋\n\nI found **5 trending TikTok videos** that match your interests. These videos are currently getting lots of love:\n\n✨ **Diverse Content:**\n- Programming & Technology\n- Entertainment & News\n- Food & ASMR\n- Funny moments\n\nYou can:\n- 👁️ **View & Rate** - Swipe through each video like Tinder\n- ❤️ **Like** - Help me recommend better videos\n- 👎 **Dislike** - Skip videos you don't enjoy\n- 💾 **Download** - Save videos to your device\n\nLet me know which ones you like! 😊`;
      } else {
        demoResponse = `Thanks for reaching out! 💬\n\nI'm currently in demo mode and can help you with:\n\n🎬 **Discover trending TikTok videos**\n- Try asking: "Recommend TikTok videos for me"\n- Or: "Show me trending videos"\n- Or: "Any cool videos?"\n\nI'll find the best videos just for you! ✨\n\nWhat kind of videos are you looking for? 🎥`;
      }
      
      let acc = "";
      const words = demoResponse.split(" ");
      
      for (let i = 0; i < words.length; i++) {
        acc += (i > 0 ? " " : "") + words[i];
        setMessages((prev) =>
          prev.map((m) => (m.id === aid ? { ...m, content: acc } : m))
        );
        // Simulate streaming delay
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      // DEMO: Auto-name session (client-side only)
      if (messages.length === 0) {
        const demoTitle = p.prompt.slice(0, 50) + (p.prompt.length > 50 ? "..." : "");
        nav(location.pathname, {
          state: { 
            ...location.state, 
            sessionId: sid,
            title: demoTitle
          },
          replace: true,
        });
      }

      // COMMENTED OUT: Real backend streaming
      // // 1) Tạo session nếu đang new chat
      // let sid = sessionId;
      // if (!sid) {
      //   if (!userId) {
      //     setTyping(false);
      //     return;
      //   }
      //   const s = await startSession();
      //   sid = s.session_id;
      //   setSessionId(sid);
      //   sessionStorage.setItem("activeSessionId", sid);
      //   nav(location.pathname, {
      //     state: { ...location.state, sessionId: sid },
      //     replace: true,
      //   });
      // }

      // // 2) cập nhật UI ngay
      // const uid = crypto.randomUUID();
      // const aid = crypto.randomUUID();
      // setMessages((prev) => [
      //   ...prev,
      //   { id: uid, role: "user", content: p.prompt },
      //   { id: aid, role: "assistant", content: "" },
      // ]);

      // // 3) stream SSE
      // let acc = "";
      // await streamChat(sid!, p.prompt, (token) => {
      //   acc += token;
      //   setMessages((prev) =>
      //     prev.map((m) => (m.id === aid ? { ...m, content: acc } : m))
      //   );
      // });

      // // 4) Auto-name the session if this is the first message
      // if (messages.length === 0) {
      //   try {
      //     const { title } = await autoNameSession(sid!);
      //     nav(location.pathname, {
      //       state: { 
      //         ...location.state, 
      //         sessionId: sid,
      //         title: title
      //       },
      //       replace: true,
      //     });
      //   } catch (e) {
      //     console.error("Failed to auto-name session:", e);
      //   }
      // }
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
