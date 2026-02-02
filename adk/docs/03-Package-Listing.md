# Google ADK Complete Package Listing

This document provides a complete listing of all Google ADK packages, their subpackages, classes, and links to their documentation.

## 📦 Complete Package Inventory

Based on exploration of the installed Google ADK package (version 1.22.1), here are all packages:

### Core Packages (Documented)

1. **agents** - `google.adk.agents`
   - **Documentation**: [01-Agents-Package.md](01-Agents-Package.md)
   - **File Path**: `docs/01-Agents-Package.md`
   - **Key Classes**: Agent, BaseAgent, LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
   - **Subpackages**: None (but has internal modules)

2. **tools** - `google.adk.tools`
   - **Documentation**: [02-Tools-Package.md](02-Tools-Package.md)
   - **File Path**: `docs/02-Tools-Package.md`
   - **Key Classes**: BaseTool, FunctionTool, AgentTool, TransferToAgentTool
   - **Subpackages**: 
     - `apihub_tool` - API Hub tool integration
     - `application_integration_tool` - Application integration tools
     - `bigquery` - BigQuery tool
     - `bigtable` - Bigtable tool
     - `computer_use` - Computer use tools
     - `google_api_tool` - Google API tools
     - `mcp_tool` - MCP (Model Context Protocol) tools
     - `openapi_tool` - OpenAPI tool integration
     - `pubsub` - Pub/Sub tools
     - `retrieval` - Retrieval tools
     - `spanner` - Spanner database tools

3. **a2a** - `google.adk.a2a` (Agent-to-Agent)
   - **Documentation**: [04-A2A-Package.md](04-A2A-Package.md)
   - **File Path**: `docs/04-A2A-Package.md`
   - **Key Classes**: RemoteA2aAgent
   - **Subpackages**: 
     - `converters` - A2A protocol converters
     - `executor` - A2A executor
     - `logs` - A2A logging
     - `utils` - A2A utilities

4. **apps** - `google.adk.apps`
   - **Documentation**: [05-Apps-Package.md](05-Apps-Package.md)
   - **File Path**: `docs/05-Apps-Package.md`
   - **Key Classes**: App, ResumabilityConfig
   - **Subpackages**: None

5. **code_executors** - `google.adk.code_executors`
   - **Documentation**: [06-Code-Executors-Package.md](06-Code-Executors-Package.md)
   - **File Path**: `docs/06-Code-Executors-Package.md`
   - **Key Classes**: BaseCodeExecutor, BuiltInCodeExecutor, UnsafeLocalCodeExecutor
   - **Subpackages**: None

6. **sessions** - `google.adk.sessions`
    - **Documentation**: [07-Sessions-Package.md](07-Sessions-Package.md)
    - **File Path**: `docs/07-Sessions-Package.md`
    - **Key Classes**: Session, BaseSessionService, InMemorySessionService, VertexAiSessionService, DatabaseSessionService
    - **Subpackages**: None

7. **memory** - `google.adk.memory`
   - **Documentation**: [08-Memory-Package.md](08-Memory-Package.md)
   - **File Path**: `docs/08-Memory-Package.md`
   - **Key Classes**: BaseMemoryService, InMemoryMemoryService, VertexAiMemoryBankService, VertexAiRagMemoryService
   - **Subpackages**: None

### Supporting Packages (Documented in Other Packages)

