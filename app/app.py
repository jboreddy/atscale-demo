"""Customer 360 Chat Application — Streamlit UI for the C360 Agent."""

import sys
import os

# Add agent module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

import streamlit as st
from agent import invoke_agent

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Customer 360 Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Customer 360")
    st.markdown("---")
    st.markdown("""
    **Powered by:**
    - AtScale Semantic Layer
    - Amazon Bedrock (Claude Sonnet)
    - Strands Agents
    
    **Data Sources:**
    - 🟢 Aurora PostgreSQL (Customers)
    - 🔵 Amazon Redshift (Products/Purchases)
    """)

    st.markdown("---")
    st.markdown("**Sample Questions:**")
    sample_questions = [
        "List 10 customers and their state",
        "Top 10 products by units sold",
        "Who are the top spenders in Wisconsin?",
        "Revenue by product category",
        "How many big spenders per state?",
        "Average order value by state",
        "Which vendors have the most products?",
    ]

    for q in sample_questions:
        if st.button(q, key=f"sample_{q[:20]}", use_container_width=True):
            st.session_state.pending_question = q

# ─────────────────────────────────────────────
# Main Chat Interface
# ─────────────────────────────────────────────
st.title("💬 Customer 360 Analytics Assistant")
st.caption("Ask questions about customers, products, and purchases in natural language.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show expandable sections for assistant messages
        if message["role"] == "assistant" and "metadata" in message:
            metadata = message["metadata"]

            # SQL transparency
            if metadata.get("sql"):
                with st.expander("🔎 View Generated SQL"):
                    st.code(metadata["sql"], language="sql")

            # Data sources
            if metadata.get("sources"):
                sources_str = " | ".join(
                    [f"{'🟢' if 'Aurora' in s else '🔵'} {s}" for s in metadata["sources"]]
                )
                st.caption(f"Sources: {sources_str}")

# Handle pending question from sidebar
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Querying semantic layer..."):
            result = invoke_agent(question)

        st.markdown(result["answer"])

        metadata = {
            "sql": result.get("tool_calls", [{}])[0].get("input", {}).get("sql", "") if result.get("tool_calls") else "",
            "sources": result.get("sources", []),
        }

        if metadata["sql"]:
            with st.expander("🔎 View Generated SQL"):
                st.code(metadata["sql"], language="sql")

        if metadata["sources"]:
            sources_str = " | ".join(
                [f"{'🟢' if 'Aurora' in s else '🔵'} {s}" for s in metadata["sources"]]
            )
            st.caption(f"Sources: {sources_str}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "metadata": metadata,
        })

    st.rerun()

# Chat input
if prompt := st.chat_input("Ask a question about your customers..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Querying semantic layer..."):
            result = invoke_agent(prompt)

        st.markdown(result["answer"])

        metadata = {
            "sql": result.get("tool_calls", [{}])[0].get("input", {}).get("sql", "") if result.get("tool_calls") else "",
            "sources": result.get("sources", []),
        }

        if metadata["sql"]:
            with st.expander("🔎 View Generated SQL"):
                st.code(metadata["sql"], language="sql")

        if metadata["sources"]:
            sources_str = " | ".join(
                [f"{'🟢' if 'Aurora' in s else '🔵'} {s}" for s in metadata["sources"]]
            )
            st.caption(f"Sources: {sources_str}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "metadata": metadata,
        })
