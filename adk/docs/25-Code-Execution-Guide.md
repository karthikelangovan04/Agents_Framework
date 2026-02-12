## Code Execution in Google ADK

This document summarizes how **code execution** works in the Google Agent Development Kit (ADK), which languages are involved, and how to use the feature from Python (and, at a high level, Java).

---

## Conceptual Overview

- **What “code execution” means**:  
  Code execution lets an `LlmAgent` write Python code, run it in a safe Google-managed sandbox (via the Gemini API), and use the results to refine its answer.

- **Two distinct language layers**:
  - **Host language**: The language you are using to build the agent (Python, TypeScript/JS, Go, Java).
  - **Sandbox language**: The language that actually runs inside the Gemini code execution sandbox.  
    - **Today this is Python only.**

- **Key ADK pieces (Python)**:
  - `google.adk.agents.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.InMemorySessionService` (or other session services)
  - `google.adk.code_executors.BuiltInCodeExecutor`
  - `google.genai.types` (for low-level Gemini types like `Content`, `Part`, `GenerateContentConfig`, etc.)

Relevant external docs:
- ADK LLM agents (including code execution):  
  `https://google.github.io/adk-docs/agents/llm-agents/#code-execution`
- Gemini API code execution overview and limits:  
  `https://ai.google.dev/gemini-api/docs/code-execution`

---

## Supported Languages

### Host languages (for building agents)

ADK supports multiple host SDKs:

- **Python ADK**
- **TypeScript / JavaScript ADK**
- **Go ADK**
- **Java ADK**

Any of these can build an `LlmAgent`. However, only some expose a *first-class* integration for Gemini’s code execution tool:

- **Python**: via `code_executor=BuiltInCodeExecutor()`.
- **Java**: via `BuiltInCodeExecutionTool` added as a tool on `LlmAgent`.

The other host SDKs can still call Gemini’s code-execution tool through the Gemini API directly, but the focus of the ADK docs you referenced is on Python and Java.

### Sandbox language (what actually executes)

The **code execution sandbox** behind ADK’s `BuiltInCodeExecutor` runs:

- **Python (only)** as of 2026.

You can ask the model to *generate* other languages (JavaScript, SQL, Bash, etc.), but when ADK or Gemini talk about “code execution” as a tool, this means:

- The model writes **Python**.
- The Python code is sent to the **Gemini code execution sandbox**.
- The sandbox executes the Python code and returns the result.

---

## Python Code Execution: Environment and Libraries

The Gemini code execution environment is a **pre-configured Python 3 sandbox**. You do **not** manage its environment via your local virtualenv; instead, Google manages the runtime and its libraries.

Key points from the Gemini docs:

- **Language**: Python 3 (Google-managed).
- **Execution limits**:
  - ~30 seconds maximum per code execution.
  - Typically up to 5 executions per interaction/turn before a re-prompt is needed.
  - No outbound internet access; designed for local reasoning, math, data analysis, and working on uploaded files or provided data.
- **Example preinstalled libraries** (non-exhaustive, but representative):
  - **Data / numerics**: `numpy`, `pandas`
  - **Visualization**: `matplotlib` (for plots/graphs the model can “see`)

Your **local** `adk/.venv` only needs:

- `google-adk` / `google.adk` (ADK runtime)
- `google-genai` (Gemini client library)
- Any of *your* own application dependencies

You do **not** install `numpy`/`pandas` into the sandbox; they already exist in Gemini’s environment.

---

## Python ADK: Using `BuiltInCodeExecutor`

### High-level flow

1. You define an `LlmAgent` with:
   - A `model` (for example `gemini-2.0-flash` or a newer model supporting code execution).
   - A natural language `instruction` that tells the agent how and when to write and run code.
   - `code_executor=BuiltInCodeExecutor()`.
2. During a conversation, the LLM may decide to:
   - Produce **executable code parts** (Python).
   - Send them to the code execution tool.
3. ADK’s `BuiltInCodeExecutor`:
   - Forwards the code to the Gemini code-execution sandbox.
   - Receives results (`stdout`, return values, or errors).
4. The agent:
   - Reads the result.
   - Produces a final natural language (or structured) response for the user.

### Minimal Python example

```python
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types

APP_NAME = "calculator_app"
USER_ID = "user1234"
SESSION_ID = "session_code_exec"
MODEL = "gemini-2.0-flash"  # or another Gemini 2.x model with code execution support

# 1. Define an agent that can execute Python code
code_agent = LlmAgent(
    name="calculator_agent",
    model=MODEL,
    code_executor=BuiltInCodeExecutor(),  # <-- enables code execution
    instruction="""
    You are a calculator agent.
    When given a mathematical or data-analysis question:
    - Write Python code using the code execution tool.
    - Execute the code.
    - Return only the final numerical result as plain text (no markdown).
    """,
    description="Executes Python code to perform calculations.",
)

# 2. Set up session + runner
session_service = InMemorySessionService()
session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
)

