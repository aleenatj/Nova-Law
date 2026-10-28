# Lambda Optimization Guide

## Overview

This guide provides comprehensive instructions for optimizing your FastAPI application for AWS Lambda deployment while staying within the 250MB package size limit.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Tools Overview](#tools-overview)
3. [Development Workflow](#development-workflow)
4. [Deployment Process](#deployment-process)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Quick Start

### Prerequisites

```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment
source venv-be/bin/activate

# Verify Poetry is available
poetry --version
```

### Basic Commands

```bash
# Analyze current package size and dependencies
python scripts/lambda_tools.py analyze

# Build optimized Lambda package
python scripts/lambda_tools.py build --create-layer

# Run full optimization pipeline
python scripts/lambda_tools.py optimize

# Check package size for CI/CD
python scripts/lambda_tools.py check --fail-on-limit
```

## Tools Overview

### 1. Lambda Optimizer (`scripts/lambda_optimizer.py`)

**Purpose**: Analyzes dependencies and identifies optimization opportunities.

**Features**:
- Calculates package sizes
- Identifies dependencies >10MB
- Suggests lighter alternatives
- Generates optimized `pyproject.toml`
- Creates Lambda layer builder script

**Usage**:
```bash
# Basic analysis
python scripts/lambda_optimizer.py

# Generate optimized config
python scripts/lambda_optimizer.py --generate-optimized

# Create layer builder script
python scripts/lambda_optimizer.py --create-layer-script

# Custom threshold for large dependencies
python scripts/lambda_optimizer.py --threshold-mb 5
```

### 2. Lambda Package Builder (`scripts/build_lambda_package.py`)

**Purpose**: Creates optimized deployment packages for Lambda.

**Features**:
- Builds ZIP packages for Lambda deployment
- Creates Lambda layers for large dependencies
- Generates optimized Dockerfiles
- Removes unnecessary files (tests, docs, cache)
- Optimizes Python packages

**Usage**:
```bash
# Basic build
python scripts/build_lambda_package.py

# Build with Lambda layer
python scripts/build_lambda_package.py --create-layer

# Build with Dockerfile
python scripts/build_lambda_package.py --create-dockerfile

# Custom package name
python scripts/build_lambda_package.py --package-name my-app.zip

# Clean build directories only
python scripts/build_lambda_package.py --clean-only
```

### 3. CI Size Checker (`scripts/ci_size_check.py`)

**Purpose**: Integrates with CI/CD pipelines for automated size monitoring.

**Features**:
- Monitors package size in CI/CD
- Generates GitHub comments for PRs
- Creates Slack notifications
- Checks dependency groups
- Fails builds on size violations

**Usage**:
```bash
# Basic size check
python scripts/ci_size_check.py

# Check with dependency groups
python scripts/ci_size_check.py --check-groups

# Generate GitHub comment
python scripts/ci_size_check.py --github-comment

# Generate Slack notification
python scripts/ci_size_check.py --slack-notification

# Fail build if over limit
python scripts/ci_size_check.py --fail-on-limit
```

### 4. Lambda Tools Wrapper (`scripts/lambda_tools.py`)

**Purpose**: Provides easy access to all optimization tools.

**Features**:
- Single command interface
- Full optimization pipeline
- Helpful examples and documentation

**Usage**:
```bash
# Show help
python scripts/lambda_tools.py

# Analyze dependencies
python scripts/lambda_tools.py analyze

# Build package
python scripts/lambda_tools.py build

# Create layer
python scripts/lambda_tools.py layer

# Run size checks
python scripts/lambda_tools.py check

# Full optimization pipeline
python scripts/lambda_tools.py optimize
```

## Development Workflow

### Adding New Dependencies

1. **Add with appropriate group**:
   ```bash
   # Production dependencies
   poetry add --group prod fastapi uvicorn pydantic

   # Development dependencies
   poetry add --group dev pytest black ruff mypy

   # Test dependencies
   poetry add --group test pytest-cov httpx
   ```

2. **Check size impact**:
   ```bash
   python scripts/lambda_tools.py analyze
   ```

3. **If package is large, consider alternatives**:
   ```bash
   # Example: Replace pandas with polars
   poetry remove pandas
   poetry add --group prod polars
   ```

### Before Committing

1. **Run size check**:
   ```bash
   python scripts/lambda_tools.py check --fail-on-limit
   ```

2. **Ensure package size is within limits** (250MB)

3. **Commit changes**

### Regular Maintenance

1. **Weekly analysis**:
   ```bash
   python scripts/lambda_tools.py analyze
   ```

2. **Review large dependencies**:
   ```bash
   python scripts/lambda_optimizer.py --threshold-mb 10
   ```

3. **Update dependencies**:
   ```bash
   poetry update
   python scripts/lambda_tools.py check
   ```

## Deployment Process

### Local Testing

1. **Build optimized package**:
   ```bash
   python scripts/lambda_tools.py build --create-layer
   ```

2. **Check package size**:
   ```bash
   ls -lh dist/lambda-package.zip
   ```

3. **Test locally** (if needed):
   ```bash
   # Extract and test
   unzip dist/lambda-package.zip -d test-package/
   cd test-package/
   python -c "import app; print('Package works!')"
   ```

### Lambda Deployment

1. **Deploy function code**:
   ```bash
   aws lambda update-function-code \
     --function-name nova-law-api \
     --zip-file fileb://dist/lambda-package.zip
   ```

2. **Deploy Lambda layer** (if created):
   ```bash
   aws lambda publish-layer-version \
     --layer-name nova-law-dependencies \
     --description "Dependencies for Nova Law API" \
     --zip-file fileb://dist/lambda-layer.zip \
     --compatible-runtimes python3.11
   ```

3. **Attach layer to function** (if using layers):
   ```bash
   aws lambda update-function-configuration \
     --function-name nova-law-api \
     --layers arn:aws:lambda:region:account:layer:nova-law-dependencies:1
   ```

### Docker Deployment

1. **Build Docker image**:
   ```bash
   docker build -f Dockerfile.lambda -t nova-law-lambda .
   ```

2. **Deploy to ECR**:
   ```bash
   aws ecr get-login-password --region region | docker login --username AWS --password-stdin account.dkr.ecr.region.amazonaws.com
   docker tag nova-law-lambda:latest account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest
   docker push account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest
   ```

3. **Update Lambda function**:
   ```bash
   aws lambda update-function-code \
     --function-name nova-law-api \
     --image-uri account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest
   ```

## CI/CD Integration

### GitHub Actions Setup

The workflow (`.github/workflows/lambda-deployment.yml`) automatically:

1. **Analyzes package size** on every PR
2. **Comments on PRs** with size information
3. **Fails builds** if package exceeds 250MB
4. **Creates optimized packages** for deployment
5. **Deploys to Lambda** on main branch

### Required Secrets

Add these secrets to your GitHub repository:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)

### Manual CI Checks

```bash
# Run size analysis
python scripts/ci_size_check.py --check-groups

# Generate GitHub comment
python scripts/ci_size_check.py --github-comment

# Generate Slack notification
python scripts/ci_size_check.py --slack-notification
```

## Troubleshooting

### Common Issues

#### Poetry Not Found
```bash
# Solution: Activate virtual environment
source venv-be/bin/activate
```

#### Package Too Large
```bash
# Analyze large dependencies
python scripts/lambda_optimizer.py --threshold-mb 10

# Consider alternatives
poetry remove heavy-package
poetry add --group prod light-alternative
```

#### Build Failures
```bash
# Clean build directories
python scripts/build_lambda_package.py --clean-only

# Rebuild with fresh dependencies
poetry lock --no-update
python scripts/lambda_tools.py build
```

#### Runtime Errors
- Check Lambda layer compatibility
- Verify Python version matches (3.11)
- Ensure all dependencies are included
- Check for missing native extensions

#### CI/CD Failures
```bash
# Check package size locally
python scripts/lambda_tools.py check --fail-on-limit

# Verify dependency groups
python scripts/ci_size_check.py --check-groups
```

### Debug Commands

```bash
# Check Poetry version
poetry --version

# List all dependencies
poetry show --tree

# Check virtual environment
which python
which poetry

# Verify package structure
ls -la dist/
```

## Best Practices

### Dependency Management

1. **Use Poetry groups**:
   ```bash
   poetry add --group prod <package>  # Production only
   poetry add --group dev <package>   # Development only
   poetry add --group test <package>  # Testing only
   ```

2. **Regular audits**:
   ```bash
   # Monthly dependency review
   poetry show --tree
   python scripts/lambda_tools.py analyze
   ```

3. **Consider alternatives for large packages**:
   | Heavy Package | Light Alternative | Size Reduction |
   |---------------|-------------------|----------------|
   | `pandas` | `polars` | 50-80% |
   | `matplotlib` | `plotly` | 60-70% |
   | `scipy` | `scipy-lite` | 40-60% |

### Build Optimization

1. **Use production dependencies only**:
   ```bash
   poetry install --only=prod
   ```

2. **Remove unnecessary files**:
   - Tests and test data
   - Documentation
   - Cache files
   - Development tools

3. **Use Lambda layers for large dependencies**:
   ```bash
   python scripts/lambda_tools.py build --create-layer
   ```

### Monitoring

1. **Set up alerts** for package size increases
2. **Monitor dependency updates** for size impact
3. **Regular size trend analysis**
4. **Automated CI/CD checks**

### Security

1. **Use dependency scanning**:
   ```bash
   poetry run bandit -r app/
   ```

2. **Keep dependencies updated**:
   ```bash
   poetry update
   python scripts/lambda_tools.py check
   ```

3. **Review security advisories** regularly

## Reference

### File Structure

```
backend/
├── scripts/                          # Optimization tools
│   ├── lambda_optimizer.py           # Dependency analysis
│   ├── build_lambda_package.py       # Package building
│   ├── ci_size_check.py              # CI/CD integration
│   ├── lambda_tools.py               # Wrapper script
│   └── makefile                      # Automation commands
├── .github/workflows/                # CI/CD pipeline
│   └── lambda-deployment.yml
├── pyproject.lambda.toml            # Optimized config template
├── docs/guides/                      # Documentation
│   └── lambda-optimization-guide.md  # This guide
└── README_LAMBDA_OPTIMIZATION.md    # Quick reference
```

### Environment Variables

```bash
# Required for deployment
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Optional for notifications
SLACK_WEBHOOK_URL=your-slack-webhook
GITHUB_TOKEN=your-github-token
```

### Size Limits

- **Lambda ZIP package**: 250MB (unzipped)
- **Lambda layer**: 250MB (unzipped)
- **Lambda container**: 10GB
- **Warning threshold**: 200MB (configurable)

### Performance Tips

1. **Use connection pooling** for databases
2. **Implement caching** strategies
3. **Use async operations** where possible
4. **Optimize memory usage**
5. **Monitor cold start times**

## Support

For issues or questions:

1. Check this guide first
2. Review the troubleshooting section
3. Check the generated logs in `logs/`
4. Run debug commands to identify issues
5. Consult AWS Lambda documentation

---

*Last updated: [Current Date]*
*Version: 1.0*
