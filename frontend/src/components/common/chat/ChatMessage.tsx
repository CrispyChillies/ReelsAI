import styled from "styled-components";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

/* ===================== types ===================== */
export type Msg = {
  id: string;
  role: "user" | "assistant" | "ai";
  content: string;
  metadata?: {
    images?: string[];
    videos?: Array<{ url: string; thumbnail?: string; title?: string }>;
    embedCode?: string;
    embedUrl?: string;
    [key: string]: any;
  };
};

type PreviewData = {
  url: string;
  hostname: string;
  title?: string;
  description?: string;
  icon?: string; // favicon
  image?: string; // screenshot
};

/* ===================== component ===================== */

// ============================================================
// MOCK DATA - COMMENTED OUT FOR PRODUCTION
// TODO: Replace with real API data from backend
// ============================================================
/*
const MOCK_TIKTOK_VIDEOS: TikTokVideo[] = [
  {
    id: "1",
    videoId: "7558395085964971282",
    author: "@codemindx.com",
    url: "https://www.tiktok.com/@codemindx.com/video/7558395085964971282",
    embedHtml: `<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@codemindx.com/video/7558395085964971282" data-video-id="7558395085964971282" style="max-width: 605px;min-width: 325px;" > <section> <a target="_blank" title="@codemindx.com" href="https://www.tiktok.com/@codemindx.com?refer=embed">@codemindx.com</a> Cách mình sử dụng AI trong lập trình coding <a title="laptrinhvien" target="_blank" href="https://www.tiktok.com/tag/laptrinhvien?refer=embed">#laptrinhvien</a> <a title="it" target="_blank" href="https://www.tiktok.com/tag/it?refer=embed">#it</a> <a title="codemindx" target="_blank" href="https://www.tiktok.com/tag/codemindx?refer=embed">#codemindx</a> <a title="developer" target="_blank" href="https://www.tiktok.com/tag/developer?refer=embed">#developer</a> <a title="cntt" target="_blank" href="https://www.tiktok.com/tag/cntt?refer=embed">#cntt</a> <a target="_blank" title="♬ Beat - beaty" href="https://www.tiktok.com/music/Beat-7142169219956738050?refer=embed">♬ Beat - beaty</a> </section> </blockquote>`,
  },
  {
    id: "2",
    videoId: "7545748594473733394",
    author: "@theanh28funfact",
    url: "https://www.tiktok.com/@theanh28funfact/video/7545748594473733394",
    embedHtml: `<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@theanh28funfact/video/7545748594473733394" data-video-id="7545748594473733394" style="max-width: 605px;min-width: 325px;" > <section> <a target="_blank" title="@theanh28funfact" href="https://www.tiktok.com/@theanh28funfact?refer=embed">@theanh28funfact</a> 3 CÔ GÁI ĐÓ TIN TƯỞNG CHÁU QUÁ HA <a title="theanh28" target="_blank" href="https://www.tiktok.com/tag/theanh28?refer=embed">#Theanh28</a> <a title="theanh28funfact" target="_blank" href="https://www.tiktok.com/tag/theanh28funfact?refer=embed">#theanh28funfact</a> <a title="tiktoknews" target="_blank" href="https://www.tiktok.com/tag/tiktoknews?refer=embed">#tiktoknews</a> <a title="theanh28news" target="_blank" href="https://www.tiktok.com/tag/theanh28news?refer=embed">#theanh28news</a> <a target="_blank" title="♬ Take Your Ease Under The Stars - NS Records" href="https://www.tiktok.com/music/Take-Your-Ease-Under-The-Stars-7176165317066885122?refer=embed">♬ Take Your Ease Under The Stars - NS Records</a> </section> </blockquote>`,
  },
  {
    id: "3",
    videoId: "7552834568135527710",
    author: "@yttk0625rg2",
    url: "https://www.tiktok.com/@yttk0625rg2/video/7552834568135527710",
    embedHtml: `<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@yttk0625rg2/video/7552834568135527710" data-video-id="7552834568135527710" style="max-width: 605px;min-width: 325px;" > <section> <a target="_blank" title="@yttk0625rg2" href="https://www.tiktok.com/@yttk0625rg2?refer=embed">@yttk0625rg2</a> <p></p> <a target="_blank" title="♬ original sound - Jessica" href="https://www.tiktok.com/music/original-sound-7552834697965931294?refer=embed">♬ original sound - Jessica</a> </section> </blockquote>`,
  },
  {
    id: "4",
    videoId: "7543233624934501639",
    author: "@bayashi.tiktok",
    url: "https://www.tiktok.com/@bayashi.tiktok/video/7543233624934501639",
    embedHtml: `<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@bayashi.tiktok/video/7543233624934501639" data-video-id="7543233624934501639" style="max-width: 605px;min-width: 325px;" > <section> <a target="_blank" title="@bayashi.tiktok" href="https://www.tiktok.com/@bayashi.tiktok?refer=embed">@bayashi.tiktok</a> <a title="tiktokfood" target="_blank" href="https://www.tiktok.com/tag/tiktokfood?refer=embed">#tiktokfood</a> <a title="asmr" target="_blank" href="https://www.tiktok.com/tag/asmr?refer=embed">#asmr</a> <a target="_blank" title="♬ オリジナル楽曲  - バヤシ🥑Bayashi" href="https://www.tiktok.com/music/オリジナル楽曲-バヤシ🥑Bayashi-7543233706027272961?refer=embed">♬ オリジナル楽曲  - バヤシ🥑Bayashi</a> </section> </blockquote>`,
  },
  {
    id: "5",
    videoId: "7570312514043579656",
    author: "@chankochamdat_",
    url: "https://www.tiktok.com/@chankochamdat_/video/7570312514043579656",
    embedHtml: `<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@chankochamdat_/video/7570312514043579656" data-video-id="7570312514043579656" style="max-width: 605px;min-width: 325px;" > <section> <a target="_blank" title="@chankochamdat_" href="https://www.tiktok.com/@chankochamdat_?refer=embed">@chankochamdat_</a> <a title="giaitri" target="_blank" href="https://www.tiktok.com/tag/giaitri?refer=embed">#giaitri</a> <a title="xhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh" target="_blank" href="https://www.tiktok.com/tag/xhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh?refer=embed">#xhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh</a> <a target="_blank" title="♬ nhạc nền - cậu mèo - hà hững hờ" href="https://www.tiktok.com/music/nhạc-nền-cậu-mèo-7564960557393103633?refer=embed">♬ nhạc nền - cậu mèo - hà hững hờ</a> </section> </blockquote>`,
  },
];
*/
// ============================================================

