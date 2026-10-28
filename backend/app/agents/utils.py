import json
import re
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_keywords(text: str) -> list[str]:
    """Extract important keywords from text."""
    # Remove common words and punctuation
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
    }

    # Clean text
    text = re.sub(r"[^\w\s]", "", text.lower())
    words = text.split()

    # Filter out stop words and short words
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords[:10]  # Return top 10 keywords


def classify_intent(text: str) -> dict[str, float]:
    """Classify the intent of a message."""
    text_lower = text.lower()

    intents = {
        "question": 0.0,
        "problem": 0.0,
        "greeting": 0.0,
        "request": 0.0,
        "statement": 0.0,
    }

    # Question detection
    if any(
        word in text_lower
        for word in ["what", "how", "why", "when", "where", "who", "which"]
    ):
        intents["question"] += 0.8
    if "?" in text:
        intents["question"] += 0.2

    # Problem detection
    if any(
        word in text_lower
        for word in ["problem", "issue", "error", "fix", "solve", "help", "trouble"]
    ):
        intents["problem"] += 0.8

    # Greeting detection
    if any(
        word in text_lower
        for word in [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
    ):
        intents["greeting"] += 0.9

    # Request detection
    if any(
        word in text_lower
        for word in ["please", "can you", "could you", "would you", "need", "want"]
    ):
        intents["request"] += 0.7

    # Default to statement if no other intent is strong
    if max(intents.values()) < 0.3:
        intents["statement"] = 0.8

    return intents


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract named entities from text."""
    entities: dict[str, list[str]] = {
        "dates": [],
        "numbers": [],
        "urls": [],
        "emails": [],
    }

    # Extract dates
    date_patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["dates"].extend(matches)

    # Extract numbers
    number_pattern = r"\b\d+(?:\.\d+)?\b"
    entities["numbers"] = re.findall(number_pattern, text)

    # Extract URLs
    url_pattern = r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?"
    entities["urls"] = re.findall(url_pattern, text)

    # Extract emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    entities["emails"] = re.findall(email_pattern, text)

    return entities


def format_response(response: str, format_type: str = "text") -> str:
    """Format response based on type."""
    if format_type == "markdown":
        # Convert to markdown if needed
        return response
    elif format_type == "json":
        # Try to format as JSON
        try:
            return json.dumps(json.loads(response), indent=2)
        except Exception:
            return response
    else:
        return response


def validate_input(text: str, max_length: int = 1000) -> dict[str, Any]:
    """Validate input text."""
    validation: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    if not text or not text.strip():
        validation["valid"] = False
        validation["errors"].append("Text cannot be empty")

    if len(text) > max_length:
        validation["valid"] = False
        validation["errors"].append(
            f"Text exceeds maximum length of {max_length} characters",
        )

    if len(text) < 3:
        validation["warnings"].append("Text is very short")

    return validation


def create_context_summary(
    messages: list[dict[str, Any]],
    max_messages: int = 10,
) -> str:
    """Create a summary of conversation context."""
    if not messages:
        return "No previous context available."

    # Take the most recent messages
    recent_messages = messages[-max_messages:]

    summary_parts = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:100]  # Truncate long messages
        summary_parts.append(f"{role}: {content}")

    return " | ".join(summary_parts)


def sanitize_text(text: str) -> str:
    """Sanitize text for safe processing."""
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Trim whitespace
    text = text.strip()

    return text


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def log_agent_activity(
    agent_name: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Log agent activity for monitoring."""
    log_data = {
        "agent": agent_name,
        "action": action,
        "timestamp": get_timestamp(),
        "details": details or {},
    }

    logger.info(f"Agent activity: {json.dumps(log_data)}")
