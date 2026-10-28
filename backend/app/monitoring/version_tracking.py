"""Version tracking and monitoring for Nova Law API.

This module provides utilities for tracking API version usage, monitoring
migration progress, and generating insights for version management.
"""

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VersionUsageStats:
    """Statistics for API version usage."""

    version: str
    requests: int = 0
    errors: int = 0
    last_used: datetime | None = None
    unique_clients: int = 0
    avg_response_time: float = 0.0
    endpoints_used: list[str] | None = None

    def __post_init__(self) -> None:
        if self.endpoints_used is None:
            self.endpoints_used = []


@dataclass
class MigrationProgress:
    """Migration progress tracking."""

    from_version: str
    to_version: str
    total_clients: int
    migrated_clients: int
    migration_start_date: datetime
    target_completion_date: datetime
    current_completion_percentage: float = 0.0


class VersionUsageTracker:
    """Track API version usage and generate insights."""

    def __init__(self) -> None:
        self.usage_stats: dict[str, VersionUsageStats] = defaultdict(
            lambda: VersionUsageStats(version="unknown"),
        )
        self.client_versions: dict[str, str] = {}  # client_id -> version
        self.endpoint_usage: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int),
        )
        self.response_times: dict[str, list[float]] = defaultdict(list)
        self.migration_progress: dict[str, MigrationProgress] = {}

    def track_request(
        self,
        version: str,
        endpoint: str,
        client_id: str | None = None,
        success: bool = True,
        response_time: float = 0.0,
    ) -> None:
        """Track an API request.

        Args:
        ----
            version: API version used
            endpoint: Endpoint accessed
            client_id: Client identifier
            success: Whether request was successful
            response_time: Response time in seconds

        """
        # Update version stats
        if version not in self.usage_stats:
            self.usage_stats[version] = VersionUsageStats(version=version)

        stats = self.usage_stats[version]
        stats.requests += 1
        stats.last_used = datetime.now()

        if not success:
            stats.errors += 1

        # Track response time
        self.response_times[version].append(response_time)
        if len(self.response_times[version]) > 1000:  # Keep last 1000 samples
            self.response_times[version] = self.response_times[version][-1000:]

        # Update average response time
        if self.response_times[version]:
            stats.avg_response_time = sum(self.response_times[version]) / len(
                self.response_times[version],
            )

        # Track endpoint usage
        self.endpoint_usage[version][endpoint] += 1
        if stats.endpoints_used is not None and endpoint not in stats.endpoints_used:
            stats.endpoints_used.append(endpoint)

        # Track client version
        if client_id:
            self.client_versions[client_id] = version
            # Update unique clients count
            unique_clients = len(
                {
                    client
                    for client, ver in self.client_versions.items()
                    if ver == version
                },
            )
            stats.unique_clients = unique_clients

        logger.debug(
            f"Tracked request: version={version}, endpoint={endpoint}, success={success}",
        )

    def get_usage_report(self, days: int = 30) -> dict[str, Any]:
        """Generate usage report for the specified period.

        Args:
        ----
            days: Number of days to include in report

        Returns:
        -------
            Usage report dictionary

        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter stats for the period
        recent_stats = {}
        recent_stats = {
            version: stats
            for version, stats in self.usage_stats.items()
            if stats.last_used and stats.last_used >= cutoff_date
        }

        # Calculate totals
        total_requests = sum(stats.requests for stats in recent_stats.values())
        total_errors = sum(stats.errors for stats in recent_stats.values())

        # Calculate version distribution
        version_distribution = {}
        if total_requests > 0:
            for version, stats in recent_stats.items():
                version_distribution[version] = {
                    "requests": stats.requests,
                    "percentage": (stats.requests / total_requests) * 100,
                    "error_rate": (
                        (stats.errors / stats.requests) * 100
                        if stats.requests > 0
                        else 0
                    ),
                    "avg_response_time": stats.avg_response_time,
                    "unique_clients": stats.unique_clients,
                }

        return {
            "period_days": days,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_error_rate": (
                (total_errors / total_requests) * 100 if total_requests > 0 else 0
            ),
            "version_distribution": version_distribution,
            "most_used_endpoints": self._get_most_used_endpoints(days),
            "migration_recommendations": self._generate_migration_recommendations(),
        }

    def _get_most_used_endpoints(self, days: int) -> dict[str, list[dict[str, Any]]]:
        """Get most used endpoints by version."""
        # Note: cutoff_date is not used in current implementation
        # but kept for future filtering logic

        most_used = {}
        for version, endpoint_counts in self.endpoint_usage.items():
            # Filter for recent usage
            recent_endpoints: list[dict[str, Any]] = []
            for endpoint, count in endpoint_counts.items():
                recent_endpoints.append({"endpoint": endpoint, "requests": count})

            # Sort by request count
            recent_endpoints.sort(key=lambda x: x["requests"], reverse=True)
            most_used[version] = recent_endpoints[:10]  # Top 10

        return most_used

    def _generate_migration_recommendations(self) -> list[dict[str, Any]]:
        """Generate migration recommendations based on usage patterns."""
        recommendations: list[dict[str, Any]] = []

        # Check for deprecated version usage
        for version, stats in self.usage_stats.items():
            if stats.requests > 0 and self._is_deprecated(version):
                recommendations.append(
                    {
                        "type": "deprecation_warning",
                        "version": version,
                        "message": f"Version {version} is deprecated but still has {stats.requests} requests",
                        "priority": "high",
                        "action": "migrate_to_latest",
                    },
                )

        # Check for version distribution
        total_requests = sum(stats.requests for stats in self.usage_stats.values())
        if total_requests > 0:
            for version, stats in self.usage_stats.items():
                usage_percentage = (stats.requests / total_requests) * 100

                if usage_percentage < 5 and stats.requests > 100:
                    recommendations.append(
                        {
                            "type": "low_usage",
                            "version": version,
                            "message": f"Version {version} has low usage ({usage_percentage:.1f}%)",
                            "priority": "medium",
                            "action": "consider_deprecation",
                        },
                    )

        return recommendations

    def _is_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        # This would integrate with the version manager
        deprecated_versions = ["v0"]  # Example
        return version in deprecated_versions

    def track_migration_progress(
        self,
        migration_id: str,
        from_version: str,
        to_version: str,
        total_clients: int,
        migrated_clients: int,
        target_completion_date: datetime,
    ) -> None:
        """Track migration progress.

        Args:
        ----
            migration_id: Unique migration identifier
            from_version: Source version
            to_version: Target version
            total_clients: Total number of clients to migrate
            migrated_clients: Number of clients already migrated
            target_completion_date: Target completion date

        """
        completion_percentage = (
            (migrated_clients / total_clients) * 100 if total_clients > 0 else 0
        )

        self.migration_progress[migration_id] = MigrationProgress(
            from_version=from_version,
            to_version=to_version,
            total_clients=total_clients,
            migrated_clients=migrated_clients,
            migration_start_date=datetime.now(),
            target_completion_date=target_completion_date,
            current_completion_percentage=completion_percentage,
        )

    def get_migration_report(self) -> dict[str, Any]:
        """Generate migration progress report."""
        active_migrations: list[dict[str, Any]] = []
        completed_migrations: list[dict[str, Any]] = []

        for migration_id, progress in self.migration_progress.items():
            migration_data = asdict(progress)
            migration_data["migration_id"] = migration_id

            if progress.current_completion_percentage >= 100:
                completed_migrations.append(migration_data)
            else:
                active_migrations.append(migration_data)

        return {
            "active_migrations": active_migrations,
            "completed_migrations": completed_migrations,
            "total_migrations": len(self.migration_progress),
        }


class VersionAlertManager:
    """Manage alerts for version-related issues."""

    def __init__(self) -> None:
        self.alerts: list[dict[str, Any]] = []
        self.alert_thresholds = {
            "deprecated_version_usage": 0.1,  # 10% of total requests
            "high_error_rate": 0.05,  # 5% error rate
            "low_migration_progress": 0.5,  # 50% completion threshold
        }

    def check_alerts(self, usage_tracker: VersionUsageTracker) -> list[dict[str, Any]]:
        """Check for alerts based on current usage patterns.

        Args:
        ----
            usage_tracker: Version usage tracker instance

        Returns:
        -------
            List of active alerts

        """
        alerts: list[dict[str, Any]] = []

        # Check for deprecated version usage
        usage_report = usage_tracker.get_usage_report()
        total_requests = usage_report["total_requests"]

        if total_requests > 0:
            for version, stats in usage_report["version_distribution"].items():
                if self._is_deprecated(version):
                    usage_percentage = stats["percentage"] / 100
                    if (
                        usage_percentage
                        > self.alert_thresholds["deprecated_version_usage"]
                    ):
                        alerts.append(
                            {
                                "type": "deprecated_version_usage",
                                "severity": "high",
                                "message": f"High usage of deprecated version {version}: {stats['percentage']:.1f}%",
                                "version": version,
                                "usage_percentage": stats["percentage"],
                            },
                        )

                # Check for high error rates
                if stats["error_rate"] > self.alert_thresholds["high_error_rate"] * 100:
                    alerts.append(
                        {
                            "type": "high_error_rate",
                            "severity": "medium",
                            "message": f"High error rate for version {version}: {stats['error_rate']:.1f}%",
                            "version": version,
                            "error_rate": stats["error_rate"],
                        },
                    )

        # Check migration progress
        migration_report = usage_tracker.get_migration_report()
        for migration in migration_report["active_migrations"]:
            if (
                migration["current_completion_percentage"]
                < self.alert_thresholds["low_migration_progress"] * 100
            ):
                alerts.append(
                    {
                        "type": "low_migration_progress",
                        "severity": "medium",
                        "message": f"Low migration progress: {migration['current_completion_percentage']:.1f}%",
                        "migration_id": migration["migration_id"],
                        "completion_percentage": migration[
                            "current_completion_percentage"
                        ],
                    },
                )

        return alerts

    def _is_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        # This would integrate with the version manager
        deprecated_versions = ["v0"]
        return version in deprecated_versions


# Global tracker instance
version_tracker = VersionUsageTracker()
alert_manager = VersionAlertManager()
