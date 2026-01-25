# Google ADK Documentation - Complete File Path Reference

This document provides a complete reference of all documentation files, example files, and their locations.

## 📚 Documentation Files

All documentation files are located in the `docs/` directory:

| Document | File Path | Package(s) Covered |
|----------|-----------|-------------------|
| **INDEX** | `docs/INDEX.md` | Navigation and overview |
| **Setup Guide** | `docs/00-Setup-and-Installation.md` | Installation and setup |
| **Package Listing** | `docs/03-Package-Listing.md` | Complete package inventory |
| **Agents** | `docs/01-Agents-Package.md` | `google.adk.agents` |
| **Tools** | `docs/02-Tools-Package.md` | `google.adk.tools` + 11 subpackages |
| **A2A** | `docs/04-A2A-Package.md` | `google.adk.a2a` |
| **Apps** | `docs/05-Apps-Package.md` | `google.adk.apps` |
| **Code Executors** | `docs/06-Code-Executors-Package.md` | `google.adk.code_executors` |
| **Sessions** | `docs/07-Sessions-Package.md` | `google.adk.sessions` |
| **Memory** | `docs/08-Memory-Package.md` | `google.adk.memory` |
| **State Management** | `docs/11-State-Management.md` | `google.adk.sessions.state` |
| **Other Packages** | `docs/09-Other-Packages.md` | models, auth, examples, planners, flows, plugins, artifacts, events, telemetry, evaluation, features, cli, platform, runners, dependencies, errors, utils, version |

## 💻 Example Files

All runnable example files are located in the `examples/` directory:

| Example | File Path | Description |
|---------|-----------|-------------|
| Simple Agent | `examples/simple_agent.py` | Basic agent example |
| Tool Agent | `examples/tool_agent.py` | Agent with tools |
| Multi-Agent | `examples/multi_agent.py` | Multi-agent system |
| Web App | `examples/web_app.py` | Web application |
| Remote Server | `examples/remote_agent_server.py` | Remote agent server |
| Remote Client | `examples/remote_agent_client.py` | Remote agent client |

## 🔧 Utility Scripts

| Script | File Path | Purpose |
|--------|-----------|---------|
| Package Explorer | `explore_packages.py` | Explore all ADK packages |
| Package Details | `get_package_details.py` | Get detailed package information |

## 📦 Complete Package Coverage

### ✅ Fully Documented Packages (with examples)

1. **agents** (`google.adk.agents`)
   - File: `docs/01-Agents-Package.md`
   - Examples: 5 runnable examples
   - Classes: Agent, BaseAgent, LlmAgent, SequentialAgent, ParallelAgent, LoopAgent

2. **tools** (`google.adk.tools`)
   - File: `docs/02-Tools-Package.md`
   - Examples: 7 runnable examples
   - Subpackages: bigquery, bigtable, spanner, pubsub, google_api_tool, mcp_tool, openapi_tool, apihub_tool, application_integration_tool, retrieval, computer_use

3. **a2a** (`google.adk.a2a`)
   - File: `docs/04-A2A-Package.md`
   - Examples: 4 examples
   - Subpackages: converters, executor, logs, utils

4. **apps** (`google.adk.apps`)
   - File: `docs/05-Apps-Package.md`
   - Examples: 4 examples
   - Classes: App, ResumabilityConfig

5. **code_executors** (`google.adk.code_executors`)
   - File: `docs/06-Code-Executors-Package.md`
   - Examples: 3 examples
   - Classes: BaseCodeExecutor, BuiltInCodeExecutor, UnsafeLocalCodeExecutor

6. **sessions** (`google.adk.sessions`)
   - File: `docs/07-Sessions-Package.md`
   - Examples: 4 examples
   - Classes: Session, BaseSessionService, InMemorySessionService, VertexAiSessionService

7. **memory** (`google.adk.memory`)
   - File: `docs/08-Memory-Package.md`
   - Examples: 4 examples
   - Classes: BaseMemoryService, InMemoryMemoryService, VertexAiMemoryBankService, VertexAiRagMemoryService

8. **state** (`google.adk.sessions.state`)
   - File: `docs/11-State-Management.md`
   - Examples: 4 examples
   - Classes: State
   - Utilities: extract_state_delta

### 📝 Documented in Other Packages

