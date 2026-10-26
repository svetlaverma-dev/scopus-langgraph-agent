"""Evaluate how well the agent turns questions into Scopus queries.

Sends each case to the model once and checks its first tool call.
Makes no Scopus API calls; each case costs one LLM call.

Usage: python -m evals.run_evals
"""
import asyncio
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.graph import MCP_SERVERS, SYSTEM_PROMPT, make_model
from evals.cases import CASES


def check(case, tool_calls):
    """Return a list of failure reasons (empty means the case passed)."""
    if not case.get("expect_tool_call", True):
        return [f"expected no tool call, got {len(tool_calls)}"] if tool_calls else []
    if not tool_calls:
        return ["expected a search_scopus call, got none"]

    args = tool_calls[0]["args"]
    query = args.get("query", "")
    failures = []
    for pattern in case.get("query_must_match", []):
        if not re.search(pattern, query, re.IGNORECASE):
            failures.append(f"query does not match /{pattern}/")
    if "sort" in case and args.get("sort", "-citedby-count") != case["sort"]:
        failures.append(f"sort is {args.get('sort', '-citedby-count')!r}, expected {case['sort']!r}")
    if not 1 <= args.get("count", 10) <= 25:
        failures.append(f"count {args.get('count')} outside 1-25")
    if query.count("(") != query.count(")"):
        failures.append("unbalanced parentheses")
    return failures


async def main():
    print(f"       hohohohohohoho")
    tools = await MultiServerMCPClient(MCP_SERVERS).get_tools()
    model = make_model().bind_tools(tools)

    passed = 0
    for case in CASES:
        response = await model.ainvoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(case["question"])])
        failures = check(case, response.tool_calls)
        passed += not failures

        query = response.tool_calls[0]["args"].get("query") if response.tool_calls else "(no tool call)"
        print(f"[{'PASS' if not failures else 'FAIL'}] {case['id']}")
        print(f"       query: {query}")
        for failure in failures:
            print(f"       - {failure}")

    print(f"\n{passed}/{len(CASES)} passed")


if __name__ == "__main__":
    asyncio.run(main())
