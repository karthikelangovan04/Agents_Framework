# Frontend CopilotKit Package Listing

**File path**: `frontend_copilotkit_docs/06-Package-Listing-CopilotKit.md`

**Source**: Reference app `Adk_Copilotkit_UI_App/frontend` (read-only). Versions from installed `node_modules` at assessment time.

---

## Summary

| Package | Version (installed) | In app package.json | Role in reference app |
|---------|---------------------|----------------------|------------------------|
| @copilotkit/runtime | 1.51.3 | ^1.51.0 | CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint in API route |
| @copilotkit/react-core | 1.51.3 | ^1.51.0 | CopilotKit, useCoAgent, useCopilotChat |
| @copilotkit/react-ui | 1.51.3 | ^1.51.0 | CopilotSidebar, styles.css |
| @copilotkit/runtime-client-gql | 1.51.3 | (transitive) | TextMessage, MessageRole in deal page |
| @ag-ui/client | 0.0.44 | ^0.0.44 | HttpAgent in API route |

---

## @copilotkit/runtime

- **Version**: 1.51.3  
- **Entry**: `./dist/index.js` (main), `./dist/index.mjs` (module), `./dist/index.d.ts` (types)  
- **Exports**: `.`, `./v2`, `./langgraph`  
- **Used in reference app**: CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint  
- **Also provides**: Service adapters (OpenAI, Anthropic, LangChain, etc.), message/event types, other framework endpoints (Pages Router, Node, Express, Nest)

---

## @copilotkit/react-core

- **Version**: 1.51.3  
- **Entry**: `./dist/index.js`, `./dist/index.mjs`, `./dist/index.d.ts`  
- **Exports**: `.`, `./v2`, `./v2/styles.css`  
- **Used in reference app**: CopilotKit, useCoAgent, useCopilotChat  
- **Also provides**: useCopilotAction, useCopilotReadable, useCopilotContext, useThreads, CopilotMessagesContext, types for actions/context

---

## @copilotkit/react-ui

- **Version**: 1.51.3  
- **Entry**: `./dist/index.js`, `./dist/index.mjs`, `./dist/index.d.ts`  
- **Exports**: `.`, `./styles.css`, `./v2/styles.css`  
- **Used in reference app**: CopilotSidebar, `@copilotkit/react-ui/styles.css`  
- **Also provides**: CopilotPopup, CopilotChat, Markdown, AssistantMessage, UserMessage, Suggestions, CopilotDevConsole, hooks (useChatContext, useCopilotChatSuggestions)

---

## @copilotkit/runtime-client-gql

- **Version**: 1.51.3  
- **Dependency of**: @copilotkit/react-core (and react-ui)  
- **Used in reference app**: TextMessage, MessageRole (in deal page for appendMessage)  
- **Also provides**: CopilotRuntimeClient, message conversion (GQL ↔ AG-UI), other message types (ActionExecutionMessage, AgentStateMessage, ResultMessage, etc.)

---

## @ag-ui/client

- **Version**: 0.0.44  
- **Entry**: `./dist/index.js`, `./dist/index.mjs`, `./dist/index.d.ts`  
- **Used in reference app**: HttpAgent (url, headers) in API route  
- **Also provides**: AbstractAgent, RunAgentParameters, middleware, event parsing (SSE, proto), re-exports from @ag-ui/core

---

## Transitive @ag-ui packages (present in node_modules)

| Package | Version | Used by |
|---------|---------|--------|
| @ag-ui/core | 0.0.44 | @ag-ui/client |
| @ag-ui/encoder | 0.0.44 | @ag-ui/client |
| @ag-ui/proto | 0.0.44 | @ag-ui/client |
| @ag-ui/langgraph | 0.0.23 | @copilotkit/runtime (optional) |

The reference app does not import these directly.

---

## Regenerating the listing

From repo root:

```bash
node frontend_copilotkit_docs/explore_copilotkit_packages.js
```

Output is JSON. See [How-to-Run-Exploration-Scripts.md](How-to-Run-Exploration-Scripts.md).
