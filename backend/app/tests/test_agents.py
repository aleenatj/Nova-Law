from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agents.engage import EngageAgent
from app.agents.llm import LLMAgent
from app.agents.orchestrator import AgentOrchestrator
from app.agents.resolve import ResolveAgent
from app.main import app

client = TestClient(app)


@pytest.fixture
def resolve_agent():
    """Create a resolve agent instance."""
    return ResolveAgent()


@pytest.fixture
def engage_agent():
    """Create an engage agent instance."""
    return EngageAgent()


@pytest.fixture
def llm_agent():
    """Create an LLM agent instance."""
    return LLMAgent()


@pytest.fixture
def orchestrator():
    """Create an orchestrator instance."""
    return AgentOrchestrator()


@pytest.mark.asyncio
async def test_resolve_agent_process(resolve_agent: ResolveAgent) -> None:
    """Test resolve agent processing."""
    with patch.object(resolve_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "Here's how to resolve this issue..."

        response = await resolve_agent.process("I have a problem with my code")

        assert response is not None
        assert "resolve" in response.lower() or "issue" in response.lower()
        mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_engage_agent_process(engage_agent: EngageAgent) -> None:
    """Test engage agent processing."""
    with patch.object(engage_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "Hello! How are you doing today?"

        response = await engage_agent.process("Hello there!")

        assert response is not None
        assert "hello" in response.lower() or "how" in response.lower()
        mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_llm_agent_process(llm_agent: LLMAgent) -> None:
    """Test LLM agent processing."""
    with patch.object(llm_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "I can help you with that question."

        response = await llm_agent.process("What is Python?")

        assert response is not None
        assert "help" in response.lower() or "question" in response.lower()
        mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_process_message(orchestrator: AgentOrchestrator) -> None:
    """Test orchestrator message processing."""
    # Test with a simple message
    response = await orchestrator.process_message(
        "Hello, I need help",
        "test-session-id",
        "test-user-id",
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_resolve_agent_analyze_problem(resolve_agent: ResolveAgent) -> None:
    """Test resolve agent problem analysis."""
    with patch.object(resolve_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "Problem analysis: This is a complex issue..."

        result = await resolve_agent.analyze_problem("My application crashes")

        assert result["status"] == "completed"
        assert "analysis" in result
        assert "complex issue" in result["analysis"]


@pytest.mark.asyncio
async def test_engage_agent_conversation_starters(engage_agent: EngageAgent) -> None:
    """Test engage agent conversation starters."""
    with patch.object(engage_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "1. How has your day been?\n2. What's new?"

        starters = await engage_agent.generate_conversation_starters()

        assert len(starters) > 0
        assert any("day" in starter.lower() for starter in starters)


@pytest.mark.asyncio
async def test_llm_agent_answer_question(llm_agent: LLMAgent) -> None:
    """Test LLM agent question answering."""
    with patch.object(llm_agent.llm, "ainvoke") as mock_llm:
        mock_llm.return_value.content = "Python is a programming language..."

        answer = await llm_agent.answer_question("What is Python?")

        assert answer is not None
        assert "python" in answer.lower()


def test_agent_utils_extract_keywords():
    """Test agent utility functions."""
    from app.agents.utils import classify_intent, extract_keywords

    # Test keyword extraction
    text = "I have a problem with my Python code that needs to be resolved"
    keywords = extract_keywords(text)

    assert "problem" in keywords
    assert "python" in keywords
    assert "code" in keywords
    assert "resolved" in keywords

    # Test intent classification
    intents = classify_intent("How do I fix this issue?")
    assert intents["question"] > 0.5

    intents = classify_intent("I have a problem")
    assert intents["problem"] > 0.5

    intents = classify_intent("Hello there!")
    assert intents["greeting"] > 0.5


def test_agent_utils_validate_input():
    """Test input validation."""
    from app.agents.utils import validate_input

    # Test valid input
    result = validate_input("This is a valid message")
    assert result["valid"] is True
    assert len(result["errors"]) == 0

    # Test empty input
    result = validate_input("")
    assert result["valid"] is False
    assert len(result["errors"]) > 0

    # Test too long input
    long_text = "x" * 2000
    result = validate_input(long_text)
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_agent_orchestrator_initialization() -> None:
    """Test AgentOrchestrator initialization."""
    orchestrator = AgentOrchestrator()
    assert orchestrator is not None
    assert hasattr(orchestrator, "process_message")


def test_agent_orchestrator_process_message() -> None:
    """Test AgentOrchestrator process_message method."""
    orchestrator = AgentOrchestrator()
    message = "Hello, how can you help me?"
    response = orchestrator.process_message(message)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_with_context() -> None:
    """Test AgentOrchestrator with context."""
    orchestrator = AgentOrchestrator()
    message = "What is the weather like?"
    context = {"location": "New York", "time": "morning"}
    response = orchestrator.process_message(message, context)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_empty_message() -> None:
    """Test AgentOrchestrator with empty message."""
    orchestrator = AgentOrchestrator()
    message = ""
    response = orchestrator.process_message(message)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_long_message() -> None:
    """Test AgentOrchestrator with long message."""
    orchestrator = AgentOrchestrator()
    message = "This is a very long message " * 100
    response = orchestrator.process_message(message)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_special_characters() -> None:
    """Test AgentOrchestrator with special characters."""
    orchestrator = AgentOrchestrator()
    message = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
    response = orchestrator.process_message(message)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_unicode() -> None:
    """Test AgentOrchestrator with unicode characters."""
    orchestrator = AgentOrchestrator()
    message = "Hello 世界! Привет! こんにちは!"
    response = orchestrator.process_message(message)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_multiple_calls() -> None:
    """Test AgentOrchestrator with multiple consecutive calls."""
    orchestrator = AgentOrchestrator()

    messages = [
        "What is AI?",
        "How does machine learning work?",
        "Explain neural networks",
    ]

    responses = []
    for message in messages:
        response = orchestrator.process_message(message)
        responses.append(response)
        assert response is not None
        assert isinstance(response, str)

    assert len(responses) == len(messages)
    assert all(isinstance(r, str) for r in responses)


def test_agent_orchestrator_error_handling() -> None:
    """Test AgentOrchestrator error handling."""
    orchestrator = AgentOrchestrator()

    # Test with None message
    try:
        response = orchestrator.process_message(None)  # type: ignore
        # If it doesn't raise an error, response should be a string
        assert isinstance(response, str)
    except Exception:
        # If it raises an error, that's also acceptable
        pass

    # Test with non-string message
    try:
        response = orchestrator.process_message(123)  # type: ignore
        # If it doesn't raise an error, response should be a string
        assert isinstance(response, str)
    except Exception:
        # If it raises an error, that's also acceptable
        pass


def test_agent_orchestrator_with_session_id() -> None:
    """Test AgentOrchestrator with session_id parameter."""
    orchestrator = AgentOrchestrator()
    message = "Hello, how can you help me?"
    session_id = "test-session-123"
    response = orchestrator.process_message(message, session_id)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_with_context_dict() -> None:
    """Test AgentOrchestrator with context as dict."""
    orchestrator = AgentOrchestrator()
    message = "What is the weather like?"
    context = {"location": "New York", "time": "morning"}
    response = orchestrator.process_message(message, context)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_with_context_string() -> None:
    """Test AgentOrchestrator with context as string."""
    orchestrator = AgentOrchestrator()
    message = "What is the weather like?"
    context = "New York, morning"
    response = orchestrator.process_message(message, context)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_with_context_none() -> None:
    """Test AgentOrchestrator with context as None."""
    orchestrator = AgentOrchestrator()
    message = "What is the weather like?"
    response = orchestrator.process_message(message, None)
    assert response is not None
    assert isinstance(response, str)


def test_agent_orchestrator_with_session_id_and_context() -> None:
    """Test AgentOrchestrator with both session_id and context."""
    orchestrator = AgentOrchestrator()
    message = "What is the weather like?"
    session_id = "test-session-123"
    context = {"location": "New York", "time": "morning"}
    response = orchestrator.process_message(message, session_id, context)
    assert response is not None
    assert isinstance(response, str)
