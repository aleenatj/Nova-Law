#!/usr/bin/env python3
"""CI Size Check for Lambda Packages.

Checks package sizes and provides GitHub/Slack notifications.
"""

import json
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

import click


class CISizeChecker:
    """Checks package sizes for CI/CD pipelines."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.lambda_limit_mb = 250
        self.warning_threshold_mb = 200

    def check_current_package_size(self) -> dict[str, Any]:
        """Check the size of the current package."""
        print("🔍 Checking current package size...")

        # Get Poetry dependencies as text
        result = subprocess.run(  # nosec B607, B603
            ["poetry", "show", "--tree"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            check=False,
        )

        if result.returncode != 0:
            raise click.ClickException("Failed to get dependency tree")

        # Parse the text output
        dependencies = self._parse_dependency_tree(result.stdout)

        # Calculate sizes
        package_sizes = self._calculate_package_sizes(dependencies)
        total_size_mb = sum(package_sizes.values()) / (1024 * 1024)

        return {
            "total_size_mb": total_size_mb,
            "package_sizes": package_sizes,
            "dependencies": dependencies,
        }

    def _parse_dependency_tree(self, tree_output: str) -> list[dict[str, str]]:
        """Parse Poetry's dependency tree text output."""
        dependencies = []
        lines = tree_output.strip().split("\n")

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Parse package information
            # Format: package_name version description
            parts = line.strip().split(" ", 2)
            if len(parts) >= 2:
                package_name = parts[0]
                version = parts[1]
                description = parts[2] if len(parts) > 2 else ""

                # Skip dependency tree indicators (├──, └──, etc.)
                if (
                    not package_name.startswith("├──")
                    and not package_name.startswith("└──")
                    and not package_name.startswith("│")
                ):
                    dependencies.append(
                        {
                            "name": package_name,
                            "version": version,
                            "description": description,
                        }
                    )

        return dependencies

    def _calculate_package_sizes(self, dependencies: list[dict]) -> dict[str, int]:
        """Calculate package sizes in bytes."""
        sizes = {}

        for dep in dependencies:
            try:
                # Get package location
                result = subprocess.run(  # nosec B607, B603
                    [
                        "poetry",
                        "run",
                        "python",
                        "-c",
                        f"import {dep['name']}; print({dep['name']}.__file__)",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    check=False,
                )

                if result.returncode == 0:
                    package_path = Path(result.stdout.strip())
                    if package_path.exists():
                        size = self._calculate_directory_size(package_path)
                        sizes[dep["name"]] = size

            except Exception:
                sizes[dep["name"]] = 0

        return sizes

    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of a directory."""
        total_size = 0

        if path.is_file():
            return path.stat().st_size

        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def check_build_artifact_size(self, artifact_path: Path) -> float:
        """Check the size of a built artifact."""
        if not artifact_path.exists():
            raise click.ClickException(f"Artifact not found: {artifact_path}")

        size_bytes = artifact_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        return size_mb

    def generate_size_report(self, package_info: dict[str, Any]) -> str:
        """Generate a detailed size report."""
        report = []
        report.append("📊 PACKAGE SIZE REPORT")
        report.append("=" * 50)

        total_size = package_info["total_size_mb"]
        report.append(f"Total package size: {total_size:.2f} MB")

        # Status indicators
        if total_size > self.lambda_limit_mb:
            report.append("❌ CRITICAL: Package exceeds Lambda's 250MB limit!")
            report.append("   Consider using Lambda layers or optimizing dependencies.")
        elif total_size > self.warning_threshold_mb:
            report.append("⚠️  WARNING: Package size approaching Lambda limit")
            report.append("   Consider optimization before deployment.")
        else:
            report.append("✅ Package size is within acceptable limits")

        # Large dependencies
        large_deps = []
        for package, size in package_info["package_sizes"].items():
            size_mb = size / (1024 * 1024)
            if size_mb > 10:  # Dependencies larger than 10MB
                large_deps.append((package, size_mb))

        if large_deps:
            report.append("\n🔍 Large dependencies (> 10MB):")
            for package, size in sorted(large_deps, key=lambda x: x[1], reverse=True):
                report.append(f"  - {package}: {size:.2f} MB")

        return "\n".join(report)

    def create_github_comment(self, report: str, package_size: float) -> str:
        """Create a GitHub comment for PRs."""
        status_emoji = "✅" if package_size <= self.lambda_limit_mb else "❌"

        comment = f"""## Lambda Package Size Check {status_emoji}

{report}

### Recommendations:
- Use `poetry add --group prod <package>` for production dependencies
- Consider Lambda layers for large dependencies
- Use multi-stage Docker builds
- Implement runtime dependency loading
- Use `poetry export --only=prod` for deployment

### CI/CD Integration:
This check runs automatically on every PR to ensure Lambda deployment compatibility.
"""

        return comment

    def create_slack_notification(self, package_size: float, report: str) -> dict:
        """Create a Slack notification payload."""
        color = "#36a64f" if package_size <= self.lambda_limit_mb else "#ff0000"

        return {
            "attachments": [
                {
                    "color": color,
                    "title": "Lambda Package Size Check",
                    "text": report,
                    "fields": [
                        {
                            "title": "Package Size",
                            "value": f"{package_size:.2f} MB",
                            "short": True,
                        },
                        {
                            "title": "Lambda Limit",
                            "value": f"{self.lambda_limit_mb} MB",
                            "short": True,
                        },
                    ],
                }
            ]
        }

    def check_dependency_groups(self) -> dict[str, list[str]]:
        """Check if dependencies are properly organized in groups."""
        print("🔍 Checking dependency groups...")

        # Get all dependencies as text
        result = subprocess.run(  # nosec B607, B603
            ["poetry", "show"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            check=False,
        )

        if result.returncode != 0:
            return {}

        # Parse the text output
        dependencies = self._parse_dependency_tree(result.stdout)

        # Check which dependencies are in which groups
        groups: dict[str, list[str]] = {
            "prod": [],
            "dev": [],
            "test": [],
            "ungrouped": [],
        }

        for dep in dependencies:
            # This is a simplified check - in practice you'd need to parse pyproject.toml
            # to get the actual group assignments
            if dep["name"] in ["pytest", "black", "ruff", "mypy"]:
                groups["dev"].append(dep["name"])
            elif dep["name"] in ["fastapi", "uvicorn", "pydantic"]:
                groups["prod"].append(dep["name"])
            else:
                groups["ungrouped"].append(dep["name"])

        return groups


@click.command()  # type: ignore[misc]
@click.option("--project-root", default=".", help="Project root directory")  # type: ignore[misc]
@click.option("--artifact-path", help="Path to built artifact to check")  # type: ignore[misc]
@click.option("--github-comment", is_flag=True, help="Generate GitHub comment format")  # type: ignore[misc]
@click.option("--slack-notification", is_flag=True, help="Generate Slack notification")  # type: ignore[misc]
@click.option("--check-groups", is_flag=True, help="Check dependency groups")  # type: ignore[misc]
@click.option("--fail-on-limit", is_flag=True, help="Exit with error if over limit")  # type: ignore[misc]
def main(
    project_root: str,
    artifact_path: str | None,
    github_comment: bool,
    slack_notification: bool,
    check_groups: bool,
    fail_on_limit: bool,
) -> None:
    """Check package size for Lambda deployment."""

    project_path = Path(project_root)

    if not (project_path / "pyproject.toml").exists():
        click.echo("❌ pyproject.toml not found in the specified directory")
        sys.exit(1)

    checker = CISizeChecker(project_path)

    try:
        # Check current package size
        package_info = checker.check_current_package_size()
        total_size = package_info["total_size_mb"]

        # Generate report
        report = checker.generate_size_report(package_info)
        click.echo(report)

        # Check artifact if provided
        if artifact_path:
            artifact_size = checker.check_build_artifact_size(Path(artifact_path))
            click.echo(f"\n📦 Artifact size: {artifact_size:.2f} MB")

        # Check dependency groups
        if check_groups:
            groups = checker.check_dependency_groups()
            click.echo("\n📋 Dependency Groups:")
            for group, deps in groups.items():
                if deps:
                    click.echo(f"  {group}: {', '.join(deps)}")

        # Generate GitHub comment
        if github_comment:
            comment = checker.create_github_comment(report, total_size)
            click.echo(f"\n📝 GitHub Comment:\n{comment}")

        # Generate Slack notification
        if slack_notification:
            notification = checker.create_slack_notification(total_size, report)
            click.echo(
                f"\n📱 Slack Notification:\n{json.dumps(notification, indent=2)}"
            )

        # Exit with error if over limit and requested
        if fail_on_limit and total_size > checker.lambda_limit_mb:
            click.echo("\n❌ Package size exceeds Lambda limit. Build failed.")
            sys.exit(1)

        click.echo("\n✅ Size check completed successfully")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
