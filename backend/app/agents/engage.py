"""Engage agent module for user engagement and conversation handling."""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EngageAgent:
    """Agent specialized in user engagement and conversation."""

    def __init__(self) -> None:
        """Initialize the EngageAgent with LLM and system prompt."""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,
            api_key=SecretStr(settings.OPENAI_API_KEY),
        )

        self.system_prompt = """You are a friendly and engaging conversational AI. Your role is to:
1. Be warm, welcoming, and personable
2. Show genuine interest in the user
3. Ask thoughtful follow-up questions
4. Remember context from the conversation
5. Provide emotional support when appropriate
6. Keep conversations engaging and natural

Always be empathetic, supportive, and conversational. Focus on building rapport and maintaining engaging dialogue."""

    async def process(self, message: str, context: dict[str, Any] | None = None) -> str:
        """Process a message and provide engaging conversation.

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
                    ("human", "Please engage with this message: {message}"),
                ],
            )

            # Format the prompt
            formatted_prompt = prompt.format_messages(message=message)

            # Get response from LLM
            response = await self.llm.ainvoke(formatted_prompt)

            logger.info(f"Engage agent processed message: {message[:50]}...")

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error in engage agent: {e!s}")
            return "I'm sorry, I'm having trouble engaging with you right now. Let's try again!"

    async def generate_conversation_starters(
        self,
        user_context: dict[str, Any] | None = None,
    ) -> list[str]:
        """Generate conversation starters based on context.

        Args:
            user_context: Optional user context dictionary

        Returns:
            List of conversation starter strings
        """
        try:
            context_info = ""
            if user_context:
                context_info = f"User context: {user_context}"

            starter_prompt = f"""
            Generate 5 engaging conversation starters. {context_info}

            Make them:
            1. Open-ended and interesting
            2. Relevant to the context if provided
            3. Appropriate for a professional but friendly conversation
            4. Designed to encourage thoughtful responses
            """

            response = await self.llm.ainvoke([HumanMessage(content=starter_prompt)])

            # Parse the response into a list
            starters = [
                line.strip()
                for line in str(response.content).split("\n")
                if line.strip()
            ]

            return starters[:5]  # Return max 5 starters

        except Exception as e:
            logger.exception(f"Error generating conversation starters: {e!s}")
            return [
                "How has your day been so far?",
                "What's something interesting you've learned recently?",
                "Is there anything you'd like to discuss or explore?",
                "What are your thoughts on AI and technology?",
                "How can I help you today?",
            ]

    async def provide_emotional_support(self, user_message: str) -> str:
        """Provide emotional support and empathy.

        Args:
            user_message: The user's message requiring emotional support

        Returns:
            Supportive response string
        """
        try:
            support_prompt = f"""
            The user has shared: "{user_message}"

            Provide empathetic, supportive, and caring response. Be:
            1. Understanding and validating
            2. Encouraging and positive
            3. Professional but warm
            4. Helpful without being preachy
            5. Focused on emotional support
            """

            response = await self.llm.ainvoke([HumanMessage(content=support_prompt)])

            logger.info("Provided emotional support response")

            return str(response.content)

        except Exception as e:
            logger.exception(f"Error providing emotional support: {e!s}")
            return "I understand this might be difficult. I'm here to listen and support you."

    async def ask_follow_up_questions(
        self, conversation_history: list[str]
    ) -> list[str]:
        """Generate follow-up questions based on conversation history.

        Args:
            conversation_history: List of previous conversation messages

        Returns:
            List of follow-up question strings
        """
        try:
            # Create context from recent messages
            recent_context = "\n".join(conversation_history[-3:])  # Last 3 messages

            follow_up_prompt = f"""
            Based on this conversation context:
            {recent_context}

            Generate 3 thoughtful follow-up questions that:
            1. Build on what was discussed
            2. Show genuine interest
            3. Encourage deeper conversation
            4. Are relevant and timely
            """

            response = await self.llm.ainvoke([HumanMessage(content=follow_up_prompt)])

            # Parse questions
            questions = [
                line.strip()
                for line in str(response.content).split("\n")
                if line.strip()
            ]

            return questions[:3]  # Return max 3 questions

        except Exception as e:
            logger.exception(f"Error generating follow-up questions: {e!s}")
            return [
                "Could you tell me more about that?",
                "What are your thoughts on this?",
                "How does that make you feel?",
            ]

    async def detect_engagement_level(self, message: str) -> int:
        """Detect the engagement level of a user message.

        Args:
            message: The user message to analyze

        Returns:
            Engagement level (1-5, where 5 is highly engaged)
        """
        try:
            engagement_prompt = f"""
            Analyze this message for engagement level: "{message}"

            Rate from 1-5:
            1: Very low engagement (one word, generic)
            2: Low engagement (short, basic)
            3: Moderate engagement (some detail)
            4: High engagement (detailed, personal)
            5: Very high engagement (very detailed, emotional, personal)

            Return only the number.
            """

            response = await self.llm.ainvoke([HumanMessage(content=engagement_prompt)])

            # Try to parse the response as an integer
            try:
                level = int(str(response.content).strip())
                return max(1, min(5, level))  # Ensure it's between 1-5
            except ValueError:
                return 3  # Default to moderate engagement

        except Exception as e:
            logger.exception(f"Error detecting engagement level: {e!s}")
            return 3  # Default to moderate engagement