8. **models** (`google.adk.models`)
   - File: `docs/09-Other-Packages.md#models-package`
   - Classes: BaseLlm, Gemini, Gemma, LLMRegistry, ApigeeLlm

9. **auth** (`google.adk.auth`)
   - File: `docs/09-Other-Packages.md#auth-package`
   - Subpackages: credential_service, exchanger, refresher

10. **examples** (`google.adk.examples`)
    - File: `docs/09-Other-Packages.md#examples-package`
    - Classes: BaseExampleProvider, Example, VertexAiExampleStore

11. **planners** (`google.adk.planners`)
    - File: `docs/09-Other-Packages.md#planners-package`
    - Classes: BasePlanner, BuiltInPlanner, PlanReActPlanner

12. **flows** (`google.adk.flows`)
    - File: `docs/09-Other-Packages.md#flows-package`
    - Subpackages: llm_flows

13. **plugins** (`google.adk.plugins`)
    - File: `docs/09-Other-Packages.md#plugins-package`
    - Classes: BasePlugin, PluginManager, LoggingPlugin, ReflectAndRetryToolPlugin

14. **artifacts** (`google.adk.artifacts`)
    - File: `docs/09-Other-Packages.md#artifacts-package`
    - Classes: BaseArtifactService, FileArtifactService, GcsArtifactService, InMemoryArtifactService

15. **events** (`google.adk.events`)
    - File: `docs/09-Other-Packages.md#events-package`
    - Classes: Event, EventActions

16. **telemetry** (`google.adk.telemetry`)
    - File: `docs/09-Other-Packages.md#telemetry-package`
    - Functions: trace_call_llm, trace_tool_call, trace_send_data, trace_merged_tool_calls

17. **evaluation** (`google.adk.evaluation`)
    - File: `docs/09-Other-Packages.md#evaluation-package`
    - Classes: AgentEvaluator
    - Subpackages: simulation

18. **features** (`google.adk.features`)
    - File: `docs/09-Other-Packages.md`
    - Classes: FeatureName
    - Functions: experimental, stable, working_in_progress, is_feature_enabled

19. **cli** (`google.adk.cli`)
    - File: `docs/09-Other-Packages.md#cli-package`
    - Subpackages: built_in_agents, conformance, plugins, utils

20. **platform** (`google.adk.platform`)
    - File: `docs/09-Other-Packages.md`
    - Subpackages: internal

21. **runners** (`google.adk.runners`)
    - File: Referenced in `docs/01-Agents-Package.md`
    - Classes: Runner

22. **dependencies** (`google.adk.dependencies`)
    - Purpose: Dependency management

23. **errors** (`google.adk.errors`)
    - Purpose: Error handling and exceptions

24. **utils** (`google.adk.utils`)
    - Purpose: Utility functions

25. **version** (`google.adk.version`)
    - Purpose: Version information

## 📊 Summary Statistics

- **Total Packages**: 25
- **Fully Documented**: 8 packages (with detailed examples)
- **Documented in Other**: 17 packages
- **Documentation Files**: 12 markdown files
- **Example Files**: 6 runnable Python files
- **Utility Scripts**: 2 Python scripts

## 🔗 Quick Access Links

### Start Here
- [INDEX.md](docs/INDEX.md) - Main navigation
- [Package Listing](docs/03-Package-Listing.md) - Complete package inventory
- [Setup Guide](docs/00-Setup-and-Installation.md) - Get started

### Core Packages
- [Agents](docs/01-Agents-Package.md)
- [Tools](docs/02-Tools-Package.md)
- [A2A](docs/04-A2A-Package.md)
- [Apps](docs/05-Apps-Package.md)
- [Code Executors](docs/06-Code-Executors-Package.md)
- [Sessions](docs/07-Sessions-Package.md)
- [Memory](docs/08-Memory-Package.md)
- [State Management](docs/11-State-Management.md)
- [Other Packages](docs/09-Other-Packages.md)

### Examples
- [Simple Agent](examples/simple_agent.py)
- [Tool Agent](examples/tool_agent.py)
- [Multi-Agent](examples/multi_agent.py)
- [Web App](examples/web_app.py)
- [Remote Server](examples/remote_agent_server.py)
- [Remote Client](examples/remote_agent_client.py)

---

**Last Updated**: Based on Google ADK version 1.22.1  
**Project Root**: `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore`
