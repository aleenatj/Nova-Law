# Makefile for Lambda Package Optimization
# Usage: make <target>

.PHONY: help analyze build clean layer docker test ci-check optimize

# Default target
help:
	@echo "Available targets:"
	@echo "  analyze     - Analyze package size and dependencies"
	@echo "  build       - Build optimized Lambda package"
	@echo "  layer       - Create Lambda layer"
	@echo "  docker      - Build Docker image for Lambda"
	@echo "  clean       - Clean build artifacts"
	@echo "  test        - Run tests"
	@echo "  ci-check    - Run CI size checks"
	@echo "  optimize    - Run full optimization pipeline"

# Analyze dependencies and package size
analyze:
	@echo "🔍 Analyzing package size and dependencies..."
	python scripts/lambda_optimizer.py --generate-optimized --create-layer-script
	@echo "✅ Analysis complete"

# Build optimized Lambda package
build:
	@echo "📦 Building optimized Lambda package..."
	python scripts/build_lambda_package.py --create-layer --create-dockerfile
	@echo "✅ Build complete"

# Create Lambda layer
layer:
	@echo "🔧 Creating Lambda layer..."
	python scripts/build_lambda_package.py --create-layer
	@echo "✅ Layer created"

# Build Docker image for Lambda
docker:
	@echo "🐳 Building Docker image for Lambda..."
	docker build -f Dockerfile.lambda -t nova-law-lambda .
	@echo "✅ Docker image built"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	python scripts/build_lambda_package.py --clean-only
	rm -rf build/ dist/ *.zip lambda-layer/
	@echo "✅ Clean complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "✅ Tests complete"

# Run CI size checks
ci-check:
	@echo "🔍 Running CI size checks..."
	python scripts/ci_size_check.py --check-groups --fail-on-limit
	@echo "✅ CI checks complete"

# Run full optimization pipeline
optimize: clean analyze build ci-check
	@echo "🚀 Full optimization pipeline complete"

# Development workflow
dev-setup:
	@echo "🔧 Setting up development environment..."
	poetry install --with dev,test
	pre-commit install
	@echo "✅ Development setup complete"

# Production dependencies only
prod-install:
	@echo "📦 Installing production dependencies only..."
	poetry install --only=prod
	@echo "✅ Production dependencies installed"

# Export requirements for deployment
export-requirements:
	@echo "📋 Exporting requirements..."
	poetry export --only=prod --without-hashes --format=requirements.txt > requirements.txt
	@echo "✅ Requirements exported to requirements.txt"

# Check package size
size-check:
	@echo "📊 Checking package size..."
	python scripts/ci_size_check.py --github-comment
	@echo "✅ Size check complete"

# Quick build for testing
quick-build:
	@echo "⚡ Quick build for testing..."
	python scripts/build_lambda_package.py --package-name quick-test.zip
	@echo "✅ Quick build complete"

# Analyze large dependencies
analyze-large:
	@echo "🔍 Analyzing large dependencies..."
	python scripts/lambda_optimizer.py --threshold-mb 5
	@echo "✅ Large dependency analysis complete"

# Create deployment package
deploy-package: clean build
	@echo "🚀 Creating deployment package..."
	@echo "Package ready for deployment in dist/"
	@echo "✅ Deployment package created"

# Lambda-specific optimizations
lambda-optimize:
	@echo "🔧 Running Lambda-specific optimizations..."
	# Remove unnecessary files
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	# Remove test files
	find . -path "*/tests/*" -delete
	find . -path "*/test_*" -delete
	# Remove documentation
	find . -path "*/docs/*" -delete
	find . -name "*.md" -delete
	@echo "✅ Lambda optimizations complete"

# Check for unused dependencies
check-unused:
	@echo "🔍 Checking for unused dependencies..."
	poetry show --tree
	@echo "✅ Dependency tree displayed"

# Security scan
security-scan:
	@echo "🔒 Running security scan..."
	poetry run bandit -r app/ -f json -o bandit-report.json
	@echo "✅ Security scan complete"

# Format and lint
format:
	@echo "🎨 Formatting code..."
	poetry run black .
	poetry run ruff format .
	@echo "✅ Code formatted"

# Lint check
lint:
	@echo "🔍 Running linters..."
	poetry run ruff check .
	poetry run mypy app/
	@echo "✅ Lint check complete"

# Full quality check
quality: format lint test security-scan
	@echo "✅ Quality checks complete"

# Help with examples
examples:
	@echo "📚 Usage examples:"
	@echo ""
	@echo "Analyze current package:"
	@echo "  make analyze"
	@echo ""
	@echo "Build for Lambda deployment:"
	@echo "  make build"
	@echo ""
	@echo "Create Lambda layer:"
	@echo "  make layer"
	@echo ""
	@echo "Run CI checks:"
	@echo "  make ci-check"
	@echo ""
	@echo "Full optimization:"
	@echo "  make optimize"
