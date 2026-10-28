"""Core versioning management system for Nova Law API.

This module provides centralized version management, including version detection,
deprecation handling, and migration utilities.
"""

import re
from datetime import datetime
from typing import Any

from fastapi import Request

from app.enums import APIVersion


class VersionManager:
    """Centralized version management for the API."""

    def __init__(self) -> None:
        self.supported_versions: list[APIVersion] = [APIVersion.V1]
        self.default_version: APIVersion = APIVersion.V1
        self.deprecated_versions: list[APIVersion] = []
        self.deprecation_schedule: dict[str, datetime] = {}

        # Version lifecycle dates
        self.version_lifecycle = {
            APIVersion.V1: {
                "release_date": datetime(2024, 1, 1),
                "deprecation_date": datetime(2025, 6, 1),
                "end_of_life": datetime(2025, 12, 31),
            },
        }

    def is_supported(self, version: str) -> bool:
        """Check if a version is currently supported."""
        try:
            api_version = APIVersion(version)
            return api_version in self.supported_versions
        except ValueError:
            return False

    def is_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        try:
            api_version = APIVersion(version)
            return api_version in self.deprecated_versions
        except ValueError:
            return False

    def get_deprecation_info(self, version: str) -> dict[str, Any] | None:
        """Get deprecation information for a version."""
        if not self.is_deprecated(version):
            return None

        lifecycle = self.version_lifecycle.get(APIVersion(version), {})
        end_of_life = lifecycle.get("end_of_life")

        days_until_eol = None
        if end_of_life is not None:
            days_until_eol = (end_of_life - datetime.now()).days

        result: dict[str, Any] = {
            "version": version,
            "deprecation_date": lifecycle.get("deprecation_date"),
            "end_of_life": end_of_life,
            "days_until_eol": days_until_eol,
        }
        return result

    def add_version(self, version: APIVersion, release_date: datetime) -> None:
        """Add a new supported version."""
        self.supported_versions.append(version)
        self.version_lifecycle[version] = {
            "release_date": release_date,
            "deprecation_date": None,
            "end_of_life": None,
        }

    def deprecate_version(
        self,
        version: APIVersion,
        deprecation_date: datetime,
        end_of_life: datetime,
    ) -> None:
        """Mark a version as deprecated."""
        self.deprecated_versions.append(version)
        if version in self.version_lifecycle:
            self.version_lifecycle[version].update(
                {
                    "deprecation_date": deprecation_date,
                    "end_of_life": end_of_life,
                },
            )

    def get_latest_version(self) -> APIVersion:
        """Get the latest stable version."""
        return max(self.supported_versions, key=lambda v: v.value)

    def get_recommended_version(self) -> APIVersion:
        """Get the recommended version for new integrations."""
        return self.get_latest_version()


class VersionDetector:
    """Detect API version from request."""

    def __init__(self, version_manager: VersionManager) -> None:
        self.version_manager = version_manager

    def detect_version(self, request: Request) -> str:
        """Detect API version from request.

        Priority order:
        1. URL path (/api/v1/, /api/v2/)
        2. Accept header (application/vnd.novalaw.v1+json)
        3. Default version
        """
        # Check URL path
        path_version = self._extract_version_from_path(request.url.path)
        if path_version and self.version_manager.is_supported(path_version):
            return path_version

        # Check Accept header
        accept_header = request.headers.get("accept", "")
        header_version = self._extract_version_from_header(accept_header)
        if header_version and self.version_manager.is_supported(header_version):
            return header_version

        # Return default version
        return self.version_manager.default_version.value

    def _extract_version_from_path(self, path: str) -> str | None:
        """Extract version from URL path."""
        # Pattern: /api/v1/, /api/v2/, etc.
        pattern = r"/api/(v\d+)/"
        match = re.search(pattern, path)
        return match.group(1) if match else None

    def _extract_version_from_header(self, accept_header: str) -> str | None:
        """Extract version from Accept header."""
        # Pattern: application/vnd.novalaw.v1+json
        pattern = r"application/vnd\.novalaw\.(v\d+)\+json"
        match = re.search(pattern, accept_header)
        return match.group(1) if match else None


class MigrationHelper:
    """Helper utilities for API version migrations."""

    @staticmethod
    def migrate_data(
        data: dict[str, Any],
        from_version: str,
        to_version: str,
        schema_type: str,
    ) -> dict[str, Any]:
        """Migrate data between API versions.

        Args:
        ----
            data: Input data to migrate
            from_version: Source version
            to_version: Target version
            schema_type: Type of schema (e.g., 'user', 'auth')

        Returns:
        -------
            Migrated data

        """
        if from_version == to_version:
            return data

        # Define migration functions
        migrations = {
            ("v1", "v2"): MigrationHelper._migrate_v1_to_v2,
            ("v2", "v1"): MigrationHelper._migrate_v2_to_v1,
        }

        migration_key = (from_version, to_version)
        if migration_key in migrations:
            return migrations[migration_key](data, schema_type)

        # If no specific migration, return as-is
        return data

    @staticmethod
    def _migrate_v1_to_v2(data: dict[str, Any], schema_type: str) -> dict[str, Any]:
        """Migrate data from v1 to v2."""
        migrated_data = data.copy()

        if schema_type == "user_create":
            # Add new fields with defaults
            if "phone_number" not in migrated_data:
                migrated_data["phone_number"] = None
            if "accept_terms" not in migrated_data:
                migrated_data["accept_terms"] = False

        elif schema_type == "user_response":
            # Convert string age to integer if present
            if "age" in migrated_data and isinstance(migrated_data["age"], str):
                try:
                    migrated_data["age"] = int(migrated_data["age"])
                except ValueError:
                    migrated_data["age"] = None

        return migrated_data

    @staticmethod
    def _migrate_v2_to_v1(data: dict[str, Any], schema_type: str) -> dict[str, Any]:
        """Migrate data from v2 to v1 (backward compatibility)."""
        migrated_data = data.copy()

        if schema_type == "user_create":
            # Remove new fields
            migrated_data.pop("phone_number", None)
            migrated_data.pop("accept_terms", None)

        elif schema_type == "user_response":
            # Convert integer age back to string if present
            if "age" in migrated_data and isinstance(migrated_data["age"], int):
                migrated_data["age"] = str(migrated_data["age"])

        return migrated_data


# Global version manager instance
version_manager = VersionManager()
version_detector = VersionDetector(version_manager)
migration_helper = MigrationHelper()
