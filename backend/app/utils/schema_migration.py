"""Schema migration utilities for Nova Law API.

This module provides utilities for migrating data between different API versions,
ensuring backward compatibility and smooth transitions.
"""

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SchemaMigrator:
    """Handles schema migration between API versions."""

    def __init__(self) -> None:
        self.migration_rules: dict[str, dict[str, Any]] = {}
        self._register_default_migrations()

    def _register_default_migrations(self) -> None:
        """Register default migration rules."""
        # v1 to v2 migrations
        self.migration_rules.update(
            {
                "v1_to_v2": {
                    "user_create": self._migrate_user_create_v1_to_v2,
                    "user_response": self._migrate_user_response_v1_to_v2,
                    "auth_login": self._migrate_auth_login_v1_to_v2,
                    "agent_config": self._migrate_agent_config_v1_to_v2,
                },
                "v2_to_v1": {
                    "user_create": self._migrate_user_create_v2_to_v1,
                    "user_response": self._migrate_user_response_v2_to_v1,
                    "auth_login": self._migrate_auth_login_v2_to_v1,
                    "agent_config": self._migrate_agent_config_v2_to_v1,
                },
            },
        )

    def migrate_data(
        self,
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
            schema_type: Type of schema to migrate

        Returns:
        -------
            Migrated data

        """
        if from_version == to_version:
            return data

        migration_key = f"{from_version}_to_{to_version}"

        if migration_key not in self.migration_rules:
            logger.warning(f"No migration rules found for {migration_key}")
            return data

        schema_rules = self.migration_rules[migration_key]

        if schema_type not in schema_rules:
            logger.warning(
                f"No migration rule found for {schema_type} in {migration_key}",
            )
            return data

        try:
            migrated_data = schema_rules[schema_type](data)
            logger.info(
                f"Successfully migrated {schema_type} from {from_version} to {to_version}",
            )
            result: dict[str, Any] = migrated_data
            return result
        except Exception as e:
            logger.exception(f"Migration failed for {schema_type}: {e!s}")
            return data

    def validate_migration(
        self,
        original_data: dict[str, Any],
        migrated_data: dict[str, Any],
        schema_type: str,
    ) -> bool:
        """Validate that migration was successful.

        Args:
        ----
            original_data: Original data
            migrated_data: Migrated data
            schema_type: Type of schema

        Returns:
        -------
            True if migration is valid

        """
        # Basic validation - ensure required fields are present
        required_fields = self._get_required_fields(schema_type)

        for field in required_fields:
            if field not in migrated_data:
                logger.error(f"Required field {field} missing after migration")
                return False

        return True

    def _get_required_fields(self, schema_type: str) -> list[str]:
        """Get required fields for a schema type."""
        required_fields_map = {
            "user_create": ["email", "full_name", "password"],
            "user_response": ["id", "email", "full_name"],
            "auth_login": ["email", "password"],
            "agent_config": ["agent_id", "config"],
        }

        return required_fields_map.get(schema_type, [])

    # Migration functions for v1 to v2
    def _migrate_user_create_v1_to_v2(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate user creation from v1 to v2."""
        migrated_data = data.copy()

        # Add new optional fields with defaults
        if "phone_number" not in migrated_data:
            migrated_data["phone_number"] = None

        if "accept_terms" not in migrated_data:
            migrated_data["accept_terms"] = False

        # Add new validation fields
        if "email_verified" not in migrated_data:
            migrated_data["email_verified"] = False

        return migrated_data

    def _migrate_user_response_v1_to_v2(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate user response from v1 to v2."""
        migrated_data = data.copy()

        # Convert string age to integer if present
        if "age" in migrated_data and isinstance(migrated_data["age"], str):
            try:
                migrated_data["age"] = int(migrated_data["age"])
            except ValueError:
                migrated_data["age"] = None

        # Add new fields with defaults
        if "phone_number" not in migrated_data:
            migrated_data["phone_number"] = None

        if "email_verified" not in migrated_data:
            migrated_data["email_verified"] = False

        if "profile_complete" not in migrated_data:
            migrated_data["profile_complete"] = True

        return migrated_data

    def _migrate_auth_login_v1_to_v2(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate auth login from v1 to v2."""
        migrated_data = data.copy()

        # Add new optional fields
        if "remember_me" not in migrated_data:
            migrated_data["remember_me"] = False

        if "device_id" not in migrated_data:
            migrated_data["device_id"] = None

        return migrated_data

    def _migrate_agent_config_v1_to_v2(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate agent config from v1 to v2."""
        migrated_data = data.copy()

        # Add new configuration options
        if "advanced_settings" not in migrated_data:
            migrated_data["advanced_settings"] = {}

        if "performance_metrics" not in migrated_data:
            migrated_data["performance_metrics"] = True

        return migrated_data

    # Migration functions for v2 to v1 (backward compatibility)
    def _migrate_user_create_v2_to_v1(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate user creation from v2 to v1."""
        migrated_data = data.copy()

        # Remove new fields
        migrated_data.pop("phone_number", None)
        migrated_data.pop("accept_terms", None)
        migrated_data.pop("email_verified", None)

        return migrated_data

    def _migrate_user_response_v2_to_v1(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate user response from v2 to v1."""
        migrated_data = data.copy()

        # Convert integer age back to string if present
        if "age" in migrated_data and isinstance(migrated_data["age"], int):
            migrated_data["age"] = str(migrated_data["age"])

        # Remove new fields
        migrated_data.pop("phone_number", None)
        migrated_data.pop("email_verified", None)
        migrated_data.pop("profile_complete", None)

        return migrated_data

    def _migrate_auth_login_v2_to_v1(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate auth login from v2 to v1."""
        migrated_data = data.copy()

        # Remove new fields
        migrated_data.pop("remember_me", None)
        migrated_data.pop("device_id", None)

        return migrated_data

    def _migrate_agent_config_v2_to_v1(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate agent config from v2 to v1."""
        migrated_data = data.copy()

        # Remove new fields
        migrated_data.pop("advanced_settings", None)
        migrated_data.pop("performance_metrics", None)

        return migrated_data


class SchemaCompatibilityChecker:
    """Check compatibility between schema versions."""

    @staticmethod
    def check_backward_compatibility(
        old_schema: type[BaseModel],
        new_schema: type[BaseModel],
    ) -> dict[str, Any]:
        """Check if new schema is backward compatible with old schema.

        Args:
        ----
            old_schema: Old schema class
            new_schema: New schema class

        Returns:
        -------
            Compatibility report

        """
        old_fields = old_schema.model_fields
        new_fields = new_schema.model_fields

        compatibility_report: dict[str, Any] = {
            "compatible": True,
            "breaking_changes": [],
            "new_fields": [],
            "removed_fields": [],
            "type_changes": [],
        }

        # Check for removed fields
        for field_name, field_info in old_fields.items():
            if field_name not in new_fields:
                compatibility_report["compatible"] = False
                compatibility_report["breaking_changes"].append(
                    f"Field '{field_name}' removed",
                )
                compatibility_report["removed_fields"].append(field_name)
                continue

            # Check for type changes
            new_field_info = new_fields[field_name]
            if field_info.annotation != new_field_info.annotation:
                compatibility_report["type_changes"].append(
                    {
                        "field": field_name,
                        "old_type": str(field_info.annotation),
                        "new_type": str(new_field_info.annotation),
                    },
                )

            # Check for required field made optional
            if field_info.is_required() and not new_field_info.is_required():
                compatibility_report["breaking_changes"].append(
                    f"Required field '{field_name}' made optional",
                )

        # Check for new fields
        for field_name in new_fields:
            if field_name not in old_fields:
                compatibility_report["new_fields"].append(field_name)

        return compatibility_report

    @staticmethod
    def validate_schema_evolution(schemas: list[type[BaseModel]]) -> dict[str, Any]:
        """Validate schema evolution across multiple versions.

        Args:
        ----
            schemas: List of schema classes in version order

        Returns:
        -------
            Evolution report

        """
        evolution_report: dict[str, Any] = {
            "valid": True,
            "issues": [],
            "recommendations": [],
        }

        for i in range(len(schemas) - 1):
            old_schema = schemas[i]
            new_schema = schemas[i + 1]

            compatibility = SchemaCompatibilityChecker.check_backward_compatibility(
                old_schema,
                new_schema,
            )

            if not compatibility["compatible"]:
                evolution_report["valid"] = False
                evolution_report["issues"].extend(compatibility["breaking_changes"])

        return evolution_report


# Global migrator instance
schema_migrator = SchemaMigrator()
compatibility_checker = SchemaCompatibilityChecker()
