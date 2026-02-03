import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function POST(req: NextRequest) {
  const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

  console.log(`🔌 CopilotKit API: userId=${userId}, sessionId=${sessionId?.slice(0, 8)}...`);
  console.log(`🍪 Cookies received:`, req.cookies.getAll().map(c => `${c.name}=${c.value.slice(0, 20)}`));

  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      my_agent: new HttpAgent({
        url: `${backendUrl}/ag-ui`,
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
