"""LLM agent module for general purpose AI assistance."""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMAgent:
    """General purpose LLM agent for fallback and general tasks."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4") -> None:
        """Initialize the LLMAgent with LLM and system prompt."""
        self.api_key = api_key
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.1,
            api_key=SecretStr(settings.OPENAI_API_KEY),
        )

        self.system_prompt = """You are a helpful and knowledgeable AI assistant. Your role is to:
1. Provide accurate and helpful information
2. Answer questions clearly and comprehensively
3. Assist with various tasks and topics
4. Be friendly and professional
5. Admit when you don't know something
6. Suggest resources when appropriate

Always be helpful, accurate, and honest in your responses."""

    async def process(self, message: str, context: dict[str, Any] | None = None) -> str:
        """Process a message and provide a general response.

        Args:
            message: The user message to process
            context: Optional context dictionary

        Returns:
            The agent's response as a string
        """
        try:
            # Create prompt with context
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.system_prompt),
                    ("human", "Please help with this: {message}"),
                ],
            )

            # Format the prompt
            formatted_prompt = prompt.format_messages(message=message)

            # Get response from LLM
            response = await self.llm.ainvoke(formatted_prompt)

            logger.info(f"LLM agent processed message: {message[:50]}...")

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error in LLM agent: {e!s}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again."

    async def answer_question(self, question: str) -> str:
        """Answer a specific question.

        Args:
            question: The question to answer

        Returns:
            The answer as a string
        """
        try:
            answer_prompt = f"""
            Please provide a comprehensive answer to this question:

            Question: {question}

            Please:
            1. Provide a clear and accurate answer
            2. Include relevant details and context
            3. Cite sources if appropriate
            4. Be helpful and informative
            """

            response = await self.llm.ainvoke([HumanMessage(content=answer_prompt)])

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error answering question: {e!s}")
            return (
                "I'm sorry, I couldn't process your question. Please try rephrasing it."
            )

    async def provide_information(self, topic: str) -> dict[str, Any]:
        """Provide information about a specific topic.

        Args:
            topic: The topic to provide information about

        Returns:
            Dictionary containing topic information
        """
        try:
            info_prompt = f"""
            Please provide comprehensive information about: {topic}

            Please include:
            1. Definition/overview
            2. Key points
            3. Important details
            4. Related concepts
            5. Additional resources
            """

            response = await self.llm.ainvoke([HumanMessage(content=info_prompt)])

            return {
                "topic": topic,
                "information": str(response.content),
                "source": "AI Assistant",
            }

        except Exception as e:
            logger.exception(f"Error providing information: {e!s}")
            return {
                "topic": topic,
                "information": "Sorry, I couldn't retrieve information about this topic.",
                "error": str(e),
            }

    async def summarize_text(self, text: str) -> str:
        """Summarize a given text.

        Args:
            text: The text to summarize

        Returns:
            The summary as a string
        """
        try:
            summary_prompt = f"""
            Please provide a concise summary of this text:

            {text}

            Please:
            1. Capture the main points
            2. Be concise but comprehensive
            3. Maintain accuracy
            4. Use clear language
            """

            response = await self.llm.ainvoke([HumanMessage(content=summary_prompt)])

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error summarizing text: {e!s}")
            return "Sorry, I couldn't summarize this text. Please try again."

    async def generate_suggestions(self, request: str) -> list[str]:
        """Generate suggestions based on a request.

        Args:
            request: The request for suggestions

        Returns:
            List of suggestion strings
        """
        try:
            suggestion_prompt = f"""
            Based on this request: "{request}"

            Generate 5 helpful suggestions that:
            1. Are relevant to the request
            2. Provide practical value
            3. Are actionable
            4. Cover different aspects
            5. Are specific and useful
            """

            response = await self.llm.ainvoke([HumanMessage(content=suggestion_prompt)])

            # Parse suggestions
            suggestions = [
                line.strip()
                for line in str(response.content).split("\n")
                if line.strip()
            ]

            return suggestions[:5]  # Return max 5 suggestions

        except Exception as e:
            logger.exception(f"Error generating suggestions: {e!s}")
            return [
                "Consider breaking this down into smaller steps",
                "Try approaching this from a different angle",
                "Research similar examples for guidance",
                "Seek expert advice if needed",
                "Take your time to plan this carefully",
            ]

    async def explain_concept(self, concept: str, level: str = "general") -> str:
        """Explain a concept at a specified level.

        Args:
            concept: The concept to explain
            level: Explanation level ("simple", "general", "detailed")

        Returns:
            The explanation as a string
        """
        try:
            level_instructions = {
                "simple": "Explain in simple terms that anyone can understand",
                "general": "Provide a general explanation suitable for most people",
                "detailed": "Give a detailed explanation with technical details",
            }

            instruction = level_instructions.get(level, level_instructions["general"])

            explain_prompt = f"""
            {instruction} for this concept: {concept}

            Please:
            1. Use appropriate language for the level
            2. Include examples if helpful
            3. Be clear and accurate
            4. Structure the explanation logically
            """

            response = await self.llm.ainvoke([HumanMessage(content=explain_prompt)])

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error explaining concept: {e!s}")
            return (
                f"Sorry, I couldn't explain {concept} at this time. Please try again."
            )

    async def generate_case_summary(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = "gpt-3.5-turbo"
    ) -> str:
        """Generate a case summary using OpenAI with custom parameters.

        Args:
            system_message: System prompt for the AI
            user_message: User message with case details
            temperature: Temperature for AI generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            model: Model name to use (e.g., "gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o")

        Returns:
            Generated case summary as a string
        """
        try:
            # Create a new LLM instance with custom parameters
            custom_llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
            )

            # Create messages
            messages = [
                ("system", system_message),
                ("human", user_message),
            ]

            # Create prompt
            prompt = ChatPromptTemplate.from_messages(messages)
            formatted_prompt = prompt.format_messages()

            # Get response from LLM
            response = await custom_llm.ainvoke(formatted_prompt)

            logger.info(f"Generated case summary using model: {model}")

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error generating case summary: {e!s}")
            return "Sorry, I couldn't generate the case summary at this time. Please try again."
