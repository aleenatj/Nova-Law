# Deployment Guide

This document provides comprehensive instructions for deploying the Nova Law AI Backend to different environments using GitHub Actions.

## 🏗️ Architecture Overview

The deployment system supports multiple environments with the following characteristics:

- **Environment-specific secrets** stored in GitHub Environments
- **Branch-based deployment** with automatic environment detection
- **Secure DATABASE_URL construction** from individual secrets
- **Database migrations** using Alembic
- **Lambda function and layer management** per environment

## 🌿 Branch to Environment Mapping

### Current Mapping (Interim)
| Branch | Environment | Lambda Function | Lambda Layer | Purpose |
|--------|-------------|-----------------|--------------|---------|
| `main` | `staging` | `nova-law-api-staging` | `nova-law-dependencies-staging` | Staging/Testing |
| `staging` | `staging` | `nova-law-api-staging` | `nova-law-dependencies-staging` | Staging/Testing |
| `develop` | `staging` | `nova-law-api-staging` | `nova-law-dependencies-staging` | Development |

### Future Mapping (When main becomes production)
| Branch | Environment | Lambda Function | Lambda Layer | Purpose |
|--------|-------------|-----------------|--------------|---------|
| `main` | `production` | `nova-law-api-production` | `nova-law-dependencies-production` | Production |
| `staging` | `staging` | `nova-law-api-staging` | `nova-law-dependencies-staging` | Staging/Testing |
| `develop` | `staging` | `nova-law-api-staging` | `nova-law-dependencies-staging` | Development |

## 🔧 GitHub Environment Setup

### 1. Create GitHub Environments

Navigate to your GitHub repository → Settings → Environments and create:

#### Staging Environment
- **Name**: `staging`
- **Protection rules**: Optional (recommended for staging)
- **Required reviewers**: Optional

#### Production Environment (Future)
- **Name**: `production`
- **Protection rules**: Required
- **Required reviewers**: Required (at least 1)

### 2. Configure Environment Secrets

For each environment, add the following secrets:

#### Required Secrets for All Environments
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Database Configuration (Individual parameters for security)
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=your-database-name
```

#### Environment-Specific Secrets
- **Staging**: Use staging database and AWS resources
- **Production**: Use production database and AWS resources

### 3. Environment Variables (Optional)
You can also set environment variables for non-sensitive configuration:

```bash
# Environment-specific variables
ENVIRONMENT=staging
LOG_LEVEL=INFO
DEBUG=false
```

## 🔄 Workflow Configuration

### Branch Mapping Logic

The workflow automatically determines the environment based on the branch name:

```bash
# Current mapping (in .github/workflows/deploy.yml)
case "${{ github.ref_name }}" in
  "main")
    echo "environment=staging"  # TODO: Change to production
    ;;
  "staging")
    echo "environment=staging"
    ;;
  "develop")
    echo "environment=staging"
    ;;
esac
```

### To Change Main to Production

When ready to promote main to production, update the mapping in `.github/workflows/deploy.yml`:

```bash
case "${{ github.ref_name }}" in
  "main")
    echo "environment=production"  # Changed from staging
    echo "lambda-function-name=nova-law-api-production"  # Changed
    echo "lambda-layer-name=nova-law-dependencies-production"  # Changed
    ;;
  # ... rest remains the same
esac
```

## 🚀 Deployment Process

### Automatic Deployment
1. **Push to main/staging/develop** → Triggers deployment to staging
2. **Workflow determines environment** → Based on branch mapping
3. **Build package** → Creates Lambda deployment package
4. **Security scan** → Runs Bandit security analysis
5. **Deploy to Lambda** → Updates function code and configuration
6. **Database migration** → Runs Alembic migrations
7. **Connection verification** → Verifies database connectivity

### Manual Deployment
Use the "workflow_dispatch" trigger in GitHub Actions:
1. Go to Actions → Environment-Specific Deployment
2. Click "Run workflow"
3. Select environment (staging/production)
4. Click "Run workflow"

## 🔒 Security Features

### DATABASE_URL Construction
The workflow constructs the DATABASE_URL dynamically from individual secrets:

```bash
# Secure construction (no hardcoded credentials)
echo "DATABASE_URL=postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASSWORD }}@${{ secrets.DB_HOST }}:${{ secrets.DB_PORT }}/${{ secrets.DB_NAME }}" >> $GITHUB_ENV
```

### Environment-Specific Secrets
- Each environment has its own set of secrets
- Secrets are scoped to the environment using `environment:` in the workflow
- No cross-environment secret sharing

## 🧪 Local Testing Guide

### Prerequisites
```bash
# Install dependencies
poetry install --with migrate

# Set up environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=nova_law_db
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
```

### Test Database Connection
```bash
# Test database configuration
poetry run python -c "
from app.core.config import settings
print(f'Database URL: {settings.database_url}')
"

# Test database connection
poetry run python -c "
from app.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connection successful')
"
```

### Test Alembic Migrations
```bash
# Check current migration status
poetry run alembic current

# Run migrations
poetry run alembic upgrade head

# Create new migration (if needed)
poetry run alembic revision --autogenerate -m "Description of changes"

# Downgrade (if needed)
poetry run alembic downgrade -1
```

### Test Lambda Package Build
```bash
# Build package locally
poetry run python scripts/build_lambda_package.py

# Check package size
ls -lh dist/lambda-package.zip

# Test package contents
unzip -l dist/lambda-package.zip
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check environment variables
echo $DATABASE_URL

# Test connection manually
psql "postgresql://user:pass@host:port/db" -c "SELECT 1"
```

#### 2. Lambda Deployment Failed
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Lambda function exists
aws lambda get-function --function-name nova-law-api-staging
```

#### 3. Migration Failed
```bash
# Check Alembic configuration
poetry run alembic show

# Check migration history
poetry run alembic history
```

### Debug Workflow
1. **Check workflow logs** → Actions → Workflow runs
2. **Verify secrets** → Settings → Environments → Secrets
3. **Test locally** → Use local testing guide above
4. **Check AWS resources** → Verify Lambda functions and databases exist

## 📋 Checklist for New Environment

- [ ] Create GitHub Environment
- [ ] Configure environment secrets
- [ ] Create AWS Lambda function
- [ ] Create database instance
- [ ] Update branch mapping (if needed)
- [ ] Test deployment manually
- [ ] Verify database migrations
- [ ] Test application functionality

## 🔄 Promoting Main to Production

When ready to promote main to production:

1. **Create production environment** in GitHub
2. **Configure production secrets**
3. **Create production Lambda function**
4. **Set up production database**
5. **Update workflow mapping** (change main → production)
6. **Test deployment** to production
7. **Update documentation**

### Minimal Steps Required
```bash
# 1. Update workflow mapping
# In .github/workflows/deploy.yml, change:
echo "environment=production"  # instead of staging

# 2. Add production secrets to GitHub Environment
# 3. Create production AWS resources
# 4. Test deployment
```

## 📚 Additional Resources

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [AWS Lambda Deployment Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
