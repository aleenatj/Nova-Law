import time

from prometheus_client import Counter, Gauge, Histogram

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Agent metrics
AGENT_REQUEST_COUNT = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["agent_name", "status"],
)

AGENT_RESPONSE_TIME = Histogram(
    "agent_response_time_seconds",
    "Agent response time in seconds",
    ["agent_name"],
)

AGENT_ERROR_COUNT = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["agent_name", "error_type"],
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
)

DB_CONNECTION_COUNT = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# System metrics
ACTIVE_SESSIONS = Gauge("active_sessions_total", "Number of active chat sessions")

ACTIVE_USERS = Gauge("active_users_total", "Number of active users")

MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes")

# Custom metrics
ORCHESTRATOR_DECISIONS = Counter(
    "orchestrator_decisions_total",
    "Total orchestrator routing decisions",
    ["agent_name"],
)


class MetricsCollector:
    """Collector for application metrics."""

    def __init__(self) -> None:
        self.start_time = time.time()

    def record_request(
        self, method: str, endpoint: str, status: int, duration: float
    ) -> None:
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    def record_agent_request(
        self, agent_name: str, status: str, duration: float
    ) -> None:
        """Record agent request metrics."""
        AGENT_REQUEST_COUNT.labels(agent_name=agent_name, status=status).inc()
        AGENT_RESPONSE_TIME.labels(agent_name=agent_name).observe(duration)

    def record_agent_error(self, agent_name: str, error_type: str) -> None:
        """Record agent error metrics."""
        AGENT_ERROR_COUNT.labels(agent_name=agent_name, error_type=error_type).inc()

    def record_db_query(self, operation: str, table: str, duration: float) -> None:
        """Record database query metrics."""
        DB_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)

    def set_active_sessions(self, count: int) -> None:
        """Set active sessions count."""
        ACTIVE_SESSIONS.set(count)

    def set_active_users(self, count: int) -> None:
        """Set active users count."""
        ACTIVE_USERS.set(count)

    def set_memory_usage(self, bytes_used: int) -> None:
        """Set memory usage."""
        MEMORY_USAGE.set(bytes_used)

    def record_orchestrator_decision(self, agent_name: str) -> None:
        """Record orchestrator routing decision."""
        ORCHESTRATOR_DECISIONS.labels(agent_name=agent_name).inc()

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


# Global metrics collector instance
metrics_collector = MetricsCollector()
