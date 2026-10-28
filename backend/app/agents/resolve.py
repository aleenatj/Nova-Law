from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResolveAgent:
    """Agent specialized in problem resolution and analysis."""

    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=SecretStr(settings.OPENAI_API_KEY),
        )

        self.system_prompt = """You are a problem resolution specialist. Your role is to:
1. Analyze problems systematically
2. Break down complex issues into manageable parts
3. Provide step-by-step solutions
4. Identify root causes
5. Suggest preventive measures

Always be thorough, analytical, and solution-oriented. Focus on practical, actionable advice."""

    async def process(self, message: str, context: dict[str, Any] | None = None) -> str:
        """Process a message and provide problem resolution."""
        try:
            # Create prompt with context
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system_prompt),
                    ("human", "Please analyze and resolve this issue: {message}"),
                ],
            )

            # Format the prompt
            formatted_prompt = prompt.format_messages(message=message)

            # Get response from LLM
            response = await self.llm.ainvoke(formatted_prompt)

            logger.info(f"Resolve agent processed message: {message[:50]}...")

            return response.content

        except Exception as e:
            logger.exception(f"Error in resolve agent: {e!s}")
            return "I'm sorry, I encountered an error while trying to resolve this issue. Please try again or contact support."

    async def analyze_problem(self, problem_description: str) -> dict[str, Any]:
        """Perform detailed problem analysis."""
        try:
            analysis_prompt = f"""
            Please provide a detailed analysis of this problem:

            Problem: {problem_description}

            Please provide:
            1. Problem classification
            2. Root cause analysis
            3. Impact assessment
            4. Solution options
            5. Recommended approach
            6. Prevention strategies
            """

            response = await self.llm.ainvoke([HumanMessage(content=analysis_prompt)])

            return {"analysis": response.content, "status": "completed"}

        except Exception as e:
            logger.exception(f"Error in problem analysis: {e!s}")
            return {
                "analysis": "Error performing analysis",
                "status": "error",
                "error": str(e),
            }

    async def generate_solution_plan(self, problem: str) -> dict[str, Any]:
        """Generate a detailed solution plan."""
        try:
            plan_prompt = f"""
            Create a detailed solution plan for this problem:

            Problem: {problem}

            Please provide:
            1. Immediate actions (next 24 hours)
            2. Short-term solutions (next week)
            3. Long-term solutions (next month)
            4. Required resources
            5. Timeline
            6. Success metrics
            """

            response = await self.llm.ainvoke([HumanMessage(content=plan_prompt)])

            return {"plan": response.content, "status": "completed"}

        except Exception as e:
            logger.exception(f"Error generating solution plan: {e!s}")
            return {"plan": "Error generating plan", "status": "error", "error": str(e)}