export default function ChatMessage({
  msg,
  done = true,
}: {
  msg: Msg;
  done?: boolean;
}) {
  const isAssistant = /^(assistant|ai)$/i.test(String(msg.role || ""));
  const raw = String(msg.content ?? "");

  // ---- Hooks theo đúng thứ tự ----
  const steps = useMemo(() => extractSteps(raw), [raw]);
  const contentNoSteps = useMemo(
    () => raw.replace(/<!--\s*steps\s*:\s*\[[\s\S]*?\]\s*-->/i, ""),
    [raw]
  );
  const normalized = useMemo(
    () => contentNoSteps.replace(/\r\n/g, "\n"),
    [contentNoSteps]
  );
  const hiddenAssistant = useMemo(
    () => isAssistant && normalized.trim().length === 0 && !steps,
    [isAssistant, normalized, steps]
  );

  // Link card
  const firstUrl = useMemo(() => findFirstUrl(normalized), [normalized]);
  const showCard = useMemo(
    () => done && !!firstUrl && shouldShowLinkCard(normalized, firstUrl!),
    [done, normalized, firstUrl]
  );

  const mdKey = `md-${msg.id}-${normalized.length}`;
  const [copied, setCopied] = useState(false);

  const copyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(normalized.trim());
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  };

  // ===== Link Preview hover =====
  const mdRef = useRef<HTMLDivElement | null>(null);
  const [preview, setPreview] = useState<{
    show: boolean;
    x: number;
    y: number;
    loading: boolean;
    data: PreviewData | null;
  }>({ show: false, x: 0, y: 0, loading: false, data: null });

  useEffect(() => {
    const root = mdRef.current;
    if (!root) return;

    const anchors = Array.from(
      root.querySelectorAll<HTMLAnchorElement>("a[href^='http']")
    );
    if (!anchors.length) return;

    let fetchTimer: number | null = null;

    const showFor = (a: HTMLAnchorElement) => {
      const rect = a.getBoundingClientRect();
      const pad = 8,
        vw = window.innerWidth,
        vh = window.innerHeight;
      const estW = 360,
        estH = 210;
      let x = rect.left,
        y = rect.bottom + 8;
      if (x + estW + pad > vw) x = Math.max(pad, vw - estW - pad);
      if (y + estH + pad > vh) y = rect.top - estH - 8;
      if (y < pad) y = Math.min(vh - estH - pad, rect.bottom + 8);

      const u = safeURL(a.href);
      const hostname = u ? u.hostname : a.href;
      const icon = u
        ? `https://www.google.com/s2/favicons?domain=${u.hostname}`
        : undefined;

      setPreview({
        show: true,
        x,
        y,
        loading: true,
        data: { url: a.href, hostname, icon },
      });

      if (fetchTimer) window.clearTimeout(fetchTimer);
      fetchTimer = window.setTimeout(async () => {
        const og = await fetchOG(a.href).catch(() => null);
        setPreview((p) => {
          if (!p.show || !p.data) return { ...p, loading: false };
          return {
            ...p,
            loading: false,
            data: {
              url: p.data.url,
              hostname: p.data.hostname,
              title: og?.title ?? p.data.title,
              description: og?.description ?? p.data.description,
              icon: og?.icon ?? p.data.icon,
              image: og?.image ?? p.data.image,
            },
          };
        });
      }, 120);
    };

    const hide = () => {
      if (fetchTimer) window.clearTimeout(fetchTimer);
      setPreview((p) => (p.show ? { ...p, show: false } : p));
    };

    // Gắn trực tiếp vào từng <a>: hover vào hiện, rời là ẩn
    const enterHandlers: Array<
      [
        (e: Event) => void,
        (e: Event) => void,
        (e: Event) => void,
        (e: Event) => void
      ]
    > = [];
    anchors.forEach((a) => {
      const hEnter = () => showFor(a);
      const hLeave = () => hide();
      const hFocus = () => showFor(a);
      const hBlur = () => hide();
      a.addEventListener("mouseenter", hEnter);
      a.addEventListener("mouseleave", hLeave);
      a.addEventListener("focus", hFocus);
      a.addEventListener("blur", hBlur);
      enterHandlers.push([hEnter, hLeave, hFocus, hBlur]);
    });

    // Ẩn khi cuộn / bấm ra ngoài / nhấn Esc / tab mất focus
    const onScroll = hide;
    const onWheel = hide;
    const onPointerDown = (e: PointerEvent) => {
      const el = e.target as HTMLElement | null;
      if (!el?.closest?.(".md a")) hide();
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") hide();
    };
    const onBlur = hide;

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("blur", onBlur);

    return () => {
      anchors.forEach((a, i) => {
        const [hEnter, hLeave, hFocus, hBlur] = enterHandlers[i]!;
        a.removeEventListener("mouseenter", hEnter);
        a.removeEventListener("mouseleave", hLeave);
        a.removeEventListener("focus", hFocus);
        a.removeEventListener("blur", hBlur);
      });
      window.removeEventListener("scroll", onScroll as any);
      window.removeEventListener("wheel", onWheel as any);
      window.removeEventListener("pointerdown", onPointerDown as any);
      window.removeEventListener("keydown", onKeyDown as any);
      window.removeEventListener("blur", onBlur as any);
      if (fetchTimer) window.clearTimeout(fetchTimer);
      setPreview({ show: false, x: 0, y: 0, loading: false, data: null });
    };
  }, [mdKey]);

  // Không override <a> → để toàn bộ hành vi click trái/phải/middle là NATIVE
  if (hiddenAssistant) return null;

  return (
    <>
      <Item className={isAssistant ? "assistant" : "user"}>
        <div className="bubble">
        {isAssistant ? (
          <div className="assistant-inner">
            {!!steps && (
              <>
                <div className="hint">Hướng dẫn từng bước</div>
                <ol className="steps">
                  {steps.map((s, i) => (
                    <li key={i}>
                      <span className="idx">{i + 1}</span>
                      <span className="tx">{s}</span>
                    </li>
                  ))}
                </ol>
              </>
            )}

            {!done ? (
              <pre className="streaming">{normalized}</pre>
            ) : (
              <div className="md" ref={mdRef}>
                <ReactMarkdown
                  key={mdKey}
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                >
                  {normalized}
                </ReactMarkdown>
              </div>
            )}

            {showCard && (
              <div className="linkcard">
                <a href={firstUrl!}>{firstUrl}</a>
              </div>
            )}

            {/* Media Content from API metadata */}
            {done && msg.metadata && (
              <>
                {/* Images */}
                {msg.metadata.images && msg.metadata.images.length > 0 && (
                  <div className="media-images">
                    {msg.metadata.images.map((imgUrl: string, idx: number) => (
                      <img 
                        key={idx} 
                        src={imgUrl} 
                        alt={`Image ${idx + 1}`}
                        loading="lazy"
                      />
                    ))}
                  </div>
                )}

                {/* Videos */}
                {msg.metadata.videos && msg.metadata.videos.length > 0 && (
                  <div className="media-videos">
                    {msg.metadata.videos.map((video: any, idx: number) => (
                      <div key={idx} className="video-item">
                        {video.title && <div className="video-title">{video.title}</div>}
                        <video 
                          controls 
                          poster={video.thumbnail}
                          preload="metadata"
                        >
                          <source src={video.url} />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    ))}
                  </div>
                )}

                {/* Embed Code (e.g., TikTok, YouTube, Twitter) */}
                {msg.metadata.embedCode && (
                  <div 
                    className="media-embed"
                    dangerouslySetInnerHTML={{ __html: msg.metadata.embedCode }}
                  />
                )}

                {/* Embed URL (iframe) */}
                {msg.metadata.embedUrl && (
                  <div className="media-embed">
                    <iframe 
                      src={msg.metadata.embedUrl}
                      title="Embedded content"
                      allowFullScreen
                    />
                  </div>
                )}
              </>
            )}

            {/* TikTok Videos - COMMENTED OUT (MOCK DATA)
            TODO: Replace with real video recommendations from backend API
            {done && <TikTokCarousel videos={MOCK_TIKTOK_VIDEOS} onOpenSwipe={() => setShowSwipeModal(true)} />}
            */}

            <div className="toolbar">
              <button className="tbtn" onClick={copyMarkdown} title="Copy">
                {copied ? "Đã chép" : "Sao chép"}
              </button>
            </div>

            {preview.show && preview.data && (
              <Preview style={{ left: preview.x, top: preview.y }}>
                <div className="row">
                  {preview.data.icon && (
                    <img className="ico" src={preview.data.icon} alt="" />
                  )}
                  <div className="meta">
                    <div className="host">{preview.data.hostname}</div>
                    {preview.loading && (
                      <div className="loading">Đang lấy thông tin…</div>
                    )}
                    {preview.data.title && (
                      <div className="title">{preview.data.title}</div>
                    )}
                    {preview.data.description && (
                      <div className="desc">{preview.data.description}</div>
                    )}
                  </div>
                </div>
                {preview.data.image && (
                  <div className="thumb">
                    <img src={preview.data.image} alt="" />
                  </div>
                )}
              </Preview>
            )}
          </div>
        ) : (
          <span className="user-text">{raw}</span>
        )}
      </div>
      </Item>

      {/* TikTok Swipe Modal - COMMENTED OUT (MOCK DATA)
      TODO: Replace with real video recommendations from backend API
      {isAssistant && (
        <TikTokSwipeModal
          videos={MOCK_TIKTOK_VIDEOS}
          isOpen={showSwipeModal}
          onClose={() => setShowSwipeModal(false)}
        />
      )}
      */}
    </>
  );
}

