import { NextRequest, NextResponse } from "next/server";

/**
 * Set current chat session in a cookie so the CopilotKit agent proxy can send X-Session-Id.
 * POST body: { sessionId: string }
 */
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const sessionId = typeof body.sessionId === "string" ? body.sessionId : "";
  const res = NextResponse.json({ ok: true });
  if (sessionId) {
    res.cookies.set("copilot_adk_session_id", sessionId, {
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
      sameSite: "lax",
    });
  } else {
    res.cookies.delete("copilot_adk_session_id");
  }
  return res;
}
