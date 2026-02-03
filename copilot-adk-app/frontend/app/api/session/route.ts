import { NextRequest, NextResponse } from "next/server";

/**
 * Set current user and session cookies for AG-UI
 * POST body: { user_id?: number, session_id?: string }
 */
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const userId = body.user_id;
  const sessionId = body.session_id;
  
  const res = NextResponse.json({ ok: true });
  
  // Set user_id cookie (required for AG-UI)
  if (userId) {
    res.cookies.set("copilot_adk_user_id", String(userId), {
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      sameSite: "lax",
    });
  }
  
  // Set session_id cookie
  if (sessionId) {
    res.cookies.set("copilot_adk_session_id", sessionId, {
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      sameSite: "lax",
    });
  } else {
    // If no session, clear it
    res.cookies.delete("copilot_adk_session_id");
  }
  
  return res;
}
