"""Streamlit chat UI for the Scopus agent (layer 4)."""
import asyncio
import os

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from agent.graph import build_agent

MAX_QUESTIONS = 10  # per visitor session, to cap API spend on the hosted demo

st.set_page_config(page_title="Scopus research agent", page_icon="📚")
st.title("Scopus research agent")
st.caption(
    "Ask about research literature in plain English. The agent writes a Scopus "
    "Advanced Search query, runs it and answers with cited papers."
)

if os.environ.get("DEMO_MODE") == "1":  # NEW
    st.info(
        "**Demo mode:** Claude writes each Scopus query live, but the search results "
        "are synthetic placeholders, not real Scopus data."
    )

# Access gate: only active when ACCESS_CODE is set (on the hosted demo)
access_code = os.environ.get("ACCESS_CODE")
if access_code and not st.session_state.get("unlocked"):
    entered = st.text_input("Access code", type="password")
    if entered == access_code:
        st.session_state.unlocked = True
        st.rerun()
    if entered:
        st.error("Wrong access code.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []


async def ask(messages):
    agent = await build_agent()
    result = await agent.ainvoke({"messages": messages})
    return result["messages"]


# Redraw the conversation so far
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.text)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            for call in msg.tool_calls:  # show the queries Claude wrote
                st.caption("Scopus query")
                st.code(call["args"].get("query", ""), language=None)
            if msg.text:
                st.markdown(msg.text)

questions_asked = sum(isinstance(m, HumanMessage) for m in st.session_state.messages)
if questions_asked >= MAX_QUESTIONS:
    st.info(f"This demo is limited to {MAX_QUESTIONS} questions per visit. Thanks for trying it!")
elif question := st.chat_input("e.g. What are the most cited UK cancer papers since 2020?"):
    st.chat_message("user").write(question)
    st.session_state.messages.append(HumanMessage(question))
    try:
        with st.spinner("Searching Scopus..."):
            st.session_state.messages = asyncio.run(ask(st.session_state.messages))
    except Exception as e:
        st.session_state.messages.pop()  # drop the unanswered question
        st.error(f"Something went wrong: {e}")
    else:
        st.rerun()
