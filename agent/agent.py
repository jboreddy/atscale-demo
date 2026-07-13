"""Customer 360 Agent — Strands Agent with AtScale semantic layer tool."""

import os
from strands import Agent
from tools import query_atscale, get_semantic_model_info
from prompts.system_prompt import SYSTEM_PROMPT


def create_agent() -> Agent:
    """Create and configure the Customer 360 Strands Agent."""
    
    # Determine model ID based on environment
    model_id = os.environ.get(
        "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-6-v1:0"
    )
    region = os.environ.get("AWS_REGION", "us-east-1")

    agent = Agent(
        model=f"bedrock/{model_id}",
        tools=[query_atscale, get_semantic_model_info],
        system_prompt=SYSTEM_PROMPT,
        # Agent configuration
        name="Customer360Agent",
        description="Customer 360 analytics assistant using AtScale semantic layer",
    )

    return agent


def invoke_agent(question: str, session_id: str = "default") -> dict:
    """
    Invoke the agent with a natural language question.
    
    Args:
        question: Natural language question about customer/product data
        session_id: Session identifier for conversation continuity
        
    Returns:
        dict with keys: answer, tool_calls, sources
    """
    agent = create_agent()
    
    try:
        response = agent(question)
        
        # Extract tool usage information
        tool_calls = []
        sources = set()
        
        if hasattr(response, "tool_use") and response.tool_use:
            for tc in response.tool_use:
                tool_calls.append({
                    "tool": tc.get("name", "unknown"),
                    "input": tc.get("input", {}),
                })
                # Determine sources from query content
                sql = tc.get("input", {}).get("sql", "")
                if any(kw in sql.lower() for kw in ["customer", "address", "state", "email"]):
                    sources.add("Aurora PostgreSQL")
                if any(kw in sql.lower() for kw in ["product", "purchase", "revenue", "quantity"]):
                    sources.add("Redshift")
        
        # Default to both if we can't determine
        if not sources:
            sources = {"Aurora PostgreSQL", "Redshift"}
        
        return {
            "answer": str(response),
            "tool_calls": tool_calls,
            "sources": list(sources),
            "success": True,
        }
        
    except Exception as e:
        return {
            "answer": f"I encountered an error processing your question: {str(e)}",
            "tool_calls": [],
            "sources": [],
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    # Quick test
    import sys
    
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List 5 customers and their state"
    print(f"Question: {question}\n")
    
    result = invoke_agent(question)
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")
