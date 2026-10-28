from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.engage import EngageAgent
from app.agents.llm import LLMAgent
from app.agents.orchestrator import AgentOrchestrator
from app.agents.resolve import ResolveAgent
from app.db.models import User
from app.schemas.v1.auth import AgentStatus
from app.utils.dependencies import get_current_active_user

router = APIRouter()


class AgentInfo:
    """Agent information model."""
    def __init__(self, id: str, name: str, description: str, status: str, config: dict[str, Any]):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.config = config


@router.get("/agents", response_model=dict[str, AgentInfo])
async def get_agents(current_user: User = Depends(get_current_active_user)) -> dict[str, AgentInfo]:
    """Get list of available agents."""
    return {
        "resolve": AgentInfo(
            id="resolve",
            name="Resolve Agent",
            description="Specialized in problem resolution and analysis",
            status="active",
            config={},
        ),
        "engage": AgentInfo(
            id="engage",
            name="Engage Agent",
            description="Handles user engagement and conversation",
            status="active",
            config={},
        ),
        "llm": AgentInfo(
            id="llm",
            name="LLM Agent",
            description="General purpose LLM agent",
            status="active",
            config={},
        ),
    }


@router.get("/agents/{agent_id}", response_model=dict[str, Any])
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Get specific agent details."""
    agents = {
        "resolve": {
            "id": "resolve",
            "name": "Resolve Agent",
            "description": "Handles problem resolution and analysis",
            "status": "active",
            "config": {},
        },
        "engage": {
            "id": "engage",
            "name": "Engage Agent",
            "description": "Handles user engagement and conversation",
            "status": "active",
            "config": {},
        },
        "llm": {
            "id": "llm",
            "name": "LLM Agent",
            "description": "General purpose LLM agent",
            "status": "active",
            "config": {},
        },
    }

    if agent_id not in agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agents[agent_id]


@router.put("/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: str,
    config_update: dict,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Update agent configuration."""
    # TODO: Implement agent configuration update logic
    return {"message": f"Agent {agent_id} configuration updated"}


@router.post("/agents/{agent_id}/test")
async def test_agent(
    agent_id: str,
    test_message: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Test a specific agent with a message."""
    if agent_id == "resolve":
        resolve_agent = ResolveAgent()
        response = await resolve_agent.process(test_message)
    elif agent_id == "engage":
        engage_agent = EngageAgent()
        response = await engage_agent.process(test_message)
    elif agent_id == "llm":
        llm_agent = LLMAgent()
        response = await llm_agent.process(test_message)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return {"agent_id": agent_id, "input": test_message, "response": response}


@router.get("/agents/status", response_model=dict[str, AgentStatus])
async def get_agents_status(current_user: User = Depends(get_current_active_user)) -> dict[str, AgentStatus]:
    """Get status of all agents."""
    return {
        "resolve": {
            "status": "active",
            "message_count": 100,
            "last_activity": "2024-01-01T00:00:00Z",
        },
        "engage": {
            "status": "active",
            "message_count": 150,
            "last_activity": "2024-01-01T00:00:00Z",
        },
        "llm": {
            "status": "active",
            "message_count": 200,
            "last_activity": "2024-01-01T00:00:00Z",
        },
    }


@router.post("/agents/orchestrator/route")
async def route_message(
    message: str,
    session_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Route a message through the orchestrator."""
    response = await AgentOrchestrator().process_message(
        message=message,
        session_id=session_id,
    )

    return {"message": message, "response": response, "routed_to": "orchestrator"}