/* ===================== helpers ===================== */
function extractSteps(raw: string): string[] | null {
  const m = raw.match(/<!--\s*steps\s*:\s*(\[[\s\S]*?\])\s*-->/i);
  if (!m) return null;
  try {
    return JSON.parse(m[1]);
  } catch {
    return null;
  }
}
function findFirstUrl(text: string): string | null {
  const m = text.match(/https?:\/\/[^\s)]+/);
  return m ? m[0].replace(/[)\]]+$/, "") : null;
}
function shouldShowLinkCard(text: string, url: string): boolean {
  if (
    /\[[^\]]+\]\(https?:\/\/[^\s)]+\)/.test(text) ||
    /<https?:\/\/[^>]+>/.test(text)
  )
    return false;
  const urls = text.match(/https?:\/\/[^\s)]+/g) || [];
  if (urls.length !== 1) return false;
  return text.trim() === url || text.trim() === `${url}\n`;
}
function safeURL(href: string): URL | null {
  try {
    return new URL(href);
  } catch {
    return null;
  }
}

/* Lấy Open Graph qua Microlink */
async function fetchOG(url: string): Promise<Partial<PreviewData> | null> {
  try {
    const r = await fetch(
      `https://api.microlink.io?url=${encodeURIComponent(
        url
      )}&screenshot=false`,
      { mode: "cors" }
    );
    const data = await r.json().catch(() => null);
    if (!data || data.status !== "success") return null;
    const d = data.data || {};
    return {
      title: d.title,
      description: d.description,
      icon: d.logo?.url || d.logo,
      image: d.image?.url || d.image,
    };
  } catch {
    return null;
  }
}

