"""LangGraph agent that answers research questions using the Scopus MCP server (layer 3)."""
import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

SYSTEM_PROMPT = """You are a research assistant with access to the Scopus database.
Answer questions by turning them into Scopus Advanced Search queries for the search_scopus tool.
Only search when the user wants to find, list or compare published literature. For greetings,
general questions or definitions of concepts, answer directly from general knowledge without searching.
Only add the filters the user asked for. Do not add DOCTYPE or year filters unless the question
implies them (for example "recent", "since 2020" or "not reviews").
If a query fails, read the error, fix the query and try again.
You cannot download papers. If asked for a PDF, find the paper and give its DOI link instead.
Answer only from the tool results, citing each paper with its title, first author, year and DOI."""

if os.environ.get("DEMO_MODE") == "1":
    SYSTEM_PROMPT += (
        "\nDemo mode is on: search results are synthetic placeholders, not real papers. "
        "Present them as usual and mention once, briefly, that they are demo data."
    )


MCP_SERVERS = {
    "scopus": {
        "command": sys.executable,           # the venv's python
        "args": ["-m", "server.mcp_server"],  # same as your manual tests
        "transport": "stdio",
        "env": dict(os.environ),             # pass DEMO_MODE and API keys to the server
    }
}

MODEL = "claude-sonnet-5-5"

def make_model():
    return ChatAnthropic(model=MODEL)

async def build_agent():
    client = MultiServerMCPClient(MCP_SERVERS)
    tools = await client.get_tools()  # tools/list → LangChain tools
    model = make_model().bind_tools(tools)

    async def call_model(state: MessagesState):
        response = await model.ainvoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # tool call → "tools", else → END
    graph.add_edge("tools", "agent")
    return graph.compile()


async def main():
    agent = await build_agent()
    print("Ask about research literature. Type 'quit' to exit.")
    messages = []
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        messages.append(HumanMessage(question))
        result = await agent.ainvoke({"messages": messages})

        for msg in result["messages"][len(messages):]:  # show the queries Claude wrote
            for call in getattr(msg, "tool_calls", []):
                print(f"  [tool] {call['name']}({call['args']})")

        messages = result["messages"]
        print(f"\nAgent: {messages[-1].text}")


if __name__ == "__main__":
    asyncio.run(main())
