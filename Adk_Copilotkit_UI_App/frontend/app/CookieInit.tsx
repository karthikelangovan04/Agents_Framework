"use client";

import { useEffect } from "react";

/**
 * Without auth we set AG-UI cookies so the API route can send X-User-Id and X-Session-Id.
 * Same cookie names as reference (copilot-adk-app). One session per browser tab/visit.
 */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? match[2] : null;
}

function setCookie(name: string, value: string, maxAge = 60 * 60 * 24 * 7) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${value}; path=/; max-age=${maxAge}; samesite=lax`;
}

function randomId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `sess_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
}

export function CookieInit() {
  useEffect(() => {
    if (!getCookie("copilot_adk_user_id")) {
      setCookie("copilot_adk_user_id", "default");
    }
    if (!getCookie("copilot_adk_session_id")) {
      setCookie("copilot_adk_session_id", randomId());
    }
  }, []);
  return null;
}