/* ===================== styles ===================== */
const Item = styled.div`
  display: flex;
  margin-bottom: 24px;
  justify-content: flex-start;
  
  &:first-child {
    margin-top: 8px;
  }
  
  &:last-child {
    margin-bottom: 8px;
  }
  
  &.user {
    justify-content: flex-end;
  }

  .bubble {
    position: relative;
    max-width: min(800px, 90%);
    padding: 18px 22px;
    border-radius: 16px;
    background: ${({ theme }) => theme.colors.surface};
    border: 1px solid rgba(13, 148, 136, 0.12);
    color: ${({ theme }) => theme.colors.primary};
    line-height: 1.7;
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.06), 
                0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease,
      border-color 0.2s ease;
    word-break: break-word;
    overflow-wrap: anywhere;
  }

  &.assistant .bubble {
    background: linear-gradient(135deg, 
      rgba(240, 253, 250, 0.7) 0%,
      rgba(255, 255, 255, 0.9) 100%
    );
    border-color: rgba(13, 148, 136, 0.12);
  }
  
  &.assistant .bubble:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(13, 148, 136, 0.12), 
                0 2px 6px rgba(0, 0, 0, 0.06);
    border-color: rgba(13, 148, 136, 0.2);
  }
  
  &.user .bubble {
    background: linear-gradient(135deg, 
      rgba(13, 148, 136, 0.85) 0%,
      rgba(20, 184, 166, 0.9) 100%
    );
    border: 1.5px solid rgba(13, 148, 136, 0.4);
    color: white;
    box-shadow: 0 3px 12px rgba(13, 148, 136, 0.25),
                0 1px 6px rgba(0, 0, 0, 0.08);
  }
  
  &.user .bubble:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(13, 148, 136, 0.35),
                0 3px 10px rgba(0, 0, 0, 0.12);
    border-color: rgba(13, 148, 136, 0.6);
  }

  .assistant-inner .hint {
    font-size: 0.92rem;
    color: ${({ theme }) => theme.colors.secondary};
    margin-bottom: 8px;
    letter-spacing: 0.2px;
  }
  .steps {
    list-style: none;
    padding: 0;
    margin: 8px 0 12px;
    display: grid;
    gap: 8px;
  }
  .steps li {
    display: grid;
    grid-template-columns: 24px 1fr;
    gap: 10px;
    align-items: flex-start;
    padding: 8px 10px;
    background: ${({ theme }) => theme.colors.surface2};
    border: 1px dashed ${({ theme }) => theme.colors.border};
    border-radius: ${({ theme }) => theme.radii.md};
  }
  .steps .idx {
    display: inline-grid;
    place-items: center;
    width: 24px;
    height: 24px;
    border-radius: 999px;
    background: ${({ theme }) => theme.colors.accent2};
    color: #fff;
    font-size: 0.85rem;
    font-weight: 700;
  }
  .steps .tx {
    flex: 1;
  }

  .md {
    font-size: 1rem;
  }
  .md :is(p, ul, ol, blockquote, pre, table) {
    margin: 0.55rem 0;
  }
  .md ul,
  .md ol {
    padding-left: 1.25rem;
  }
  .md :is(p, li, td, th) {
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .md a {
    color: ${({ theme }) => theme.colors.accent2};
    text-decoration: none;
    border-bottom: 1px dashed currentColor;
    cursor: pointer;
    position: relative;
    z-index: 1;
  }
  .md a:hover {
    opacity: 0.9;
  }
  .md code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
      "Liberation Mono", "Courier New", monospace;
    background: ${({ theme }) => theme.colors.surface2};
    border: 1px solid ${({ theme }) => theme.colors.border};
    border-radius: 8px;
    padding: 0.18rem 0.4rem;
    font-size: 0.92em;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .md pre {
    max-width: 100%;
    overflow: auto;
  }
  .md pre code {
    display: block;
    padding: 0.9rem;
    border-radius: ${({ theme }) => theme.radii.md};
  }
  .md h1,
  .md h2,
  .md h3 {
    line-height: 1.25;
    margin: 0.9rem 0 0.5rem;
    color: ${({ theme }) => theme.colors.accent2};
  }
  .md table {
    width: 100%;
    border-collapse: collapse;
    overflow: hidden;
    border-radius: ${({ theme }) => theme.radii.md};
  }
  .md th,
  .md td {
    border: 1px solid ${({ theme }) => theme.colors.border};
    padding: 0.45rem 0.6rem;
  }
  .md th {
    background: ${({ theme }) => theme.colors.surface2};
    text-align: left;
  }

  .streaming {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
    margin: 0.45rem 0;
    background: transparent;
    border: 0;
    padding: 0;
    font: inherit;
    color: ${({ theme }) => theme.colors.secondary};
  }

  .linkcard {
    padding: 12px 14px;
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface};
    border-radius: ${({ theme }) => theme.radii.md};
    margin: 10px 0 4px;
    display: flex;
    align-items: center;
    gap: 10px;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .linkcard a {
    color: ${({ theme }) => theme.colors.accent2};
    font-weight: 600;
  }

  .media-images {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin: 12px 0;
  }

  .media-images img {
    width: 100%;
    height: auto;
    border-radius: ${({ theme }) => theme.radii.md};
    border: 1px solid ${({ theme }) => theme.colors.border};
    object-fit: cover;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .media-images img:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .media-videos {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin: 12px 0;
  }

  .video-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .video-title {
    font-size: 14px;
    font-weight: 600;
    color: ${({ theme }) => theme.colors.primary};
  }

  .media-videos video {
    width: 100%;
    max-width: 600px;
    border-radius: ${({ theme }) => theme.radii.md};
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: #000;
  }

  .media-embed {
    margin: 12px 0;
    border-radius: ${({ theme }) => theme.radii.md};
    overflow: hidden;
    border: 1px solid ${({ theme }) => theme.colors.border};
  }

  .media-embed iframe {
    width: 100%;
    min-height: 400px;
    border: none;
    display: block;
  }

  .media-embed blockquote {
    margin: 0 !important;
  }

  .toolbar {
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
    gap: 6px;
  }
  .tbtn {
    height: 26px;
    padding: 0 10px;
    border-radius: 999px;
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface2};
    color: ${({ theme }) => theme.colors.secondary};
    font-size: 12px;
    cursor: pointer;
    transition: all 0.12s ease;
  }
  .tbtn:hover {
    color: ${({ theme }) => theme.colors.accent};
    border-color: ${({ theme }) => theme.colors.accent};
    background: ${({ theme }) => `${theme.colors.accent}20`};
  }

  .user-text {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
`;

