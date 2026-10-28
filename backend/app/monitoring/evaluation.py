from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentEvaluator:
    """Evaluator for agent outputs and system performance."""

    def __init__(self) -> None:
        self.evaluation_criteria = {
            "relevance": 0.0,
            "accuracy": 0.0,
            "completeness": 0.0,
            "helpfulness": 0.0,
            "response_time": 0.0,
        }

    def evaluate_response_relevance(
        self,
        user_input: str,
        agent_response: str,
    ) -> float:
        """Evaluate how relevant the agent response is to the user input."""
        # Simple keyword matching (can be enhanced with semantic similarity)
        user_words = set(user_input.lower().split())
        response_words = set(agent_response.lower().split())

        if not user_words:
            return 0.0

        common_words = user_words.intersection(response_words)
        relevance_score = len(common_words) / len(user_words)

        return min(relevance_score, 1.0)

    def evaluate_response_accuracy(self, response: str) -> float:
        """Evaluate the accuracy of the response."""
        # Check for common accuracy indicators
        accuracy_indicators = [
            "i'm not sure",
            "i don't know",
            "i cannot",
            "i'm unable",
            "error",
            "sorry",
        ]

        response_lower = response.lower()
        accuracy_score = 1.0

        for indicator in accuracy_indicators:
            if indicator in response_lower:
                accuracy_score -= 0.2

        return max(accuracy_score, 0.0)

    def evaluate_response_completeness(self, response: str) -> float:
        """Evaluate the completeness of the response."""
        # Check response length and structure
        if len(response.strip()) < 10:
            return 0.0

        # Check for structured responses
        has_structure = any(
            [
                len(response.split("\n")) > 2,
                "•" in response or "-" in response,
                any(
                    word in response.lower()
                    for word in ["first", "second", "third", "finally"]
                ),
            ],
        )

        completeness_score = 0.5  # Base score

        if has_structure:
            completeness_score += 0.3

        if len(response) > 100:
            completeness_score += 0.2

        return min(completeness_score, 1.0)

    def evaluate_response_helpfulness(self, response: str) -> float:
        """Evaluate how helpful the response is."""
        helpful_indicators = [
            "here's how",
            "you can",
            "try this",
            "solution",
            "steps",
            "recommend",
            "suggest",
        ]

        response_lower = response.lower()
        helpfulness_score = 0.5  # Base score

        for indicator in helpful_indicators:
            if indicator in response_lower:
                helpfulness_score += 0.1

        return min(helpfulness_score, 1.0)

    def evaluate_response_time(self, response_time: float) -> float:
        """Evaluate response time performance."""
        if response_time < 1.0:
            return 1.0
        elif response_time < 3.0:
            return 0.8
        elif response_time < 5.0:
            return 0.6
        elif response_time < 10.0:
            return 0.4
        else:
            return 0.2

    def evaluate_agent_response(
        self,
        user_input: str,
        agent_response: str,
        response_time: float,
        agent_name: str,
    ) -> dict[str, Any]:
        """Comprehensive evaluation of agent response."""
        try:
            evaluation = {
                "agent_name": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_input": user_input,
                "agent_response": agent_response,
                "response_time": response_time,
                "scores": {
                    "relevance": self.evaluate_response_relevance(
                        user_input,
                        agent_response,
                    ),
                    "accuracy": self.evaluate_response_accuracy(agent_response),
                    "completeness": self.evaluate_response_completeness(agent_response),
                    "helpfulness": self.evaluate_response_helpfulness(agent_response),
                    "response_time": self.evaluate_response_time(response_time),
                },
            }

            # Calculate overall score
            scores = evaluation["scores"]
            if isinstance(scores, dict):
                overall_score = sum(scores.values()) / len(scores)
            else:
                overall_score = 0.0
            evaluation["overall_score"] = overall_score

            # Add evaluation level
            if overall_score >= 0.8:
                evaluation["level"] = "excellent"
            elif overall_score >= 0.6:
                evaluation["level"] = "good"
            elif overall_score >= 0.4:
                evaluation["level"] = "fair"
            else:
                evaluation["level"] = "poor"

            logger.info(
                f"Agent evaluation for {agent_name}: {overall_score:.2f} ({evaluation['level']})",
            )

            return evaluation

        except Exception as e:
            logger.exception(f"Error evaluating agent response: {e!s}")
            return {
                "agent_name": agent_name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def evaluate_conversation_flow(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Evaluate the flow of a conversation."""
        if len(messages) < 2:
            return {"flow_score": 0.0, "issues": ["Insufficient messages"]}

        flow_score = 1.0
        issues = []

        # Check for conversation continuity
        for i in range(1, len(messages)):
            # prev_msg = messages[i - 1]
            curr_msg = messages[i]

            # Check if responses are too short
            if (
                curr_msg.get("role") == "assistant"
                and len(curr_msg.get("content", "")) < 10
            ):
                flow_score -= 0.1
                issues.append(f"Short response at message {i}")

            # Check for repeated responses
            if i > 1:
                prev_prev_msg = messages[i - 2]
                if prev_prev_msg.get("content") == curr_msg.get(
                    "content",
                ) and prev_prev_msg.get("role") == curr_msg.get("role"):
                    flow_score -= 0.2
                    issues.append(f"Repeated response at message {i}")

        return {
            "flow_score": max(flow_score, 0.0),
            "issues": issues,
            "message_count": len(messages),
        }

    def generate_evaluation_report(
        self,
        evaluations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate a comprehensive evaluation report."""
        if not evaluations:
            return {"error": "No evaluations provided"}

        # Calculate aggregate metrics
        overall_scores = [
            e.get("overall_score", 0) for e in evaluations if "overall_score" in e
        ]
        response_times = [
            e.get("response_time", 0) for e in evaluations if "response_time" in e
        ]

        report: dict[str, Any] = {
            "total_evaluations": len(evaluations),
            "average_overall_score": (
                sum(overall_scores) / len(overall_scores) if overall_scores else 0
            ),
            "average_response_time": (
                sum(response_times) / len(response_times) if response_times else 0
            ),
            "score_distribution": {
                "excellent": len(
                    [e for e in evaluations if e.get("level") == "excellent"],
                ),
                "good": len([e for e in evaluations if e.get("level") == "good"]),
                "fair": len([e for e in evaluations if e.get("level") == "fair"]),
                "poor": len([e for e in evaluations if e.get("level") == "poor"]),
            },
            "agent_performance": {},
        }

        # Group by agent
        agent_groups: dict[str, list[dict[str, Any]]] = {}
        for eval in evaluations:
            agent_name = eval.get("agent_name", "unknown")
            if agent_name not in agent_groups:
                agent_groups[agent_name] = []
            agent_groups[agent_name].append(eval)

        # Calculate agent-specific metrics
        for agent_name, agent_evals in agent_groups.items():
            agent_scores = [
                e.get("overall_score", 0) for e in agent_evals if "overall_score" in e
            ]
            agent_times = [
                e.get("response_time", 0) for e in agent_evals if "response_time" in e
            ]

            report["agent_performance"][agent_name] = {
                "evaluation_count": len(agent_evals),
                "average_score": (
                    sum(agent_scores) / len(agent_scores) if agent_scores else 0
                ),
                "average_response_time": (
                    sum(agent_times) / len(agent_times) if agent_times else 0
                ),
                "best_score": max(agent_scores) if agent_scores else 0,
                "worst_score": min(agent_scores) if agent_scores else 0,
            }

        return report


# Global evaluator instance
agent_evaluator = AgentEvaluator()
