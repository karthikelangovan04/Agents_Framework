## Code Execution with MCP Diagram Server and Artifacts (25a)

This document describes an **end-to-end pattern** where a **Python-based ADK agent**:

- Interprets a **user request for an architecture diagram**.
- **Writes diagram code or a diagram spec** (e.g., Graphviz DOT, PlantUML, or Python for `diagrams`).
- Uses an **MCP server** (with full Python + diagram libraries) to execute that code.
- Receives **2K and 4K image outputs**.
- Uses **ADK Artifacts** to **store** and **return** the generated images to the user.

It builds on:

- **Artifacts docs**: `https://google.github.io/adk-docs/artifacts/`
- **MCP tools docs**: `https://google.github.io/adk-docs/tools-custom/mcp-tools/`
- **LLM Agents & Code Execution**: `https://google.github.io/adk-docs/agents/llm-agents/#code-execution`

---

## Why MCP for Code Execution with Extra Libraries?

Gemini’s **built-in code execution** (via `BuiltInCodeExecutor`) runs **Python** in a **Google-managed sandbox** with a curated set of libraries (e.g., `numpy`, `pandas`, `matplotlib`), but:

- You **cannot `pip install` additional libraries** inside that sandbox.
- Diagram-oriented libraries like:
  - `diagrams`
  - `graphviz` (and system `dot`)
  - `plantuml`
  are **not guaranteed to be available** in the Gemini sandbox.

To get:

- Custom Python packages,
- System binaries (`dot`, `plantuml.jar`),
- High-resolution output control (2K, 4K),

you should **run code in your own environment** and expose it to ADK via **MCP**.

**Pattern:**

- **ADK Agent**: LLM “brain”, written in Python.
- **MCP Diagram Server**: Separate process/container where *you* control Python packages and binaries.
- **McpToolset**: ADK bridge that exposes MCP tools to the agent as regular tools.
- **Artifacts**: Persist diagram images as named, versioned blobs bound to a session or user.

---

## High-Level Architecture

1. **User** asks:  
   “Generate an architecture diagram of our ADK + MCP deployment, in both 2K and 4K resolution.”

2. **LlmAgent (Python ADK)**:
   - Parses the request (components, style, resolutions).
   - Writes a **diagram spec** (e.g., DOT, PlantUML, or `diagrams` Python snippet).
   - Calls an **MCP tool** (e.g., `generate_arch_diagram`) with:
     - `engine`: `"graphviz" | "plantuml" | "diagrams"`
     - `spec`: the diagram code/spec.
     - `resolutions`: `["2k", "4k"]`.

3. **MCP Diagram Server**:
   - Receives the tool call.
   - Runs Python code in an environment where you installed:
     - `graphviz` (and `dot`),
     - `diagrams`,
     - `plantuml` (or wrapper),
     - any other rendering stack you like.
   - Generates one or more **image files** (e.g., PNG in 2K/4K).
   - Returns them as MCP `Content` blocks that map to ADK `Part` objects with:
     - `inline_data.mime_type = "image/png"`
     - `inline_data.data = <image bytes>`

4. **ADK Agent (tool callback)**:
   - Receives image `Part`s from MCP.
   - Uses the **Artifact Service** (`InMemoryArtifactService` or `GcsArtifactService`) to:
     - `save_artifact("arch_diagram_2k.png", image_part_2k)`
     - `save_artifact("arch_diagram_4k.png", image_part_4k)`
   - Responds to the user with:
     - A textual summary,
     - Filenames or URLs for the generated diagrams.

---

## Components in Detail

### 1. MCP Diagram Server (Python)

The MCP server is a **standalone Python app** using the `mcp` library. Its job:

- Expose a tool like `generate_arch_diagram`.
- Accept:
  - `engine`: which diagram engine to use.
  - `spec`: the diagram spec / code written by the agent.
  - `resolution`: `"2k"` / `"4k"` etc.
- Return:
  - One or more **image contents** back to the ADK agent.

#### Example MCP Server Tool Signature

Conceptual JSON schema for the tool’s arguments:

```json
{
  "name": "generate_arch_diagram",
  "description": "Generate an architecture diagram image using graphviz/plantuml/diagrams.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engine": {
        "type": "string",
        "enum": ["graphviz", "plantuml", "diagrams"],
        "description": "Diagram engine to use."
      },
      "spec": {
        "type": "string",
        "description": "Diagram source code or spec (DOT, PlantUML, or Python snippet)."
      },
      "resolution": {
        "type": "string",
        "enum": ["2k", "4k"],
        "description": "Requested output resolution."
      }
    },
    "required": ["engine", "spec", "resolution"]
  }
}
```

