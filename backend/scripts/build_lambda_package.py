#!/usr/bin/env python3
"""Lambda Package Builder for Poetry Projects.

Creates optimized deployment packages for AWS Lambda with size optimization.
"""

import shutil
import subprocess  # nosec B404
import sys
import zipfile
from pathlib import Path

import click


class LambdaPackageBuilder:
    """Builds optimized Lambda deployment packages."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"

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

    def clean_build_directories(self) -> None:
        """Clean build and dist directories."""
        print("🧹 Cleaning build directories...")

        for directory in [self.build_dir, self.dist_dir]:
            if directory.exists():
                shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)

    def install_production_dependencies(self) -> None:
        """Install only production dependencies."""
        print("📦 Installing production dependencies...")

        # Check if Poetry is available
        if not self.check_poetry_availability():
            print("❌ Poetry is not available in the current environment.")
            print("💡 Please activate your virtual environment or install Poetry:")
            print("   source venv-be/bin/activate  # If using virtual environment")
            print("   # OR install Poetry globally:")
            print("   curl -sSL https://install.python-poetry.org | python3 -")
            sys.exit(1)

        # Generate requirements.txt manually since Poetry 2.1.3 doesn't have export
        requirements_file = self.build_dir / "requirements.txt"
        # self._generate_requirements_file(requirements_file)
        subprocess.run(
            [
                "poetry",
                "export",
                "-f",
                "requirements.txt",
                "--output",
                str(requirements_file),
                "--without-hashes",
                "--without",
                "dev",
            ],
            cwd=self.project_root,
            check=True,
        )        

        # Install to build directory
        subprocess.run(  # nosec B607, B603
            [
                "pip",
                "install",
                "-r",
                str(requirements_file),
                "-t",
                str(self.build_dir),
            ],
            check=True,
        )
        
        # safety check
        subprocess.run(["pip", "check"], check=True)

    def _generate_requirements_file(self, requirements_file: Path) -> None:  # noqa: PLR0912
        """Generate requirements.txt from pyproject.toml."""
        print("📋 Generating requirements.txt...")

        # Read pyproject.toml
        import tomllib

        with open(self.project_root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        # Extract dependencies
        dependencies = []
        if "tool" in config and "poetry" in config["tool"]:
            poetry_config = config["tool"]["poetry"]

            # Get main dependencies
            if "dependencies" in poetry_config:
                for package, version in poetry_config["dependencies"].items():
                    # Skip Python version constraints and other non-pip packages
                    if package in ["python"]:
                        continue

                    if isinstance(version, str):
                        # Convert Poetry version format to pip format
                        pip_version = self._convert_poetry_version_to_pip(version)
                        dependencies.append(f"{package}{pip_version}")
                    else:
                        dependencies.append(package)

            # Get production dependencies from groups
            if "group" in poetry_config:
                for group_name, group_config in poetry_config["group"].items():
                    if group_name == "prod" and "dependencies" in group_config:
                        for package, version in group_config["dependencies"].items():
                            if isinstance(version, str):
                                pip_version = self._convert_poetry_version_to_pip(
                                    version
                                )
                                dependencies.append(f"{package}{pip_version}")
                            else:
                                dependencies.append(package)

        # Write requirements.txt
        with open(requirements_file, "w") as f:
            for dep in dependencies:
                f.write(f"{dep}\n")

        print(f"✅ Generated requirements.txt with {len(dependencies)} dependencies")

    def _convert_poetry_version_to_pip(self, version: str) -> str:
        """Convert Poetry version format to pip format."""
        # Handle exact versions (no prefix)
        if not version.startswith(("^", "~", ">=", "<=", "==")):
            return f"=={version}"

        # Remove Poetry-specific version constraints
        version = version.replace("^", ">=")
        version = version.replace("~", ">=")

        # Handle version ranges
        if "||" in version:
            # Convert ">=1.0,<2.0" format
            parts = version.split("||")
            if len(parts) == 2:
                return f">={parts[0].strip()},<{parts[1].strip()}"

        return version

    def copy_application_code(self) -> None:
        """Copy application code to build directory."""
        print("📁 Copying application code...")

        # Copy app directory
        app_source = self.project_root / "app"
        app_dest = self.build_dir / "app"

        if app_source.exists():
            shutil.copytree(app_source, app_dest, dirs_exist_ok=True)

        # Copy lambda handlers
        handler_files = ["lambda_handler.py", "migration_lambda_handler.py"]
        for handler_file in handler_files:
            handler_source = self.project_root / handler_file
            if handler_source.exists():
                shutil.copy2(handler_source, self.build_dir)
                print(f"✅ Copied {handler_file}")
            else:
                print(f"⚠️ {handler_file} not found")

        # Copy alembic files for migration handler
        alembic_files = ["alembic.ini", "alembic"]
        for alembic_item in alembic_files:
            alembic_source = self.project_root / alembic_item
            if alembic_source.exists():
                if alembic_source.is_file():
                    shutil.copy2(alembic_source, self.build_dir)
                else:
                    shutil.copytree(alembic_source, self.build_dir / alembic_item, dirs_exist_ok=True)
                print(f"✅ Copied {alembic_item}")
            else:
                print(f"⚠️ {alembic_item} not found")

    def remove_unnecessary_files(self) -> None:
        """Remove unnecessary files to reduce package size."""
        print("🗑️  Removing unnecessary files...")
        # "*.dist-info",
        # "*.egg-info",

        patterns_to_remove = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "tests",
            "test_*",
            "*_test*",
            "docs",
            "documentation",
            "*.md",
            "*.rst",
            "*.txt",
            "README*",
            "CHANGELOG*",
            "LICENSE*",
            ".git",
            ".gitignore",
            ".env*",
            "*.log",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".mypy_cache",
            ".ruff_cache",
            "node_modules",
            "venv*",
            ".venv",
            "dist",
            "build",
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "*~",
            "*.bak",
            "*.tmp",
            "*.orig",
            "*.rej",
            ".DS_Store",
            "Thumbs.db",
        ]

        # Don't remove files from packages that might have internal dependencies
        packages_to_preserve = [
            "anyio",
            "fastapi",
            "pydantic",
            "mangum",
            "openai",
            "langchain",
            "langgraph",
            "stripe",
        ]

        for pattern in patterns_to_remove:
            for file_path in self.build_dir.rglob(pattern):
                # Skip files from packages we want to preserve
                if any(pkg in str(file_path) for pkg in packages_to_preserve):
                    continue
                
                # Preserve stripe.test_helpers as it's needed by the application
                if "stripe" in str(file_path) and "test_helpers" in str(file_path):
                    print(f"🔒 Keeping essential module: {file_path}")
                    continue

                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)

    def optimize_python_packages(self) -> None:
        """Optimize Python packages by removing unnecessary components."""
        print("🔧 Optimizing Python packages...")

        # Remove test files from packages
        for package_dir in self.build_dir.iterdir():
            if package_dir.is_dir() and not package_dir.name.startswith("."):
                self._optimize_package(package_dir)

        # Special handling for botocore.docs and boto3.docs - ensure they're preserved
        botocore_docs_path = self.build_dir / "botocore" / "docs"
        if not botocore_docs_path.exists():
            print("⚠️ botocore.docs missing, attempting to restore...")
            self._restore_missing_docs_module("botocore", "docs")

        boto3_docs_path = self.build_dir / "boto3" / "docs"
        if not boto3_docs_path.exists():
            print("⚠️ boto3.docs missing, attempting to restore...")
            self._restore_missing_docs_module("boto3", "docs")

    def _optimize_package(self, package_dir: Path) -> None:
        """Optimize a single package directory."""
        # Remove test directories and helper files, but preserve essential modules
        test_patterns = ["tests", "test_*", "*_test*", "helper*", "*_helper*", "helpers"]
        for pattern in test_patterns:
            for test_dir in package_dir.rglob(pattern):
                if test_dir.is_dir():
                    # Preserve stripe.test_helpers as it's needed by the application
                    if "stripe" in str(test_dir) and "test_helpers" in str(test_dir):
                        print(f"🔒 Keeping essential module: {test_dir}")
                        continue
                    shutil.rmtree(test_dir, ignore_errors=True)

        # Remove documentation (but keep essential modules like botocore.docs)
        doc_patterns = ["documentation", "*.md", "*.rst", "*.txt"]
        for pattern in doc_patterns:
            for doc_file in package_dir.rglob(pattern):
                if doc_file.is_file():
                    doc_file.unlink()
                elif doc_file.is_dir():
                    shutil.rmtree(doc_file, ignore_errors=True)

        # Special handling for docs directories - keep botocore.docs
        for docs_dir in package_dir.rglob("docs"):
            if docs_dir.is_dir():
                # Check if this is botocore.docs
                if "botocore" in str(docs_dir) and docs_dir.name == "docs":
                    print(f"🔒 Keeping essential module: {docs_dir}")
                    continue
                # Remove other docs directories
                shutil.rmtree(docs_dir, ignore_errors=True)

    def _restore_missing_docs_module(self, package_name: str, module_name: str) -> None:
        """Restore missing docs module by finding it in the current Python environment."""
        try:
            # Try to import the module to get its file path
            import importlib.util
            module_spec = importlib.util.find_spec(f"{package_name}.{module_name}")

            if module_spec and module_spec.origin:
                # Get the module directory
                module_dir = Path(module_spec.origin).parent
                target_dir = self.build_dir / package_name / module_name

                if module_dir.exists() and module_dir.is_dir():
                    shutil.copytree(module_dir, target_dir)
                    print(f"✅ Restored {package_name}.{module_name} from {module_dir}")
                else:
                    print(f"❌ Module directory not found: {module_dir}")
            else:
                print(f"❌ Could not find {package_name}.{module_name} in current environment")

        except Exception as e:
            print(f"❌ Error restoring {package_name}.{module_name}: {e}")

    def strip_shared_libraries(self) -> None:
        """Strip symbols from .so files to reduce package size."""
        print("🔧 Stripping symbols from .so files...")
        
        # Calculate size before stripping
        print("📊 Calculating size before stripping...")
        so_files_before = {}
        total_size_before = 0
        for so_file in self.build_dir.rglob("*.so"):
            if so_file.is_file():
                size = so_file.stat().st_size
                so_files_before[str(so_file)] = size
                total_size_before += size
        
        print(f"📊 Found {len(so_files_before)} .so files with total size: {total_size_before/1024/1024:.1f}MB")
        
        # Find and strip all .so files
        try:
            result = subprocess.run(  # nosec B607, B603
                ["find", str(self.build_dir), "-name", "*.so", "-exec", "strip", "--strip-unneeded", "{}", "+"],
                capture_output=True,
                text=True,
                check=True,
            )
            print("✅ Successfully stripped symbols from .so files")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Failed to strip some .so files: {e}")
            print(f"Error output: {e.stderr}")
        except FileNotFoundError:
            print("⚠️ Warning: 'strip' command not found. Skipping symbol stripping.")
            return
        
        # Calculate size after stripping
        print("📊 Calculating size after stripping...")
        total_size_after = 0
        stripped_count = 0
        total_saved = 0
        
        for so_file in self.build_dir.rglob("*.so"):
            if so_file.is_file():
                size_after = so_file.stat().st_size
                total_size_after += size_after
                
                # Check if this file was stripped
                file_path_str = str(so_file)
                if file_path_str in so_files_before:
                    size_before = so_files_before[file_path_str]
                    if size_after < size_before:
                        saved = size_before - size_after
                        total_saved += saved
                        stripped_count += 1
                        # Only print files with significant savings (> 0.5MB)
                        if saved > 524288:  # 0.5MB in bytes
                            print(f"🔧 Stripped {so_file.name}: {size_before/1024/1024:.1f}MB → {size_after/1024/1024:.1f}MB (saved {saved/1024/1024:.1f}MB)")
        
        print(f"📊 Stripping results:")
        print(f"   • Files processed: {len(so_files_before)}")
        print(f"   • Files actually stripped: {stripped_count}")
        print(f"   • Total size before: {total_size_before/1024/1024:.1f}MB")
        print(f"   • Total size after: {total_size_after/1024/1024:.1f}MB")
        print(f"   • Total saved: {total_saved/1024/1024:.1f}MB")

    def create_zip_package(self, package_name: str = "lambda-package.zip") -> Path:
        """Create ZIP package for Lambda deployment."""
        print(f"📦 Creating ZIP package: {package_name}")

        zip_path = self.dist_dir / package_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.build_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)

        # Calculate size
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"📊 Package size: {size_mb:.2f} MB")

        if size_mb > 250:
            print("⚠️  WARNING: Package size exceeds Lambda's 250MB limit!")

        return zip_path

    def create_socket_lambda_package(self) -> Path:
        """Create separate socket-lambda package with minimal dependencies."""
        print("🔌 Creating Socket Lambda package...")
        
        # Clean and create socket lambda build directory
        socket_build_dir = self.project_root / "build-socket"
        if socket_build_dir.exists():
            shutil.rmtree(socket_build_dir)
        socket_build_dir.mkdir(parents=True, exist_ok=True)
        
        # Install socket-lambda dependencies
        self._install_socket_lambda_dependencies(socket_build_dir)
        
        # Copy lambda_function.py
        lambda_source = self.project_root / "lambda_function.py"
        if lambda_source.exists():
            shutil.copy2(lambda_source, socket_build_dir)
            print("✅ Copied lambda_function.py")
        else:
            print("⚠️ lambda_function.py not found")
        
        # Create socket lambda ZIP package
        socket_zip_path = self.dist_dir / "socket-lambda-package.zip"
        with zipfile.ZipFile(socket_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in socket_build_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(socket_build_dir)
                    zipf.write(file_path, arcname)
        
        # Calculate size
        size_mb = socket_zip_path.stat().st_size / (1024 * 1024)
        print(f"📊 Socket Lambda package size: {size_mb:.2f} MB")
        
        if size_mb > 250:
            print("⚠️  WARNING: Socket Lambda package size exceeds Lambda's 250MB limit!")
        
        # Clean up socket build directory
        shutil.rmtree(socket_build_dir)
        
        return socket_zip_path

    def _install_socket_lambda_dependencies(self, socket_build_dir: Path) -> None:
        """Install socket-lambda specific dependencies."""
        print("📦 Installing Socket Lambda dependencies...")
        
        # Generate requirements for socket-lambda group
        requirements_file = socket_build_dir / "socket-requirements.txt"
        # self._generate_socket_requirements_file(requirements_file)
        
        subprocess.run(
            [
                "poetry",
                "export",
                "-f",
                "requirements.txt",
                "--output",
                str(requirements_file),
                "--without-hashes",
                "--only",
                "socket-lambda",
            ],
            cwd=self.project_root,
            check=True,
        )        
        # Install to socket build directory
        subprocess.run(  # nosec B607, B603
            [
                "pip",
                "install",
                "-r",
                str(requirements_file),
                "-t",
                str(socket_build_dir),
            ],
            check=True,
        )

    def _generate_socket_requirements_file(self, requirements_file: Path) -> None:
        """Generate requirements.txt for socket-lambda group."""
        print("📋 Generating Socket Lambda requirements.txt...")
        
        # Read pyproject.toml
        import tomllib
        
        with open(self.project_root / "pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        # Extract socket-lambda dependencies
        dependencies = []
        if "tool" in config and "poetry" in config["tool"]:
            poetry_config = config["tool"]["poetry"]
            
            # Get socket-lambda group dependencies
            if "group" in poetry_config:
                for group_name, group_config in poetry_config["group"].items():
                    if group_name == "socket-lambda" and "dependencies" in group_config:
                        for package, version in group_config["dependencies"].items():
                            if isinstance(version, str):
                                pip_version = self._convert_poetry_version_to_pip(version)
                                dependencies.append(f"{package}{pip_version}")
                            else:
                                dependencies.append(package)
        
        # Write requirements.txt
        with open(requirements_file, "w") as f:
            for dep in dependencies:
                f.write(f"{dep}\n")
        
        print(f"✅ Generated Socket Lambda requirements.txt with {len(dependencies)} dependencies")

    def create_dockerfile(self) -> None:
        """Create optimized Dockerfile for Lambda deployment."""
        dockerfile_content = """# Multi-stage build for Lambda optimization
