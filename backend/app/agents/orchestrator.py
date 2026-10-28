from langchain_core.messages import AIMessage, HumanMessage

# Temporarily disabled due to langgraph MRO conflict
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import END, StateGraph
from app.agents.engage import EngageAgent
from app.agents.llm import LLMAgent
from app.agents.resolve import ResolveAgent
from app.core.logging import get_logger

# from app.langgraph.memory import ChatMemory

logger = get_logger(__name__)


# Simple message state for temporary langgraph replacement
class SimpleMessageState:
    """Simple message state for temporary langgraph replacement."""

    def __init__(self, messages: list | None = None, next_agent: str | None = None):
        self.messages = messages or []
        self.next_agent = next_agent


class AgentOrchestrator:
    """Orchestrates multiple AI agents for different types of requests."""

    def __init__(self) -> None:
        self.resolve_agent = ResolveAgent()
        self.engage_agent = EngageAgent()
        self.llm_agent = LLMAgent()
        # Temporarily disabled langgraph functionality
        # self.memory = ChatMemory()
        # self.graph = self._build_graph()
        self.sessions: dict[str, list] = {}

    # Temporarily disabled due to langgraph MRO conflict
    # def _build_graph(self) -> StateGraph:
    #     """Build the LangGraph workflow."""
    #     workflow = StateGraph(ChatMemory)
    #
    #     # Add nodes
    #     workflow.add_node("classify", self._classify_message)
    #     workflow.add_node("resolve", self._resolve_task)
    #     workflow.add_node("engage", self._engage_user)
    #     workflow.add_node("llm", self._llm_fallback)
    #
    #     # Add edges
    #     workflow.add_edge("classify", "resolve")
    #     workflow.add_edge("classify", "engage")
    #     workflow.add_edge("classify", "llm")
    #     workflow.add_edge("resolve", END)
    #     workflow.add_edge("engage", END)
    #     workflow.add_edge("llm", END)
    #
    #     # Set entry point
    #     workflow.set_entry_point("classify")
    #
    #     return workflow.compile(checkpointer=MemorySaver())

    def _classify_message(self, message: str) -> str:
        """Classify the message to determine which agent should handle it."""
        # Simple classification logic (can be enhanced with ML)
        message_lower = message.lower()

        if any(
            keyword in message_lower
            for keyword in ["problem", "issue", "solve", "fix", "resolve"]
        ):
            return "resolve"
        elif any(
            keyword in message_lower
            for keyword in ["hello", "hi", "how are you", "conversation"]
        ):
            return "engage"
        else:
            return "llm"

    async def _resolve_task(self, message: str) -> str:
        """Handle problem resolution tasks."""
        return await self.resolve_agent.process(message)

    async def _engage_user(self, message: str) -> str:
        """Handle user engagement and conversation."""
        return await self.engage_agent.process(message)

    async def _llm_fallback(self, message: str) -> str:
        """Handle general LLM tasks."""
        return await self.llm_agent.process(message)

    async def process_message(
        self,
        message: str,
        session_id: str

    ) -> str:
        """Process a message through the appropriate agent."""
        try:
            # Get or create session history
            if session_id not in self.sessions:
                self.sessions[session_id] = []

            # Add user message to history
            self.sessions[session_id].append(HumanMessage(content=message))

            # Classify message to determine which agent to use
            agent_type = self._classify_message(message)

            # Process with appropriate agent
            if agent_type == "resolve":
                response = await self._resolve_task(message)
            elif agent_type == "engage":
                response = await self._engage_user(message)
            else:
                response = await self._llm_fallback(message)

            # Add AI response to history
            self.sessions[session_id].append(AIMessage(content=response))

            logger.info(
                f"Processed message for session {session_id} with agent {agent_type}",
            )

            return response

        except Exception as e:
            logger.exception(f"Error processing message: {e!s}")
            return "I'm sorry, I encountered an error processing your message. Please try again."

    async def get_session_history(self, session_id: str) -> list:
        """Get conversation history for a session."""
        try:
            return self.sessions.get(session_id, [])
        except Exception as e:
            logger.exception(f"Error getting session history: {e!s}")
            return []

    async def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            return True
        except Exception as e:
            logger.exception(f"Error clearing session: {e!s}")
            return False