Inside `call_tool`, you can:

- For `"graphviz"`:
  - Write `spec` to a `.dot` file.
  - Call `dot -Tpng -Gdpi=<dpi>` to control resolution, or scale the output with `Pillow`.
- For `"plantuml"`:
  - Use `plantuml` JAR or a Python wrapper to render PNG/SVG at the desired size.
- For `"diagrams"`:
  - Execute the Python snippet in a controlled environment and save the resulting diagram as PNG/SVG.

On success, return an MCP `Content` list with an **image content block**. When used with ADK’s `McpToolset` conversion utilities, this becomes an ADK `Part` with `inline_data`.

> See MCP details: `https://google.github.io/adk-docs/tools-custom/mcp-tools/`

---

### 2. Python ADK Agent with `McpToolset`

On the ADK side, you configure a **Python `LlmAgent`** with:

- A **model** (e.g., `gemini-2.0-flash`),
- **Instructions** describing how to:
  - Understand architecture diagram requests,
  - Choose engines/resolutions,
  - Call the `generate_arch_diagram` MCP tool,
  - Save outputs as artifacts.
- A **`McpToolset`** connected to your diagram MCP server.
- A **Runner** configured with an **ArtifactService**.

#### Agent Definition (Conceptual)

```python
import os
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

APP_NAME = "diagram_app"
MODEL = "gemini-2.0-flash"

# Path to your MCP diagram server script or binary
DIAGRAM_SERVER_SCRIPT = "/abs/path/to/diagram_mcp_server.py"

root_agent = LlmAgent(
    model=MODEL,
    name="arch_diagram_agent",
    instruction="""
You are an architecture diagram assistant.

When the user asks for an architecture or system diagram:
- Clarify the components and relationships in your own words.
- Decide which diagram engine to use: graphviz, plantuml, or diagrams.
- Create a clear diagram spec (DOT, PlantUML, or Python code).
- For each requested resolution (e.g., 2k and 4k), call the `generate_arch_diagram` tool
  with: engine, spec, and resolution.
- When the tool returns image content, save each image as an artifact using
  descriptive filenames like `arch_diagram_2k.png` and `arch_diagram_4k.png`.
- Finally, tell the user which artifacts you created, including filenames and resolutions.
""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python3",
                    args=[DIAGRAM_SERVER_SCRIPT],
                ),
            ),
            # Optionally restrict tools:
            # tool_filter=["generate_arch_diagram"],
        )
    ],
)


def build_runner() -> Runner:
    """Create a Runner with session + artifact services wired up."""
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    return Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        artifact_service=artifact_service,
    )
```

This agent:

- Treats MCP’s `generate_arch_diagram` as a **normal ADK tool** via `McpToolset`.
- Has no direct dependency on `graphviz`/`plantuml` locally; those live in the MCP server container.

---

### 3. Using ADK Artifacts to Store Diagram Images

Per the Artifacts docs (`https://google.github.io/adk-docs/artifacts/`), artifacts are:

- **Named, versioned blobs** stored in an `ArtifactService`,
- Represented as `google.genai.types.Part` with `inline_data` in ADK,
- Scoped to **session** or **user** (via filename prefix `user:` for user-scope).

We will:

- Take the **image `Part`** returned by the MCP diagram tool,
- Wrap/save it as an artifact:
  - `arch_diagram_2k.png`
  - `arch_diagram_4k.png`
- Later, the frontend or another tool can `load_artifact` and send it to the user.

#### Example: Saving MCP-Generated Images as Artifacts

Inside a **tool or callback** running on the ADK side:

```python
from google.adk.agents.callback_context import CallbackContext

async def save_diagram_images_as_artifacts(
    context: CallbackContext,
    images: dict[str, types.Part],
) -> dict[str, int]:
    """
    Save diagram images (2k, 4k) as artifacts.

    Args:
        context: ADK callback context with artifact_service configured.
        images: mapping from logical name -> Part, e.g.
            {
              "2k": Part(inline_data=Blob(mime_type="image/png", data=...)),
              "4k": Part(...)
            }

    Returns:
        Mapping from filename -> saved version number.
    """
    versions: dict[str, int] = {}

    for res, part in images.items():
        filename = f"arch_diagram_{res}.png"  # e.g., arch_diagram_2k.png
        version = await context.save_artifact(filename=filename, artifact=part)
        versions[filename] = version

    return versions
```

