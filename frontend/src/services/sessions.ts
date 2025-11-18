import { api } from "@/utils/http";

export type ChatSession = {
  session_id: string;
  user_id: string;
  title?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  messages_count: number;
};

// UI chỉ làm việc với "user" | "assistant"
export type ChatMessage = { role: "user" | "assistant"; content: string };

// BE có thể trả "human"/"assistant"/"system"/... => chuẩn hoá về "user"/"assistant"
function normalizeRole(raw?: string | null): "user" | "assistant" {
  const r = (raw || "").toLowerCase();
  if (r === "user" || r === "human") return "user";
  return "assistant";
}

export async function listSessions(): Promise<ChatSession[]> {
  const { data } = await api.get("/api/chat/sessions");
  return data;
}

export async function getHistory(
  sessionId: string
): Promise<{ session_id: string; messages: ChatMessage[] }> {
  const { data } = await api.get("/api/chat/history", {
    params: { session_id: sessionId },
  });

  // Chỉ giữ các message hiển thị được (user/human và assistant/ai không có tool_calls)
  const filtered = filterDisplayableMessages(data?.messages || []);

  // Chuẩn hoá role + extract text an toàn từ nhiều cấu trúc content
  const norm: ChatMessage[] = filtered.map((m: any) => ({
    role: normalizeRole(m?.role),
    content: toPlainText(m?.content),
  }));

  return { session_id: data?.session_id, messages: norm };
}

export async function renameSession(
  sessionId: string,
  title: string
): Promise<void> {
  await api.put(`/api/chat/sessions/${encodeURIComponent(sessionId)}/title`, {
    title,
  });
}

export async function autoNameSession(
  sessionId: string
): Promise<{ ok: boolean; session_id: string; title: string }> {
  const { data } = await api.post(`/api/chat/sessions/${encodeURIComponent(sessionId)}/autoname`);
  return data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/api/chat/sessions/${encodeURIComponent(sessionId)}`);
}

export async function startSession(): Promise<{ session_id: string }> {
  const { data } = await api.post("/api/chat/start_session", {});
  return data;
}

/* helpers: lọc message hiển thị & chuẩn hoá content */
/** Lấy text hiển thị từ nhiều kiểu content khác nhau (string / array parts / object). */
function toPlainText(val: any): string {
  if (typeof val === "string") return val;

  if (Array.isArray(val)) {
    // Ví dụ OpenAI "content" là mảng part: [{type:"text", text:"..."}, ...]
    return val.map((p) => toPlainText(p?.text ?? p?.content ?? p)).join("");
  }

  if (val && typeof val === "object") {
    // Một số provider trả { text: "..." } hoặc { content: "..." }
    if (typeof (val as any).text === "string") return (val as any).text;
    if ((val as any).content != null) return toPlainText((val as any).content);
    try {
      // Fallback để không crash nếu backend trả object bất kỳ
      return JSON.stringify(val);
    } catch {
      return String(val);
    }
  }

  return String(val ?? "");
}

/**
 * Chỉ giữ message hiển thị cho UI:
 * - user/human => luôn hiển thị
 * - assistant/ai => chỉ hiển thị khi tool_calls trống (undefined/null/[])
 * - ẩn system/tool và assistant có tool_calls
 * - chặn message rỗng
 */
function filterDisplayableMessages(raw: any[]): any[] {
  return (raw || []).filter((m) => {
    const role = String(m?.role || "").toLowerCase();
    const isUser = role === "user" || role === "human";
    const isAssistant = role === "assistant" || role === "ai";

    const emptyToolCalls =
      !m?.tool_calls ||
      (Array.isArray(m.tool_calls) && m.tool_calls.length === 0);

    const text =
      typeof m?.content === "string"
        ? m.content
        : JSON.stringify(m?.content ?? "");
    const hasText = text.trim().length > 0;

    return (isUser && hasText) || (isAssistant && emptyToolCalls && hasText);
  });
}

/* Networking helpers */

function resolveApiUrl(path: string): string {
  // Lấy baseURL từ axios instance để dùng đúng proxy / host của backend
  const base = (api.defaults?.baseURL as string) || "/api";
  // base có thể là '/api' hoặc 'http://localhost:8000'
  if (/^https?:\/\//i.test(base)) {
    // dạng tuyệt đối -> dùng URL để ghép
    const u = new URL(
      path.replace(/^\//, ""),
      base.endsWith("/") ? base : base + "/"
    );
    return u.toString();
  } else {
    // dạng tương đối -> ghép với window.location.origin (vite proxy xử lý)
    const prefix = base.endsWith("/") ? base.slice(0, -1) : base;
    return `${window.location.origin}${prefix}${
      path.startsWith("/") ? path : `/${path}`
    }`;
  }
}

/**
 * Streaming POST tới /api/chat/ (SSE).
 * Parse SSE chuẩn: mỗi "event" cách nhau bằng \n\n.
 * Với mỗi event, gộp các dòng "data:" lại thành 1 payload; ưu tiên JSON {delta}.
 */
export function streamChat(
  sessionId: string,
  message: string,
  onToken: (token: string) => void
): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      const url = resolveApiUrl("/api/chat/");
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        credentials: "include",
        body: JSON.stringify({ session_id: sessionId, message }),
      });

      if (!res.ok || !res.body) {
        reject(new Error(`HTTP ${res.status}`));
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // Parse SSE: tách event theo \n\n. Mỗi event có thể có nhiều dòng "data:".
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sepIndex: number;
        while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
          const rawEvent = buffer.slice(0, sepIndex);
          buffer = buffer.slice(sepIndex + 2);

          // Gom tất cả các dòng "data:" trong cùng 1 event
          const parts: string[] = [];
          for (const line of rawEvent.split("\n")) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            parts.push(trimmed.slice(5).trim());
          }
          const payload = parts.join("\n");

          if (!payload) continue;

          if (payload === "[DONE]") {
            resolve();
            return;
          }
          if (payload.startsWith("ERROR:")) {
            reject(new Error(payload));
            return;
          }

          // Ưu tiên JSON { delta }, fallback text
          let token = "";
          try {
            const obj = JSON.parse(payload);
            token = obj?.delta ?? "";
          } catch {
            token = payload;
          }
          if (token) onToken(token);
        }
      }

      // Trường hợp server đóng stream mà không gửi [DONE]
      resolve();
    } catch (err) {
      reject(err as any);
    }
  });
}
