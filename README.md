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
