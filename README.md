# scopus-langgraph-agent

A LangGraph agent that answers natural-language questions about research literature by querying Scopus through an MCP server.

## How the layers fit together

```
User (chat UI)
   │  "Most cited UK cancer papers since 2020"
   ▼
LangGraph agent (agent/)          ← Claude via langchain-anthropic
   │  decides which tool to call and writes the Scopus query string
   ▼
MCP server (server/)              ← mcp SDK; tools exposed via langchain-mcp-adapters
   │  search_scopus(query='TITLE-ABS-KEY(cancer) AND AFFILCOUNTRY("United Kingdom") AND PUBYEAR > 2019', sort='-citedby-count')
   ▼
ScopusClient (server/scopus_client.py)
   │
   ▼
Elsevier Scopus API
```

1. **Scopus client** (`server/scopus_client.py`): handles authentication, endpoints, quota and errors for the Scopus API.
2. **MCP server** (`server/`): exposes the client methods as MCP tools. Each tool's description explains Scopus query syntax so the LLM can call it correctly.
3. **LangGraph agent** (`agent/`): Claude turns the user's question into Scopus Advanced Search syntax, calls the tools, refines the query if needed and summarises the results.
4. **Chat front end**: passes the user's questions to the agent and shows its answers.

## Why LangGraph

The agent layer is built with [LangGraph](https://github.com/langchain-ai/langgraph) for these reasons:

- **Explicit control flow.** The agent loop is written out as nodes (call the model, run tools) and edges, so every step is visible and easy to extend, for example with query validation, abstract fetching or a human approval step.
- **Model-agnostic.** Claude is used via `langchain-anthropic`, and switching provider means changing the model class plus its package and API key. The graph, tools and MCP connection stay the same. Each model still needs evaluating, since query-writing quality and prompt behaviour vary.
- **MCP support.** `langchain-mcp-adapters` loads the MCP server's tools as agent tools.
- **State and memory built in.** Follow-up questions, checkpoints and resumable conversations come with the framework.
- **Observability.** LangSmith traces each step, which helps with debugging and evals.

Trade-offs accepted: a steeper learning curve and more boilerplate than simpler frameworks, plus APIs that change fairly often.

Vendor lock-in is limited to the agent layer either way: the MCP server and Scopus client work with any MCP client.

### Alternatives considered

| Option | Why not chosen |
|---|---|
| Claude Desktop / Claude Code | No custom agent code needed (they can use the MCP server directly), but they only run Claude and the agent can't be customised or evaluated in code |
| Claude Agent SDK / Anthropic SDK | Simple and well suited to Claude, but tied to Claude models |
| Pydantic AI | Simple, type-safe and model-agnostic, but has less mature orchestration for complex multi-step flows |
| LlamaIndex | Strongest for retrieval over your own documents (RAG), which this project doesn't need yet, since its data comes from a live API |
| CrewAI | Designed for teams of cooperating agents; less control and more overhead than a single agent with tools needs |
