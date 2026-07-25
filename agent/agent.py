"""Customer 360 Agent — Strands Agent with AtScale semantic layer tool."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from strands import Agent
from strands.models import BedrockModel
from tools import query_atscale, get_semantic_model_info
from prompts.system_prompt import SYSTEM_PROMPT


def create_agent() -> Agent:
    """Create and configure the Customer 360 Strands Agent."""

    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
    region = os.environ.get("AWS_REGION", "us-east-1")

    # Use BedrockModel directly (required for inference profiles)
    model = BedrockModel(
        model_id=model_id,
        region_name=region,
    )

    agent = Agent(
        model=model,
        tools=[query_atscale, get_semantic_model_info],
        system_prompt=SYSTEM_PROMPT,
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

        return {
            "answer": str(response),
            "tool_calls": [],
            "sources": ["AtScale Semantic Layer", "Amazon Redshift"],
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
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List 5 customers and their state"
    print(f"Question: {question}\n")

    result = invoke_agent(question)
    print(f"Answer: {result['answer']}")
