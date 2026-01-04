## Quick orientation for code-generating agents

This repo implements a Python-based voice/chat assistant built on LiveKit agents with a dynamic MCP tool integration and a Mem0-backed memory system. The goal here is to help an AI coding agent be immediately productive by pointing to the concrete files, patterns, and run/debug steps used across the project.

### Big picture
- Entry point: `agent.py` — creates an `Assistant` (subclass of `livekit.agents.Agent`) and starts a LiveKit session. See `AGENT_INSTRUCTION` and `SESSION_INSTRUCTION` in `prompts.py` for agent behavior.
- Dynamic tools: `mcp_client/*` provide an MCP client adapter. `MCPServerSse` (in `mcp_client/server.py`) talks to an MCP server via SSE; `mcp_client/util.py` converts MCP tools to a `FunctionTool` wrapper; `mcp_client/agent_tools.py` exposes `MCPToolsIntegration` which prepares and registers those tools on LiveKit agents.
- Built-in tools: `tools.py` contains local function tools (decorated with `@function_tool()`) used by the agent — e.g. `get_weather`, `search_web`, `send_email`.
- Memory: `mem0` client usage appears in `agent.py` and `test_mem0.py` for persisting/retrieving user memories.

### Project-specific conventions and gotchas (do these, not generic advice)
- Tools must be LiveKit function tools: local tools use `@function_tool()` and accept `context: RunContext` as the first param (see `tools.py`). When adding a new local tool, follow that signature and return a string.
- MCP tools are consumed dynamically. `mcp_client.util.to_function_tool` expects MCP tool objects with `inputSchema` and `on_invoke_tool` semantics. When altering MCP tool conversion, preserve the behavior of returning a string (JSON-encoded for complex content) as callers expect a string result.
- Agent tools are appended to `agent._tools` by `MCPToolsIntegration.register_with_agent` / `create_agent_with_tools`. Ensure any agent class you create accepts `chat_ctx` and `instructions` similar to `Assistant` in `agent.py`.
- Prompts enforce persona/format: `prompts.py` contains hard constraints (e.g., "Only answer in one sentence"). When changing prompt text, preserve structural assumptions in code that expects short assistant messages.
- Environment config: secrets and endpoints are read from the `.env` file. Required keys (present as placeholders in `.env`) include:
  - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - `MEM0_API_KEY`
  - `OPENAI_API_KEY` (used by livekit plugins)
  - `GMAIL_USER`, `GMAIL_APP_PASSWORD` (for `send_email`)
  - `N8N_MCP_SERVER_URL` (URL for the MCP SSE server)

### How to run / dev workflow (concrete commands)
1. Create and activate a virtualenv, install deps:

```ps1
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2. Populate `.env` (do NOT commit secrets). Example keys are listed above.

3. Run the agent locally (LiveKit credentials + MCP server required):

```ps1
python agent.py
```

4. Simple memory test:

```ps1
python test_mem0.py
```

### Code change patterns — concrete examples
- Adding a new local tool: create an async function, add `context: RunContext` as the first arg, decorate with `@function_tool()` and return a string. See `tools.py:get_weather`.
- Adding support for a new MCP tool type: the conversion path is `mcp_client.server.MCPServer` -> `mcp_client.util.to_function_tool` -> `mcp_client.agent_tools._create_decorated_tool`. Keep these layers small and return stable string results.
- When registering tools at runtime prefer `MCPToolsIntegration.create_agent_with_tools(...)` (used in `agent.py`) — it handles server connection and extends `agent._tools`.

### Tests & debugging
- There are minimal smoke tests: `test_mem0.py` demonstrates memory client usage. Use logging (repo uses Python logging) to trace runtime flows.
- If MCP tools are not appearing, check `cache_tools_list` flags: `agent.py` creates `MCPServerSse(..., cache_tools_list=True)`; `mcp_client.server.MCPServerSse` defaults to not caching. Tools may not refresh until the server connection is (re)initialized.

### What not to change without coordination
- Do NOT change the output contract of tool invocations: callers expect a string. If you need richer structured outputs, return JSON strings and document the change.
- Do NOT commit `.env` or secrets; add keys only as placeholders.

If any section is unclear or you'd like more examples (e.g., exact shape of MCP tool JSON schemas or a step-by-step debug scenario for MCP connectivity), tell me which area and I will expand or add code-snippets.
