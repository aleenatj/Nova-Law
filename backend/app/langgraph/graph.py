from typing import Any, TypedDict

from langgraph.graph import StateGraph

from app.agents.engage import EngageAgent
from app.agents.llm import LLMAgent
from app.agents.resolve import ResolveAgent


class AgentState(TypedDict):
    """State for agent orchestration."""
    messages: list[Any]


def create_agent_graph() -> StateGraph[AgentState]:
    """Create the agent orchestration graph."""
    # Initialize agents
    resolve_agent = ResolveAgent()
    engage_agent = EngageAgent()
    llm_agent = LLMAgent()

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("resolve", resolve_agent.process)
    workflow.add_node("engage", engage_agent.process)
    workflow.add_node("llm", llm_agent.process)

    # Add edges
    workflow.add_edge("resolve", "engage")
    workflow.add_edge("engage", "llm")
    workflow.add_edge("llm", "end")

    # Set entry point
    workflow.set_entry_point("resolve")

    return workflow
