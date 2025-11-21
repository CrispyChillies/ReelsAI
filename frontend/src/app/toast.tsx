import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import styled, { keyframes } from "styled-components";
import { Info, AlertTriangle, XCircle, CheckCircle2 } from "lucide-react";

type Tone = "info" | "warn" | "error" | "success";
type Toast = {
  id: string;
  title: string;
  content?: unknown;
  linkText?: string;
  linkHref?: string;
  tone?: Tone;
};
type ToastCtx = {
  notify: (t: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
};
const Ctx = createContext<ToastCtx>({ notify: () => {}, dismiss: () => {} });

export const useToast = () => useContext(Ctx);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const dismiss = useCallback(
    (id: string) => setToasts((prev) => prev.filter((x) => x.id !== id)),
    []
  );
  const notify = useCallback((t: Omit<Toast, "id">) => {
    const id =
      (crypto as any)?.randomUUID?.() || String(Date.now() + Math.random());
    setToasts((prev) => [...prev, { id, ...t }]);
  }, []);

  return (
    <Ctx.Provider value={{ notify, dismiss }}>
      {children}
      <Wrap role="region" aria-live="polite" aria-atomic="false">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
        ))}
      </Wrap>
    </Ctx.Provider>
  );
};

const toStringSafe = (v: unknown): string =>
  typeof v === "string"
    ? v
    : (() => {
        try {
          return JSON.stringify(v);
        } catch {
          return String(v);
        }
      })();

/* ================= item ================= */
const ToastItem: React.FC<{ toast: Toast; onDismiss: () => void }> = ({
  toast,
  onDismiss,
}) => {
  const tone: Tone = toast.tone ?? "info";
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    // Show errors longer (10s), others 6s
    const duration = tone === "error" ? 10000 : 6000;
    const t = setTimeout(() => {
      setLeaving(true);
      setTimeout(onDismiss, 320);
    }, duration);
    return () => clearTimeout(t);
  }, [onDismiss, tone]);

  const ToneIcon =
    tone === "success"
      ? CheckCircle2
      : tone === "error"
      ? XCircle
      : tone === "warn"
      ? AlertTriangle
      : Info;

  return (
    <Item tone={tone}>
      <Card data-leaving={leaving ? "true" : "false"}>
        <button
          className="exit-btn"
          onClick={() => {
            setLeaving(true);
            setTimeout(onDismiss, 320);
          }}
          aria-label="Close"
        >
          <svg
            fill="none"
            viewBox="0 0 15 15"
            height={15}
            width={15}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeWidth={2}
              stroke="currentColor"
              d="M1 14L14 1"
            />
            <path
              strokeLinecap="round"
              strokeWidth={2}
              stroke="currentColor"
              d="M1 1L14 14"
            />
          </svg>
        </button>

        <div className="row">
          <span className="tone">
            <ToneIcon size={18} strokeWidth={2.5} />
          </span>
          <div className="text">
            <p className="heading">{toast.title}</p>
            {toast.content != null && (
              <p className="content">{toStringSafe(toast.content)}</p>
            )}
            {!!toast.linkText && (
              <a href={toast.linkHref ?? "#"} className="link">
                {toast.linkText}
              </a>
            )}
          </div>
        </div>
      </Card>
    </Item>
  );
};

/* ================= styles ================= */
const slideIn = keyframes`from{transform:translateX(16px);opacity:0}to{transform:translateX(0);opacity:1}`;
const slideOut = keyframes`from{transform:translateX(0);opacity:1}to{transform:translateX(16px);opacity:0}`;

const PAD = 5,
  HOVER = 10;

const Wrap = styled.div`
  position: fixed;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 9999;
  pointer-events: none;
  padding-right: ${HOVER + PAD}px;
  padding-bottom: ${HOVER + PAD}px;
`;

const Item = styled.div<{ tone: Tone }>`
  position: relative;
  display: inline-block;
  pointer-events: auto;

  --tone: ${({ tone, theme }) => {
    switch (tone) {
      case "success":
        return theme.colors.success;
      case "error":
        return theme.colors.danger;
      case "warn":
        return "color-mix(in srgb, #ffb700 80%, #fff)";
      default:
        return theme.colors.accent;
    }
  }};
  --tone-soft: color-mix(in srgb, var(--tone) 18%, #fff);

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--tone-soft);
    box-shadow: 0 10px 26px color-mix(in srgb, var(--tone) 20%, transparent);
    z-index: -1;
    padding: ${PAD}px;
    margin: -${PAD}px;
    transform: translate(0, 0);
    transition: transform 0.3s ease;
    border-radius: 14px;
  }
  &:hover::before {
    transform: translate(-${HOVER}px, ${HOVER}px);
  }
`;

const Card = styled.div`
  position: relative;
  z-index: 0;
  width: 360px;
  border-radius: 14px;
  overflow: hidden;
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  box-shadow: ${({ theme }) => theme.shadow};
  backdrop-filter: blur(6px);
  animation: ${slideIn} 260ms ease-out both;
  &[data-leaving="true"] {
    animation: ${slideOut} 260ms ease-in both;
  }

  .row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 40px 12px 12px;
  }
  .tone {
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 999px;
    background: var(--tone-soft);
    color: var(--tone);
    border: 1px solid color-mix(in srgb, var(--tone) 30%, #fff);
  }
  .text {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .heading {
    font-size: 0.98rem;
    font-weight: 800;
    color: ${({ theme }) => theme.colors.primary};
  }
  .content {
    font-size: 0.94rem;
    font-weight: 500;
    color: ${({ theme }) => theme.colors.secondary};
    white-space: pre-line;
    word-break: break-word;
  } /* ← hiển thị xuống dòng */
  .link {
    margin-top: 2px;
    color: ${({ theme }) => theme.colors.accent};
    font-weight: 700;
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .exit-btn {
    position: absolute;
    right: 6px;
    top: 6px;
    width: 28px;
    height: 28px;
    display: grid;
    place-items: center;
    border: none;
    background: transparent;
    border-radius: 8px;
    color: ${({ theme }) => theme.colors.secondary};
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
  }
  .exit-btn:hover {
    background: var(--tone-soft);
    color: ${({ theme }) => theme.colors.primary};
  }
`;