runner = Runner(
    agent=code_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

# 3. Helper to send a question
def ask_agent(question: str) -> None:
    content = types.Content(role="user", parts=[types.Part(text=question)])
    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    )

    for event in events:
        if event.is_final_response() and event.content:
            answer = event.content.parts[0].text.strip()
            print("Q:", question)
            print("A:", answer)

# 4. Example queries
ask_agent("What is (5 + 7) * 3?")
ask_agent("Using numpy, compute the mean of [1, 2, 3, 4, 5].")
```

**Notes:**

- The *agent* decides when to call the code executor; your instruction should encourage it to use code for non-trivial calculations.
- When the model uses code execution, you will see intermediate events with:
  - `executable_code.code` (Python source).
  - `code_execution_result` (result or error).

---

## Java ADK: Code Execution Tool (High Level)

In Java, code execution is wired in as a **tool** attached to `LlmAgent` rather than as a `code_executor` parameter:

- Use `BuiltInCodeExecutionTool`.
- Add it to the agent’s `tools(...)` list.
- Give instructions that tell the LLM to write and execute Python via this tool.

Conceptual sketch:

```java
import com.google.adk.agents.BaseAgent;
import com.google.adk.agents.LlmAgent;
import com.google.adk.runner.Runner;
import com.google.adk.sessions.InMemorySessionService;
import com.google.adk.tools.BuiltInCodeExecutionTool;
import com.google.genai.types.Content;
import com.google.genai.types.Part;
import com.google.common.collect.ImmutableList;

public class CodeExecutionExample {
  public static void main(String[] args) {
    String MODEL = "gemini-2.0-flash";

    // 1. Built-in code execution tool
    BuiltInCodeExecutionTool codeTool = new BuiltInCodeExecutionTool();

    // 2. LlmAgent configured with the tool
    BaseAgent agent =
        LlmAgent.builder()
            .name("java_calculator_agent")
            .model(MODEL)
            .tools(ImmutableList.of(codeTool))
            .instruction(
                """
                You are a calculator agent.
                When given a math or data question, write Python code and execute it
                using the code execution tool, then return only the final numeric answer.
                """)
            .description("Executes Python code via Gemini code execution.")
            .build();

    // 3. Session + runner
    InMemorySessionService sessionService = new InMemorySessionService();
    Runner runner = new Runner(agent, "java_calculator_app", null, sessionService);

    Content msg =
        Content.builder()
            .role("user")
            .parts(ImmutableList.of(Part.fromText("Compute the standard deviation of [1,2,3,4,5].")))
            .build();

    runner
        .runAsync("user1234", "session1234", msg)
        .blockingForEach(
            event -> {
              if (event.finalResponse()
                  && event.content().isPresent()
                  && event.content().get().parts().isPresent()
                  && !event.content().get().parts().get().isEmpty()) {
                System.out.println(
                    "Answer: " + event.content().get().parts().get().get(0).text().orElse(""));
              }
            });
  }
}
```

This uses the same Gemini Python sandbox under the hood; Java is only the orchestrator.

---

## Practical Tips and Limitations

- **Use code execution for**:
  - Non-trivial math, statistics, and numerical analysis.
  - DataFrame-style operations (with `pandas`) on tabular data.
  - Generating and interpreting plots (`matplotlib`).
  - Inspecting and transforming user-provided data files (as supported by the Gemini API).

- **Limitations**:
  - Only Python code is executed; other languages are generated as text only.
  - No network access from executed code.
  - Execution is time-limited and resource-constrained; long-running jobs will fail.

---

## When to Use ADK Code Execution vs Custom Tools

- **Use code execution** when:
  - You want the LLM to “scratchpad” complex logic in Python and check itself.
  - You need quick, low-ops data wrangling or analysis tightly integrated with the conversation.

- **Use custom function tools** (`FunctionTool` / standard ADK tools) when:
  - Logic must be deterministic, production-grade, or integrated with your own infrastructure.
  - You need to call external APIs, databases, or internal services that the code executor cannot access.

In practice, many agents combine:

- **Function tools** for stable, production logic.
- **Code execution** for flexible, model-driven analysis and iterative reasoning.