When used with a Runner configured with an `ArtifactService`, the above:

- Will create (or increment versions of) artifacts bound to the current:
  - `app_name`, `user_id`, `session_id` (session-scope),
  - Or user-scope if you prefix filename with `user:`.

> See the Artifacts page for details on `save_artifact`, `load_artifact`, and `list_artifacts`.

---

### 4. End-to-End Flow: From Query to 2K/4K Diagrams

Putting it all together:

1. **User Query** (via web UI or CLI):
   - “Create an ADK + MCP architecture diagram showing:
     - A Python ADK agent
     - An MCP diagram server
     - Gemini
     - Artifacts in GCS
     - And generate both 2K and 4K PNG images.”

2. **LlmAgent Reasoning**:
   - Understands the architecture components.
   - Decides on a diagram engine (e.g., `"graphviz"`).
   - Generates a DOT spec, e.g.:
     - `digraph G { ADK_Agent -> MCP_Server -> Gemini; MCP_Server -> GCS; }`

3. **Tool Call via MCP**:
   - For each resolution in `["2k", "4k"]`, the agent calls:
     - `generate_arch_diagram(engine="graphviz", spec=dot_spec, resolution="2k")`
     - `generate_arch_diagram(engine="graphviz", spec=dot_spec, resolution="4k")`

4. **MCP Diagram Server Execution**:
   - Receives each call.
   - Runs `dot` or other tools to render high-resolution PNG files.
   - Returns image contents as MCP `Content` that map to ADK `Part` with:
     - `inline_data.mime_type="image/png"`,
     - `inline_data.data=<png_bytes>`.

5. **ADK Callback / Tool Handling**:
   - For each response:
     - Extract the `Part` representing the image.
     - Call `save_diagram_images_as_artifacts(...)` (as above).
   - Maintain a list of:
     - Filenames: `"arch_diagram_2k.png"`, `"arch_diagram_4k.png"`,
     - Versions: `0`, `1`, etc.

6. **Final Agent Response**:

   Example natural-language reply:

   > “I created two architecture diagrams and stored them as artifacts:
   > - `arch_diagram_2k.png` (2K resolution, version 0)
   > - `arch_diagram_4k.png` (4K resolution, version 0)
   >
   > Your frontend can now load these via the Artifacts APIs and display or download them.”

7. **Frontend Delivery (outside this doc)**:
   - Your web/API layer can:
     - Call `load_artifact("arch_diagram_2k.png")`,
     - Stream the bytes to the browser as an image.

---

## Design Considerations & Best Practices

### Why Not Use Gemini’s Built-In Code Executor Here?

- Gemini’s code executor is ideal for:
  - Math, data analysis, and quick plots with built-in libraries.
- It is **not designed** for:
  - Arbitrary PyPI installations,
  - System-level binaries (`dot`, `plantuml`),
  - Long-running or heavy rendering pipelines.

By offloading heavy/third-party diagram work to an MCP server:

- You stay within Gemini’s supported operations.
- You keep your diagram environment fully under your control.

### Choosing Engines and Formats

- **Graphviz**:
  - Great for classical architecture and network diagrams.
  - Use DPI, image size, or scaling to hit “2K/4K” style resolutions.
- **PlantUML**:
  - Ideal for UML-style diagrams and sequence diagrams.
  - Can be rendered to PNG/SVG and sized appropriately.
- **`diagrams` library**:
  - Pythonic, cloud-architecture focused.
  - Good for cloud provider icons and infra diagrams.

You can expose **multiple engines** behind the same MCP tool and let the **agent choose** per request.

### Artifacts: Session vs User Scope

- Use **session-scope filenames** (no prefix) when:
  - Diagrams are specific to a single conversation.
- Use **user-scope filenames** (prefix `user:`) when:
  - You want the user to retrieve diagrams across sessions, e.g.:
    - `"user:arch_diagram_latest_2k.png"`.

> See namespacing notes in the Artifacts docs for details.

---

## Summary

This 25a pattern demonstrates how to:

- **Let a Python ADK agent “write code/specs” for diagrams**, but execute them in an **MCP server** where any diagram libraries you need can be installed.
- **Generate high-resolution (2K/4K) architecture diagrams** using Graphviz, PlantUML, or the `diagrams` library.
- **Persist the resulting images as ADK Artifacts**, which can be fetched, versioned, and delivered to users across sessions.

Use this pattern any time you need:

- Complex or library-heavy code execution that goes beyond Gemini’s built-in sandbox, **and**
- Tight integration with ADK’s session, tooling, and artifact systems.

