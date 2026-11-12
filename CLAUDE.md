# Scopus LangGraph agent

A conversational research assistant: a LangGraph agent (Claude) turns natural-language questions into Scopus Advanced Search queries, runs them through an MCP server, and answers with cited papers.

## Structure

- `server/scopus_client.py`: layer 1, HTTP client for the Scopus Search API
- `server/mcp_server.py`: layer 2, MCP server (stdio) exposing the `search_scopus` tool
- `server/demo_data.py`: synthetic search results used when `DEMO_MODE=1`
- `agent/graph.py`: layer 3, the LangGraph ReAct agent (`make_model`, `build_agent`, CLI in `main`)
- `streamlit_app.py`: layer 4, web chat UI (hosted demo)
- `evals/`: eval cases and runner, checking the Scopus query the model writes for each question
- `tests/`: unit tests with synthetic fixtures
- `scripts/check_guardrails.py`: checks project rules that tests can't catch

## Commands

- Install: `pip install -e ".[dev]"` (Python 3.11+, in `.venv`)
- CLI agent: `python -m agent.graph`
- Web UI: `streamlit run streamlit_app.py`
- Tests: `pytest -v`
- Guardrails: `python scripts/check_guardrails.py`
- Evals (calls the LLM, costs money): `DEMO_MODE=1 python -m evals.run_evals`
- With tracing (demo mode only): `DEMO_MODE=1 LANGSMITH_TRACING=true python -m evals.run_evals`

## Project rules

- Scopus data belongs to Elsevier. Never commit real Scopus API responses; real fixtures stay local and gitignored. Tests use synthetic data.
- The hosted Streamlit app, demo videos and screenshots use demo mode (`DEMO_MODE=1`, synthetic results) until Elsevier approves real data.
- LangSmith tracing only in demo mode, so real Scopus data never reaches LangSmith. Enforced in `agent/graph.py`, which turns tracing off unless `DEMO_MODE=1`. `LANGSMITH_TRACING` is also deliberately not in `.env`.
- The MCP server talks JSON-RPC over stdout. Never `print` to stdout in `server/`; log to stderr. Enforced by `scripts/check_guardrails.py`.
- Never commit `.env` or put keys in code. New variables go in `.env.example` as empty placeholders.
- Evals call a real LLM, so they run on demand or on a schedule, not on every push.
- Changes land through pull requests; tests and guardrail checks must pass before merging.
