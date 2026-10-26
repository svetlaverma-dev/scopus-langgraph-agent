# scopus-langgraph-agent

A conversational AI agent for intelligent search over research literature. Ask a question in plain English, such as *"What are the most cited UK cancer papers since 2020?"*, and the agent turns it into a Scopus Advanced Search query, runs it through an MCP server and answers with cited results from live data.

## Contents

- [What it is](#what-it-is)
- [Why it was built](#why-it-was-built)
- [Quick start](#quick-start)
- [How the layers fit together](#how-the-layers-fit-together)
- [Why LangGraph](#why-langgraph)
  - [Alternatives considered](#alternatives-considered)
- [Roadmap](#roadmap)
  - [1. Evals suite (in progress)](#1-evals-suite-in-progress)
  - [2. CI and observability](#2-ci-and-observability)
  - [3. Guardrails and trust](#3-guardrails-and-trust)
  - [4. More tools and a web UI](#4-more-tools-and-a-web-ui)
  - [5. Vendor routing through an LLM gateway](#5-vendor-routing-through-an-llm-gateway)

## What it is

The agent combines several capabilities:

- **Conversational AI.** You talk to it in natural language, and it keeps context across turns, so follow-ups like *"Which of those are original research?"* work.
- **Intelligent, agentic search.** Claude, orchestrated by LangGraph, decides when to search, writes the Scopus query itself, reads the results, and refines or corrects the query (for example, after a syntax error) before answering.
- **Grounded answers.** Answers come from Scopus results, not the model's memory. Each paper is cited with its title, first author, year and DOI.

## Why it was built

[Scopus](https://www.elsevier.com/products/scopus) is Elsevier's abstract and citation database, curated by independent subject matter experts, with more than 100 million records according to Elsevier. Getting precise answers from it means knowing its [Advanced Search syntax](https://dev.elsevier.com/sc_search_tips.html), such as `TITLE-ABS-KEY(...)`, `AFFILCOUNTRY(...)` and `PUBYEAR > ...`. This project explores how an AI agent can remove that barrier, so anyone can query complex data sources in plain language.

It is also a hands-on exploration of how production-style agentic AI systems are put together:

- a layered architecture separating the API client, the tool layer and the agent
- tools exposed through the open **Model Context Protocol (MCP)**, so any MCP-compatible client can reuse them
- a model-agnostic agent built with **LangGraph**
- offline tests with synthetic fixtures, and care with third-party data licensing

## Quick start

Requires Python 3.11+, an Elsevier Scopus API key (from the [Elsevier Developer Portal](https://dev.elsevier.com)) and an Anthropic API key (from the [Anthropic Console](https://console.anthropic.com)).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your Scopus and Anthropic API keys
```

Run the agent:

```bash
python -m agent.graph
```

Then ask a question, e.g. `What are the most cited UK cancer papers since 2020?`. Each Scopus query the agent writes is printed as a `[tool]` line before its answer. Type `quit` to exit.

Run the tests (offline, using saved fixtures):

```bash
pytest -v
```

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

## Roadmap

The phases are ordered so that each one builds on the last. Evals and observability come first because they make every later change measurable.

### 1. Evals suite (in progress)

Measure how well the agent turns natural-language questions into correct Scopus queries, so that changes to prompts, tool descriptions or models are judged by evidence rather than guesswork.

- A set of realistic questions, each with rules its query must satisfy: the right field codes (`AFFILCOUNTRY`, `AUTHLASTNAME`, `DOCTYPE`), correct year logic ("since 2020" means `PUBYEAR > 2019`), a suitable sort order ("most cited" or "recent"), and no search at all for off-topic questions.
- Rules match patterns rather than exact strings, so equally valid queries pass.
- Checks the agent's first tool call without calling Scopus, so a run uses no Scopus quota and one LLM call per question.
- Later: end-to-end evals that grade the final answers (for example, are all papers cited and relevant?), possibly using an LLM as a judge.

### 2. CI and observability

- **Continuous integration:** a GitHub Actions workflow runs the test suite on every push, with a status badge in this README.
- **Tracing with LangSmith:** record every agent run (each step, tool call and query, plus latency and token cost) for debugging, and to provide the cost and latency data that later phases depend on.

### 3. Guardrails and trust

- **Prompt-injection defence:** treat tool results (paper titles, abstracts) as untrusted data, so text inside them can't redirect the agent. Covered by dedicated eval cases.
- **Groundedness check:** verify that every paper cited in an answer actually appeared in the search results, so citations are never invented.

### 4. More tools and a web UI

- **New MCP tools:** `get_abstract` and `search_authors`, wrapping the Scopus client's existing abstract and author endpoints. They let the agent summarise papers, identify leading researchers, and retrieve complete affiliation data, which search results only partly include.
- **Web chat interface:** a lightweight browser UI (for example, Streamlit or Gradio) and a short demo recording in this README, so the agent can be tried and seen without a terminal.

### 5. Vendor routing through an LLM gateway

Add a second AI vendor alongside Anthropic and route each request between them by rules, turning the agent's model layer into an LLM gateway.

- **Fallback:** if one vendor fails (outage, rate limit or spend cap), the request automatically goes to the other.
- **Rule-based routing:** for example, simple questions go to a cheaper model and complex ones to a stronger model, or traffic is split between vendors for A/B comparison.
- Routing is decided once per conversation, to keep behaviour consistent across turns.
- The evals suite and tracing data compare vendors on query quality, cost and speed, so routing rules are based on measured results.
- The LangGraph graph, MCP server and tools stay unchanged. Only the model layer changes, which the model-agnostic design allows.
