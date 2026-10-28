"""Error Monitoring and Alerting System for Nova Law AI Backend.

This module provides comprehensive error monitoring, alerting, and reporting
capabilities that integrate with the centralized error logging system.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel

from app.core.error_logging import (
    ErrorCategory,
    ErrorSeverity,
    get_error_statistics,
)


class AlertRule(BaseModel):
    """Alert rule configuration."""

    rule_id: str
    name: str
    description: str
    severity_threshold: ErrorSeverity
    error_count_threshold: int
    time_window_minutes: int
    category_filter: ErrorCategory | None = None
    enabled: bool = True


class Alert(BaseModel):
    """Alert instance."""

    alert_id: str
    rule_id: str
    rule_name: str
    severity: ErrorSeverity
    message: str
    error_count: int
    time_window_minutes: int
    category: ErrorCategory | None = None
    timestamp: datetime
    resolved: bool = False
    resolution_time: datetime | None = None


class ErrorMonitor:
    """Error monitoring and alerting system."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)
        self.alert_rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, Alert] = {}
        self.error_history: list[dict[str, Any]] = []
        self.monitoring_task: asyncio.Task | None = None
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default alert rules."""
        default_rules = [
            AlertRule(
                rule_id="critical_errors",
                name="Critical Error Alert",
                description="Alert when critical errors occur",
                severity_threshold=ErrorSeverity.CRITICAL,
                error_count_threshold=1,
                time_window_minutes=5,
            ),
            AlertRule(
                rule_id="high_severity_spike",
                name="High Severity Error Spike",
                description="Alert when high severity errors spike",
                severity_threshold=ErrorSeverity.HIGH,
                error_count_threshold=5,
                time_window_minutes=10,
            ),
            AlertRule(
                rule_id="database_errors",
                name="Database Error Alert",
                description="Alert when database errors occur frequently",
                severity_threshold=ErrorSeverity.HIGH,
                error_count_threshold=3,
                time_window_minutes=5,
                category_filter=ErrorCategory.DATABASE,
            ),
            AlertRule(
                rule_id="authentication_errors",
                name="Authentication Error Alert",
                description="Alert when authentication errors spike",
                severity_threshold=ErrorSeverity.MEDIUM,
                error_count_threshold=10,
                time_window_minutes=5,
                category_filter=ErrorCategory.AUTHENTICATION,
            ),
            AlertRule(
                rule_id="ai_agent_errors",
                name="AI Agent Error Alert",
                description="Alert when AI agent errors occur frequently",
                severity_threshold=ErrorSeverity.MEDIUM,
                error_count_threshold=5,
                time_window_minutes=10,
                category_filter=ErrorCategory.AI_AGENT,
            ),
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule_id}")

    def check_alerts(self) -> list[Alert]:
        """Check for new alerts based on current error statistics."""
        new_alerts = []
        current_time = datetime.now(timezone.utc)

        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Get error statistics for the time window
            window_start = current_time - timedelta(minutes=rule.time_window_minutes)
            error_count = self._count_errors_in_window(
                window_start,
                current_time,
                rule.severity_threshold,
                rule.category_filter,
            )

            # Check if threshold is exceeded
            if error_count >= rule.error_count_threshold:
                # Check if alert already exists
                existing_alert = self._get_active_alert(rule_id)
                if not existing_alert:
                    # Create new alert
                    alert = Alert(
                        alert_id=str(uuid4()),
                        rule_id=rule_id,
                        rule_name=rule.name,
                        severity=rule.severity_threshold,
                        message=f"{rule.description}: {error_count} errors in {rule.time_window_minutes} minutes",
                        error_count=error_count,
                        time_window_minutes=rule.time_window_minutes,
                        category=rule.category_filter,
                        timestamp=current_time,
                    )
                    self.active_alerts[alert.alert_id] = alert
                    new_alerts.append(alert)
                    self.logger.warning(f"New alert triggered: {alert.message}")
                else:
                    # Update existing alert
                    existing_alert.error_count = error_count
                    existing_alert.message = f"{rule.description}: {error_count} errors in {rule.time_window_minutes} minutes"

        return new_alerts

    def _count_errors_in_window(
        self,
        window_start: datetime,
        window_end: datetime,
        severity: ErrorSeverity,
        category: ErrorCategory | None = None,
    ) -> int:
        """Count errors in the specified time window."""
        count = 0
        for error_record in self.error_history:
            error_time = datetime.fromisoformat(error_record["timestamp"])
            if window_start <= error_time <= window_end:
                # Check severity distribution for the specified severity
                severity_count = error_record.get("severity_distribution", {}).get(
                    severity.value, 0
                )
                if severity_count > 0:
                    if category is None:
                        count += severity_count
                    else:
                        # Check category distribution for the specified category
                        category_count = error_record.get(
                            "category_distribution", {}
                        ).get(category.value, 0)
                        count += min(severity_count, category_count)
        return count

    def _get_active_alert(self, rule_id: str) -> Alert | None:
        """Get active alert for a rule."""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and not alert.resolved:
                return alert
        return None

    def resolve_alert(
        self,
        alert_id: str,
        resolution_message: str = "Manually resolved",
    ) -> None:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now(timezone.utc)
            self.logger.info(
                f"Alert resolved: {alert.rule_name} - {resolution_message}",
            )

    def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]

    def get_alert_history(self, days: int = 7) -> list[Alert]:
        """Get alert history for the specified number of days."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            alert
            for alert in self.active_alerts.values()
            if alert.timestamp >= cutoff_time
        ]

    def get_error_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get error summary for the specified number of hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [
            error
            for error in self.error_history
            if datetime.fromisoformat(error["timestamp"]) >= cutoff_time
        ]

        # Calculate statistics from aggregated data
        total_errors = sum(error.get("total_errors", 0) for error in recent_errors)
        severity_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        error_type_counts: dict[str, int] = {}

        # Aggregate statistics from all recent error history entries
        for error in recent_errors:
            # Aggregate severity distribution
            for severity, count in error.get("severity_distribution", {}).items():
                severity_counts[severity] = severity_counts.get(severity, 0) + count

            # Aggregate category distribution
            for category, count in error.get("category_distribution", {}).items():
                category_counts[category] = category_counts.get(category, 0) + count

            # Aggregate error type distribution
            for error_type, count in error.get("error_types", {}).items():
                error_type_counts[error_type] = (
                    error_type_counts.get(error_type, 0) + count
                )

        return {
            "period_hours": hours,
            "total_errors": total_errors,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "error_type_distribution": error_type_counts,
            "active_alerts": len(self.get_active_alerts()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def start_monitoring(self, check_interval_seconds: int = 60) -> None:
        """Start the monitoring task."""
        try:
            # Check if we're in a Lambda environment or if there's no running loop
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, this is normal in Lambda
                self.logger.info(
                    "No running event loop detected - monitoring will start when loop is available"
                )
                return

            if self.monitoring_task is None or self.monitoring_task.done():
                self.monitoring_task = asyncio.create_task(
                    self._monitoring_loop(check_interval_seconds),
                )
                self.logger.info("Error monitoring started")
        except Exception as e:
            self.logger.warning(f"Could not start error monitoring: {e}")
            # Don't fail the application if monitoring can't start

    def stop_monitoring(self) -> None:
        """Stop the monitoring task."""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            self.logger.info("Error monitoring stopped")

    async def _monitoring_loop(self, check_interval_seconds: int) -> None:
        """Main monitoring loop."""
        while True:
            try:
                # Check for new alerts
                new_alerts = self.check_alerts()

                # Update error history from error logger
                self._update_error_history()

                # Log monitoring status
                if new_alerts:
                    self.logger.warning(f"Generated {len(new_alerts)} new alerts")
                else:
                    self.logger.debug("No new alerts generated")

                # Wait for next check
                await asyncio.sleep(check_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in monitoring loop: {e!s}")
                await asyncio.sleep(check_interval_seconds)

    def _update_error_history(self) -> None:
        """Update error history from the error logger."""
        try:
            # Get current error statistics
            stats = get_error_statistics()

            # Add current timestamp to error history
            current_time = datetime.now(timezone.utc).isoformat()

            # Create error history entry
            history_entry = {
                "timestamp": current_time,
                "total_errors": stats["total_errors"],
                "severity_distribution": stats["severity_distribution"],
                "category_distribution": stats["category_distribution"],
                "error_types": stats["error_types"],
            }

            self.error_history.append(history_entry)

            # Keep only last 1000 entries to prevent memory issues
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]

        except Exception as e:
            self.logger.exception(f"Error updating error history: {e!s}")


# Global error monitor instance
error_monitor = ErrorMonitor()


# Convenience functions
def start_error_monitoring(check_interval_seconds: int = 60) -> None:
    """Start error monitoring."""
    error_monitor.start_monitoring(check_interval_seconds)


def stop_error_monitoring() -> None:
    """Stop error monitoring."""
    error_monitor.stop_monitoring()


def get_error_summary(hours: int = 24) -> dict[str, Any]:
    """Get error summary."""
    return error_monitor.get_error_summary(hours)


def get_active_alerts() -> list[Alert]:
    """Get active alerts."""
    return error_monitor.get_active_alerts()


def resolve_alert(alert_id: str, resolution_message: str = "Manually resolved") -> None:
    """Resolve an alert."""
    error_monitor.resolve_alert(alert_id, resolution_message)
