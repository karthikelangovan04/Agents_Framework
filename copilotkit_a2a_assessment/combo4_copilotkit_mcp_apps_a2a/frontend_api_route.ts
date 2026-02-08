/**
 * Combo 4: API Route with MCP Apps + ADK Orchestrator Agents
 *
 * This route configures TWO types of agents:
 * 1. BuiltInAgent + MCPAppsMiddleware for MCP App UI rendering (weather, maps, etc.)
 * 2. HttpAgent for the backend ADK orchestrator (shared state, A2A)
 *
 * File: app/api/copilotkit/route.ts
 */

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { MCPAppsMiddleware } from "@ag-ui/mcp-apps-middleware";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest, NextResponse } from "next/server";

const backendUrl = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"
).replace(/\/$/, "");

// MCP App server configurations
const mcpServers = [
  {
    type: "http" as const,
    url: "http://localhost:3006/mcp",
    serverId: "weather-server",
  },
  {
    type: "http" as const,
    url: "http://localhost:3102/mcp",
    serverId: "map-server",
  },
  // Add more MCP App servers as needed
];

const mcpMiddleware = new MCPAppsMiddleware({ mcpServers });

// MCP Apps Agent: handles weather, maps, etc. with UI rendering in chat
// Requires an LLM API key (OpenAI, etc.)
const mcpAppsAgent = new BuiltInAgent({
  model: "openai/gpt-4o",
  prompt: `You are a helpful assistant with access to MCP Apps.
You can:
- Show weather forecasts for any location (use get-forecast tool)
- Display interactive maps (use map tools)
Each tool result will render as an interactive UI widget in the chat.`,
}).use(mcpMiddleware as any);

export async function POST(req: NextRequest) {
  // Check for OpenAI key (needed for MCP Apps BuiltInAgent)
  if (!process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      { error: "OPENAI_API_KEY required for MCP Apps agent" },
      { status: 500 }
    );
  }

  const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId =
    req.cookies.get("copilot_adk_session_id")?.value || "default";

  // ADK Orchestrator Agent: handles shared state, A2A, human-in-loop
  const adkOrchestratorAgent = new HttpAgent({
    url: `${backendUrl}/`,
    headers: {
      "X-User-Id": userId,
      "X-Session-Id": sessionId,
    },
  });

  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      // MCP Apps agent for UI tool rendering
      mcp_apps: mcpAppsAgent,
      // ADK orchestrator for shared state + A2A
      orchestrator: adkOrchestratorAgent,
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
}