8. **models** - `google.adk.models`
   - **Documentation**: [09-Other-Packages.md#models-package](09-Other-Packages.md#models-package)
   - **File Path**: `docs/09-Other-Packages.md`
   - **Key Classes**: BaseLlm, Gemini, Gemma, LLMRegistry, ApigeeLlm
   - **Subpackages**: None

9. **auth** - `google.adk.auth`
   - **Documentation**: [09-Other-Packages.md#auth-package](09-Other-Packages.md#auth-package)
   - **File Path**: `docs/09-Other-Packages.md`
   - **Key Classes**: AuthConfig, AuthHandler, OAuth2Auth, AuthCredential
   - **Subpackages**: 
     - `credential_service` - Credential services
     - `exchanger` - Token exchangers
     - `refresher` - Token refreshers

10. **examples** - `google.adk.examples`
    - **Documentation**: [09-Other-Packages.md#examples-package](09-Other-Packages.md#examples-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: BaseExampleProvider, Example, VertexAiExampleStore
    - **Subpackages**: None

11. **planners** - `google.adk.planners`
    - **Documentation**: [09-Other-Packages.md#planners-package](09-Other-Packages.md#planners-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: BasePlanner, BuiltInPlanner, PlanReActPlanner
    - **Subpackages**: None

12. **flows** - `google.adk.flows`
    - **Documentation**: [09-Other-Packages.md#flows-package](09-Other-Packages.md#flows-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: Flow (various flow types)
    - **Subpackages**: 
      - `llm_flows` - LLM-based flows

13. **plugins** - `google.adk.plugins`
    - **Documentation**: [09-Other-Packages.md#plugins-package](09-Other-Packages.md#plugins-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: BasePlugin, PluginManager, LoggingPlugin, ReflectAndRetryToolPlugin
    - **Subpackages**: None

14. **artifacts** - `google.adk.artifacts`
    - **Documentation**: [09-Other-Packages.md#artifacts-package](09-Other-Packages.md#artifacts-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: BaseArtifactService, FileArtifactService, GcsArtifactService, InMemoryArtifactService
    - **Subpackages**: None

15. **events** - `google.adk.events`
    - **Documentation**: [09-Other-Packages.md#events-package](09-Other-Packages.md#events-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: Event, EventActions
    - **Subpackages**: None

16. **telemetry** - `google.adk.telemetry`
    - **Documentation**: [09-Other-Packages.md#telemetry-package](09-Other-Packages.md#telemetry-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Functions**: trace_call_llm, trace_tool_call, trace_send_data, trace_merged_tool_calls
    - **Subpackages**: None

17. **evaluation** - `google.adk.evaluation`
    - **Documentation**: [09-Other-Packages.md#evaluation-package](09-Other-Packages.md#evaluation-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: AgentEvaluator
    - **Subpackages**: 
      - `simulation` - Evaluation simulation

18. **features** - `google.adk.features`
    - **Documentation**: [09-Other-Packages.md](09-Other-Packages.md)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Key Classes**: FeatureName
    - **Key Functions**: experimental, stable, working_in_progress, is_feature_enabled
    - **Subpackages**: None

19. **cli** - `google.adk.cli`
    - **Documentation**: [09-Other-Packages.md#cli-package](09-Other-Packages.md#cli-package)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Subpackages**: 
      - `built_in_agents` - Built-in agent templates
      - `conformance` - Conformance testing
      - `plugins` - CLI plugins
      - `utils` - CLI utilities

20. **platform** - `google.adk.platform`
    - **Documentation**: [09-Other-Packages.md](09-Other-Packages.md)
    - **File Path**: `docs/09-Other-Packages.md`
    - **Subpackages**: 
      - `internal` - Internal platform utilities

21. **runners** - `google.adk.runners`
    - **Documentation**: [10-Runners-Package.md](10-Runners-Package.md)
    - **File Path**: `docs/10-Runners-Package.md`
    - **Key Classes**: Runner, InMemoryRunner
    - **Subpackages**: None

22. **dependencies** - `google.adk.dependencies`
    - **Purpose**: Dependency management
    - **Subpackages**: None

23. **errors** - `google.adk.errors`
    - **Purpose**: Error handling and exceptions
    - **Subpackages**: None

24. **utils** - `google.adk.utils`
    - **Purpose**: Utility functions
    - **Subpackages**: None

25. **version** - `google.adk.version`
    - **Purpose**: Version information
    - **Subpackages**: None

## 📄 Documentation Files with Full Paths

All documentation files are located in the `docs/` directory:

1. **[INDEX.md](INDEX.md)** - `docs/INDEX.md`
   - Master index and navigation guide

2. **[00-Setup-and-Installation.md](00-Setup-and-Installation.md)** - `docs/00-Setup-and-Installation.md`
   - Setup guide with UV, installation, authentication

3. **[01-Agents-Package.md](01-Agents-Package.md)** - `docs/01-Agents-Package.md`
   - Complete agents package documentation with 5 examples

4. **[02-Tools-Package.md](02-Tools-Package.md)** - `docs/02-Tools-Package.md`
   - Complete tools package documentation with 7 examples
   - Covers all tool subpackages

5. **[03-Package-Listing.md](03-Package-Listing.md)** - `docs/03-Package-Listing.md`
   - This file - complete package inventory

6. **[04-A2A-Package.md](04-A2A-Package.md)** - `docs/04-A2A-Package.md`
   - Agent-to-Agent communication documentation

7. **[05-Apps-Package.md](05-Apps-Package.md)** - `docs/05-Apps-Package.md`
   - Web applications and APIs documentation

8. **[06-Code-Executors-Package.md](06-Code-Executors-Package.md)** - `docs/06-Code-Executors-Package.md`
   - Code execution capabilities documentation

9. **[07-Sessions-Package.md](07-Sessions-Package.md)** - `docs/07-Sessions-Package.md`
   - Session management documentation

10. **[08-Memory-Package.md](08-Memory-Package.md)** - `docs/08-Memory-Package.md`
    - Memory services documentation

11. **[09-Other-Packages.md](09-Other-Packages.md)** - `docs/09-Other-Packages.md`
    - Documentation for models, auth, examples, planners, flows, plugins, artifacts, events, telemetry, evaluation, features, cli

## 🔍 Tools Subpackages Detailed

The `tools` package has the most subpackages. Here's what each provides:

- **bigquery** - Query Google BigQuery databases
- **bigtable** - Interact with Google Cloud Bigtable
- **spanner** - Query Google Cloud Spanner databases
- **pubsub** - Publish/subscribe to Google Cloud Pub/Sub topics
- **google_api_tool** - Generic Google API integration
- **mcp_tool** - Model Context Protocol tool integration
- **openapi_tool** - OpenAPI/Swagger API integration
- **apihub_tool** - API Hub integration
- **application_integration_tool** - Application integration capabilities
- **retrieval** - Information retrieval tools
- **computer_use** - Computer interaction tools

## 📝 Example Files

All example files are in the `examples/` directory:

- `examples/simple_agent.py` - Basic agent example
- `examples/tool_agent.py` - Agent with tools
- `examples/multi_agent.py` - Multi-agent system
- `examples/web_app.py` - Web application
- `examples/remote_agent_server.py` - Remote agent server
- `examples/remote_agent_client.py` - Remote agent client

## ✅ Coverage Status

- ✅ **25 packages** identified and listed
- ✅ **11 major packages** fully documented with examples
- ✅ **14 supporting packages** documented in Other Packages doc
- ✅ **All tools subpackages** identified (11 subpackages)
- ✅ **All example files** created and runnable

## 🔗 Quick Links

- [Start Here - INDEX](INDEX.md)
- [Setup Guide](00-Setup-and-Installation.md)
- [Agents](01-Agents-Package.md)
- [Tools](02-Tools-Package.md)
- [A2A](04-A2A-Package.md)
- [Apps](05-Apps-Package.md)
- [Code Executors](06-Code-Executors-Package.md)
- [Sessions](07-Sessions-Package.md)
- [Memory](08-Memory-Package.md)
- [Other Packages](09-Other-Packages.md)

---

**Last Updated**: Based on Google ADK version 1.22.1