FROM python:3.11-slim as builder

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install production dependencies only
RUN poetry install --only=prod --no-dev

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ /app/app/
COPY lambda_handler.py /app/

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Lambda handler
CMD ["lambda_handler.handler"]
"""

        dockerfile_path = self.project_root / "Dockerfile.lambda"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        print(f"🐳 Dockerfile created: {dockerfile_path}")

    def create_lambda_layer(self) -> Path:
        """Create Lambda layer with dependencies."""
        print("🔧 Creating Lambda layer...")

        layer_dir = self.build_dir / "lambda-layer"
        python_dir = layer_dir / "python"
        python_dir.mkdir(parents=True, exist_ok=True)

        # Install dependencies to layer
        requirements_file = self.build_dir / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(  # nosec B607, B603
                [
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                    "-t",
                    str(python_dir),
                ],
                check=True,
            )

        # Remove unnecessary files from layer
        self._clean_layer_directory(python_dir)

        # Create layer ZIP
        layer_zip = self.dist_dir / "lambda-layer.zip"
        with zipfile.ZipFile(layer_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in layer_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(layer_dir)
                    zipf.write(file_path, arcname)

        layer_size_mb = layer_zip.stat().st_size / (1024 * 1024)
        print(f"📊 Layer size: {layer_size_mb:.2f} MB")

        return layer_zip

    def _clean_layer_directory(self, layer_dir: Path) -> None:
        """Clean Lambda layer directory."""
        patterns_to_remove = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.dist-info",
            "*.egg-info",
            "tests",
            "test_*",
            "docs",
            "*.md",
            "*.rst",
            "*.txt",
        ]

        for pattern in patterns_to_remove:
            for file_path in layer_dir.rglob(pattern):
                # Preserve stripe.test_helpers as it's needed by the application
                if "stripe" in str(file_path) and "test_helpers" in str(file_path):
                    print(f"🔒 Keeping essential module: {file_path}")
                    continue
                    
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)


@click.command()  # type: ignore[misc]
@click.option("--project-root", default=".", help="Project root directory")  # type: ignore[misc]
@click.option(
    "--package-name", default="lambda-package.zip", help="Output package name"
)  # type: ignore[misc]
@click.option("--create-layer", is_flag=True, help="Create Lambda layer")  # type: ignore[misc]
@click.option("--create-dockerfile", is_flag=True, help="Create optimized Dockerfile")  # type: ignore[misc]
@click.option("--clean-only", is_flag=True, help="Only clean build directories")  # type: ignore[misc]
def main(
    project_root: str,
    package_name: str,
    create_layer: bool,
    create_dockerfile: bool,
    clean_only: bool,
) -> None:
    """Build optimized Lambda deployment package."""

    project_path = Path(project_root)

    if not (project_path / "pyproject.toml").exists():
        click.echo("❌ pyproject.toml not found in the specified directory")
        click.echo("💡 Make sure you're running this from the project root directory")
        sys.exit(1)

    builder = LambdaPackageBuilder(project_path)

    try:
        # Clean build directories
        builder.clean_build_directories()

        if clean_only:
            click.echo("✅ Build directories cleaned")
            return

        # Build package
        builder.install_production_dependencies()
        builder.copy_application_code()
        builder.remove_unnecessary_files()
        builder.optimize_python_packages()
        builder.strip_shared_libraries()

        # Create ZIP package
        zip_path = builder.create_zip_package(package_name)
        click.echo(f"✅ Lambda package created: {zip_path}")

        # Create Socket Lambda package
        socket_zip_path = builder.create_socket_lambda_package()
        click.echo(f"✅ Socket Lambda package created: {socket_zip_path}")

        # Create Lambda layer if requested
        if create_layer:
            layer_path = builder.create_lambda_layer()
            click.echo(f"✅ Lambda layer created: {layer_path}")

        # Create Dockerfile if requested
        if create_dockerfile:
            builder.create_dockerfile()

        click.echo("\n📋 DEPLOYMENT READY:")
        click.echo(f"1. Lambda package: {zip_path}")
        click.echo(f"2. Socket Lambda package: {socket_zip_path}")
        if create_layer:
            click.echo(f"3. Lambda layer: {layer_path}")
        if create_dockerfile:
            click.echo("4. Dockerfile: Dockerfile.lambda")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
