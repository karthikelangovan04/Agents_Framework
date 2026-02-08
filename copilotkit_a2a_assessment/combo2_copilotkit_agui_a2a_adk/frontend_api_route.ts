/**
 * Combo 2: Next.js API Route for CopilotKit → AG-UI → A2A → ADK
 *
 * This is the middleware between CopilotKit frontend and the backend orchestrator.
 * It creates HttpAgent pointing to the backend AG-UI endpoint.
 *
 * File: app/api/copilotkit/route.ts
 */

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const backendUrl = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"
).replace(/\/$/, "");

export async function POST(req: NextRequest) {
  const userId =
    req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId =
    req.cookies.get("copilot_adk_session_id")?.value || "default";

  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      // Single orchestrator agent that internally uses A2A to reach remote agents
      orchestrator: new HttpAgent({
        url: `${backendUrl}/`,
        headers: {
          "X-User-Id": userId,
          "X-Session-Id": sessionId,
        },
      }),
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
}
