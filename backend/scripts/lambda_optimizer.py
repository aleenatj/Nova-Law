#!/usr/bin/env python3
"""Lambda Package Optimizer.

Analyzes and optimizes Python packages for AWS Lambda deployment.
"""

import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

import click


class LambdaPackageOptimizer:
    """Analyzes and optimizes Poetry projects for Lambda deployment."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self.poetry_lock_path = project_root / "poetry.lock"

    def check_poetry_availability(self) -> bool:
        """Check if Poetry is available in the current environment."""
        try:
            result = subprocess.run(  # nosec B607, B603
                ["poetry", "--version"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def analyze_dependencies(self) -> dict[str, Any]:
        """Analyze current dependencies and their sizes."""
        print("🔍 Analyzing dependencies...")

        # Check if Poetry is available
        if not self.check_poetry_availability():
            print("❌ Poetry is not available in the current environment.")
            print("💡 Please activate your virtual environment or install Poetry:")
            print("   source venv-be/bin/activate  # If using virtual environment")
            print("   # OR install Poetry globally:")
            print("   curl -sSL https://install.python-poetry.org | python3 -")
            sys.exit(1)

        # Get dependency tree as text
        result = subprocess.run(  # nosec B607, B603
            ["poetry", "show", "--tree"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
            check=False,
        )

        if result.returncode != 0:
            print(f"❌ Failed to analyze dependencies: {result.stderr}")
            print("💡 Make sure you're in the correct directory with pyproject.toml")
            raise click.ClickException("Failed to analyze dependencies")

        # Parse the text output to extract dependencies
        dependencies = self._parse_dependency_tree(result.stdout)

        # Get package sizes
        package_sizes = self._get_package_sizes(dependencies)

        return {
            "dependencies": dependencies,
            "package_sizes": package_sizes,
            "total_size": sum(package_sizes.values()),
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

    def _get_package_sizes(self, dependencies: list[dict]) -> dict[str, int]:
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
                        size = self._calculate_package_size(package_path)
                        sizes[dep["name"]] = size

            except Exception:
                sizes[dep["name"]] = 0

        return sizes

    def _calculate_package_size(self, package_path: Path) -> int:
        """Calculate total size of a package directory."""
        total_size = 0

        if package_path.is_file():
            return package_path.stat().st_size

        for file_path in package_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    def identify_large_dependencies(
        self, package_sizes: dict[str, int], threshold_mb: int = 10
    ) -> list[tuple[str, int]]:
        """Identify dependencies larger than threshold."""
        threshold_bytes = threshold_mb * 1024 * 1024
        large_deps = []

        for package, size in package_sizes.items():
            if size > threshold_bytes:
                large_deps.append((package, size))

        return sorted(large_deps, key=lambda x: x[1], reverse=True)

    def suggest_alternatives(
        self, large_dependencies: list[tuple[str, int]]
    ) -> dict[str, list[str]]:
        """Suggest lighter alternatives for large dependencies."""
        alternatives = {
            "pandas": ["polars", "pyarrow", "vaex"],
            "numpy": ["array", "numba"],
            "scipy": ["scipy-lite", "scipy-optimize"],
            "matplotlib": ["plotly", "bokeh", "altair"],
            "seaborn": ["plotly", "bokeh"],
            "scikit-learn": ["lightgbm", "xgboost", "catboost"],
            "tensorflow": ["tensorflow-cpu", "onnxruntime"],
            "torch": ["torch-cpu", "onnxruntime"],
            "jupyter": ["ipython"],
            "notebook": ["jupyterlab"],
            "pytest": ["unittest", "nose2"],
            "black": ["autopep8", "yapf"],
            "ruff": ["flake8", "pylint"],
        }

        suggestions = {}
        for package, _ in large_dependencies:
            if package in alternatives:
                suggestions[package] = alternatives[package]

        return suggestions

    def generate_optimized_pyproject(self, exclude_dev: bool = True) -> str:
        """Generate an optimized pyproject.toml for production."""
        print("📝 Generating optimized pyproject.toml...")

        # Read current pyproject.toml
        with open(self.pyproject_path) as f:
            content = f.read()

        # Add production-specific configurations
        optimized_content = (
            content
            + """

[tool.poetry.group.prod]
optional = true

[tool.poetry.group.dev]
optional = true

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry.build]
exclude = [
    "tests/",
    "tests_*/",
    "test_*/",
    "**/tests/",
    "**/test_*/",
    "docs/",
    "documentation/",
    "*.md",
    "*.rst",
    "*.txt",
    ".git/",
    ".gitignore",
    ".env*",
    "*.log",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    ".mypy_cache/",
    ".ruff_cache/",
    "node_modules/",
    "venv*/",
    ".venv/",
    "*.egg-info/",
    "dist/",
    "build/",
    ".vscode/",
    ".idea/",
    "*.swp",
    "*.swo",
    "*~",
]

[tool.poetry.packages]
include = [
    "app/**/*",
    "lambda_handler.py",
]

[tool.poetry.scripts]
lambda-handler = "lambda_handler:handler"
"""
        )

        return optimized_content

    def create_lambda_layer_script(self) -> str:
        """Create a script for building Lambda layers."""
        return """#!/bin/bash
# Lambda Layer Builder Script

set -e

echo "🔧 Building Lambda Layer..."

# Create layer directory
LAYER_DIR="lambda-layer"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python

# Generate requirements.txt manually (Poetry 2.1.3 doesn't have export)
echo "📋 Generating requirements.txt..."
python3 -c "
import tomllib
import json