/* Tooltip preview */
const Preview = styled.div`
  position: fixed;
  left: 0;
  top: 0;
  z-index: 9999;
  pointer-events: none;

  min-width: 280px;
  max-width: 380px;
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  box-shadow: ${({ theme }) => theme.shadow};
  border-radius: ${({ theme }) => theme.radii.md};
  padding: 10px 12px;
  animation: fadeIn 0.12s ease-out;
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-2px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .row {
    display: grid;
    grid-template-columns: 20px 1fr;
    gap: 10px;
  }
  .ico {
    width: 20px;
    height: 20px;
    border-radius: 4px;
  }
  .meta {
    min-width: 0;
  }
  .host {
    font-size: 12px;
    color: ${({ theme }) => theme.colors.secondary};
    margin-bottom: 2px;
  }
  .loading {
    font-size: 12px;
    color: ${({ theme }) => theme.colors.secondary};
  }
  .title {
    font-weight: 700;
    color: ${({ theme }) => theme.colors.primary};
    overflow-wrap: anywhere;
  }
  .desc {
    font-size: 13px;
    color: ${({ theme }) => theme.colors.secondary};
    margin-top: 4px;
    overflow-wrap: anywhere;
  }

  .thumb {
    margin-top: 8px;
    overflow: hidden;
    border-radius: ${({ theme }) => theme.radii.sm};
  }
  .thumb img {
    width: 100%;
    display: block;
  }
`;
