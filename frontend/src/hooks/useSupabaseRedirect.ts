import { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { exchangeSession } from "@/services/auth";
import { useToast } from "@/app/toast";

function parseSupabaseParams() {
  const url = new URL(window.location.href);

  const hashParams = new URLSearchParams(
    (window.location.hash || "").replace(/^#/, "")
  );
  const queryParams = url.searchParams;

  const get = (key: string) =>
    hashParams.get(key) || queryParams.get(key) || null;

  const access = get("access_token") || "";
  const refresh = get("refresh_token") || undefined;
  const type = (get("type") || "").toLowerCase(); // "signup" | "recovery" | ""
  const error = get("error");
  const errorDescription = get("error_description");

  return { access, refresh, type, error, errorDescription };
}

/* Dọn URL: xóa hash & query, giữ lại pathname hiện tại */
function cleanUrl() {
  const clean = window.location.pathname;
  window.history.replaceState(null, "", clean);
}

/* Hook xử lý redirect từ email Supabase (signup verify / recovery) */
export default function useSupabaseRedirect() {
  const once = useRef(false);
  const nav = useNavigate();
  const { pathname } = useLocation();
  const { notify } = useToast();

  useEffect(() => {
    if (once.current) return;
    once.current = true;

    const { access, refresh, type, error, errorDescription } =
      parseSupabaseParams();

    // Nếu Supabase trả lỗi qua URL
    if (error || errorDescription) {
      notify({
        title: "Lỗi",
        content: errorDescription || error || "Auth error",
        tone: "error",
      });
      // Không dọn URL để thấy lỗi cần debug
      return;
    }

    // Không có token -> không làm gì
    if (!access) return;

    (async () => {
      try {
        // Đổi token sang cookie HttpOnly ở backend
        await exchangeSession(access, refresh);

        // Xoá hash & query để tránh lặp lại khi refresh
        cleanUrl();

        // Thông báo và điều hướng hợp lý
        if (type === "recovery") {
          notify({ title: "Xác thực khôi phục OK", tone: "success" });
          if (pathname !== "/reset") nav("/reset");
        } else {
          // signup / email verify / unknown
          notify({ title: "Xác minh email OK", tone: "success" });
          if (pathname !== "/app") nav("/app");
        }
      } catch (e: any) {
        // Không dọn URL khi lỗi để thấy token trong lúc debug
        notify({
          title: "Lỗi",
          content:
            e?.response?.data?.detail ||
            e?.message ||
            "Exchange session failed",
          tone: "error",
        });
      }
    })();
  }, []);
}
