/**
 * CopilotKit API route: proxies to backend AG-UI endpoints.
 * Cookie names match reference (copilot-adk-app) for consistent wiring.
 * Without auth we use defaults; frontend can set cookies for stable user/session.
 */
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");

export async function POST(req: NextRequest) {
  // Same cookie names as reference: copilot_adk_user_id, copilot_adk_session_id
  const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      deal_builder: new HttpAgent({
        url: `${backendUrl}/ag-ui/deal_builder`,
        headers: {
          "X-User-Id": userId,
          "X-Session-Id": sessionId,
        },
      }),
      knowledge_qa: new HttpAgent({
        url: `${backendUrl}/ag-ui/knowledge_qa`,
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