def convert_poetry_version_to_pip(version):
    # Remove Poetry-specific version constraints
    version = version.replace('^', '>=')
    version = version.replace('~', '>=')

    # Handle version ranges
    if '||' in version:
        parts = version.split('||')
        if len(parts) == 2:
            return f'>={parts[0].strip()},<{parts[1].strip()}'

    return version

with open('pyproject.toml', 'rb') as f:
    config = tomllib.load(f)

dependencies = []
if 'tool' in config and 'poetry' in config['tool']:
    poetry_config = config['tool']['poetry']

    # Get main dependencies
    if 'dependencies' in poetry_config:
        for package, version in poetry_config['dependencies'].items():
            # Skip Python version constraints and other non-pip packages
            if package in ['python']:
                continue

            if isinstance(version, str):
                pip_version = convert_poetry_version_to_pip(version)
                dependencies.append(f'{package}{pip_version}')
            else:
                dependencies.append(package)

    # Get production dependencies from groups
    if 'group' in poetry_config:
        for group_name, group_config in poetry_config['group'].items():
            if group_name == 'prod' and 'dependencies' in group_config:
                for package, version in group_config['dependencies'].items():
                    if isinstance(version, str):
                        pip_version = convert_poetry_version_to_pip(version)
                        dependencies.append(f'{package}{pip_version}')
                    else:
                        dependencies.append(package)

with open('requirements.txt', 'w') as f:
    for dep in dependencies:
        f.write(f'{dep}\\n')

print(f'Generated requirements.txt with {len(dependencies)} dependencies')
"

# Install to layer directory
pip install -r requirements.txt -t $LAYER_DIR/python --no-deps

# Remove unnecessary files to reduce size
find $LAYER_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $LAYER_DIR -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find $LAYER_DIR -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find $LAYER_DIR -name "*.pyc" -delete
find $LAYER_DIR -name "*.pyo" -delete
find $LAYER_DIR -name "*.pyd" -delete

# Remove test files
find $LAYER_DIR -path "*/tests/*" -delete
find $LAYER_DIR -path "*/test_*" -delete

# Remove documentation
find $LAYER_DIR -path "*/docs/*" -delete
find $LAYER_DIR -name "*.md" -delete
find $LAYER_DIR -name "*.rst" -delete
find $LAYER_DIR -name "*.txt" -delete

# Calculate size
LAYER_SIZE=$(du -sh $LAYER_DIR | cut -f1)
echo "📦 Layer size: $LAYER_SIZE"

# Create ZIP file
zip -r lambda-layer.zip $LAYER_DIR

echo "✅ Lambda layer created: lambda-layer.zip"
"""


@click.command()  # type: ignore[misc]
@click.option("--project-root", default=".", help="Project root directory")  # type: ignore[misc]
@click.option(
    "--threshold-mb", default=10, help="Size threshold in MB for large dependencies"
)  # type: ignore[misc]
@click.option(
    "--generate-optimized", is_flag=True, help="Generate optimized pyproject.toml"
)  # type: ignore[misc]
@click.option(
    "--create-layer-script", is_flag=True, help="Create Lambda layer builder script"
)  # type: ignore[misc]
def main(
    project_root: str,
    threshold_mb: int,
    generate_optimized: bool,
    create_layer_script: bool,
) -> None:
    """Lambda Package Size Optimizer for Poetry Projects."""

    project_path = Path(project_root)

    if not (project_path / "pyproject.toml").exists():
        click.echo("❌ pyproject.toml not found in the specified directory")
        click.echo("💡 Make sure you're running this from the project root directory")
        sys.exit(1)

    optimizer = LambdaPackageOptimizer(project_path)

    try:
        # Analyze dependencies
        analysis = optimizer.analyze_dependencies()

        # Identify large dependencies
        large_deps = optimizer.identify_large_dependencies(
            analysis["package_sizes"], threshold_mb
        )

        # Generate report
        click.echo("\n📊 DEPENDENCY ANALYSIS REPORT")
        click.echo("=" * 50)

        total_size_mb = analysis["total_size"] / (1024 * 1024)
        click.echo(f"Total package size: {total_size_mb:.2f} MB")

        if total_size_mb > 250:
            click.echo("⚠️  WARNING: Package size exceeds Lambda's 250MB limit!")

        if large_deps:
            click.echo(f"\n🔍 Large dependencies (> {threshold_mb}MB):")
            for package, size in large_deps:
                size_mb = size / (1024 * 1024)
                click.echo(f"  - {package}: {size_mb:.2f} MB")

            # Suggest alternatives
            suggestions = optimizer.suggest_alternatives(large_deps)
            if suggestions:
                click.echo("\n💡 Suggested lighter alternatives:")
                for package, alternatives in suggestions.items():
                    click.echo(f"  - {package}: {', '.join(alternatives)}")

        # Generate optimized pyproject.toml
        if generate_optimized:
            optimized_content = optimizer.generate_optimized_pyproject()
            output_path = project_path / "pyproject.optimized.toml"
            with open(output_path, "w") as f:
                f.write(optimized_content)
            click.echo(f"\n✅ Optimized pyproject.toml created: {output_path}")

        # Create Lambda layer script
        if create_layer_script:
            script_content = optimizer.create_lambda_layer_script()
            script_path = project_path / "build-lambda-layer.sh"
            with open(script_path, "w") as f:
                f.write(script_content)
            Path(script_path).chmod(0o755)
            click.echo(f"\n✅ Lambda layer builder script created: {script_path}")

        # Recommendations
        click.echo("\n📋 RECOMMENDATIONS:")
        click.echo("1. Use dependency groups: poetry add --group prod <package>")
        click.echo("2. Consider Lambda layers for large dependencies")
        click.echo("3. Use multi-stage Docker builds")
        click.echo("4. Implement runtime dependency loading")
        click.echo("5. Use poetry export for production requirements")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
