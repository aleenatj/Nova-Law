# GitHub Actions Workflows

This directory contains modular GitHub Actions workflows for the Nova Platform Backend CI/CD pipeline.

## Architecture Overview

We provide two approaches for running the CI/CD pipeline:

### 1. Single Container Approach (Recommended)
- **File**: `main.yml` - All steps run in a single container
- **Benefits**: Faster execution, shared dependencies, reduced overhead
- **Use Case**: When you want maximum performance and simplicity

### 2. Fully Reusable Workflows Approach
- **File**: `main-reusable.yml` - Uses ALL individual reusable workflow files
- **Benefits**: Maximum modularity, individual job isolation, complete reusability
- **Use Case**: When you need granular control, job isolation, and maximum reusability

## Workflow Files

### Main Workflows
- `main.yml` - Single container CI/CD pipeline (all steps in one job)
- `main-reusable.yml` - Fully modular CI/CD pipeline using ALL reusable workflows

### Individual Workflow Files (ALL Reusable)
- `01-determine-environment.yml` - Environment determination logic ✅ **REUSABLE**
- `02-security-scan.yml` - Security scanning with Bandit ✅ **REUSABLE**
- `03-test.yml` - Test execution ✅ **REUSABLE**
- `04-build-package.yml` - Lambda package building ✅ **REUSABLE**
- `05-deploy.yml` - AWS Lambda deployment ✅ **REUSABLE**
- `06-database-migrate.yml` - Database migration via Lambda ✅ **REUSABLE**
- `07-rollback.yml` - Rollback functionality ✅ **REUSABLE**
- `08-dependency-audit.yml` - Dependency security audit ✅ **REUSABLE**

## Execution Flow

### Single Container Approach (`main.yml`)
```
┌─────────────────────────────────────────────────────────────┐
│                    Single Job Container                     │
├─────────────────────────────────────────────────────────────┤
│ 1. Setup (Python, Poetry, Dependencies)                    │
│ 2. Determine Environment                                    │
│ 3. Security Scan                                            │
│ 4. Run Tests                                                │
│ 5. Build Package                                            │
│ 6. Deploy (push only)                                       │
│ 7. Database Migration (push only)                           │
│ 8. Rollback (on failure)                                    │
│ 9. Dependency Audit                                         │
└─────────────────────────────────────────────────────────────┘
```

### Fully Reusable Workflows Approach (`main-reusable.yml`)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Environment │───▶│ Security    │───▶│ Tests       │
│ (Reusable)  │    │ Scan        │    │ (Reusable)  │
│             │    │ (Reusable)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Deploy      │◀───│ Build       │◀───│             │
│ (Reusable)  │    │ Package     │    │             │
│             │    │ (Reusable)  │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Migration   │───▶│ Rollback    │    │ Dependency  │
│ (Reusable)  │    │ (Reusable)  │    │ Audit       │
│             │    │             │    │ (Reusable)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Triggers

### Pull Requests
- **Build**: ✅ Runs (for validation)
- **Deploy**: ❌ Skipped
- **Migration**: ❌ Skipped

### Push to Main
- **Build**: ✅ Runs
- **Deploy**: ✅ Runs
- **Migration**: ✅ Runs

## Environment Configuration

### Branch Mapping
- `main` → `staging` environment
- Other branches → `staging` environment (for testing)

### Lambda Functions
- **API Function**: `nova-law-api`
- **Layer**: `nova-law-dependencies`
- **Migration Function**: `nova-law-migration`

## Secrets Required

The following secrets must be configured in your GitHub repository:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

## Usage

### Option 1: Single Container (Recommended)
The `main.yml` workflow will automatically run on:
- Pull requests to `main`
- Pushes to `main`

### Option 2: Fully Reusable Workflows
The `main-reusable.yml` workflow provides maximum modularity with ALL steps as reusable workflows.

## Benefits of Each Approach

### Single Container (`main.yml`)
✅ **Pros:**
- Faster execution (no job startup overhead)
- Shared dependencies (install once, use everywhere)
- Simpler debugging (all logs in one place)
- Lower resource usage
- Better for small to medium projects

❌ **Cons:**
- Less granular control
- All steps must pass for any to succeed
- Harder to parallelize individual steps

### Fully Reusable Workflows (`main-reusable.yml`)
✅ **Pros:**
- **Maximum modularity** - Every workflow is reusable
- **Individual job isolation** - Each step runs independently
- **Complete reusability** - Any workflow can be called from anywhere
- **Better parallelization** - Steps can run in parallel where possible
- **Easier debugging** - Individual step logs are isolated
- **Flexible execution** - Can run individual workflows independently
- **Better for complex projects** - Each component is self-contained

❌ **Cons:**
- Slower execution (job startup overhead for each step)
- Repeated dependency installation
- More complex to maintain
- Higher resource usage

## Reusable Workflow Features

### Input Parameters
Each reusable workflow accepts relevant input parameters:

- **Environment workflows**: `ref-name`, `environment`
- **Build workflows**: `python-version`, `lambda-limit-mb`
- **Deploy workflows**: `environment`, `lambda-function-name`, etc.
- **Migration workflows**: `environment`, `migration-lambda-function-name`
- **Rollback workflows**: `environment`, `lambda-function-name`, `deployment-success`, `migration-success`

### Output Values
Each reusable workflow provides relevant outputs:

- **Environment**: `environment`, `lambda-function-name`, `lambda-layer-name`, `migration-lambda-function-name`
- **Build**: `build-success`
- **Deploy**: `deployment-success`, `previous-version`
- **Migration**: `migration-success`
- **Rollback**: `rollback-success`

### Independent Execution
You can now run any individual workflow independently:

```yaml
# Example: Run only security scan
name: Security Scan Only
on:
  workflow_dispatch:
jobs:
  security-scan:
    uses: ./.github/workflows/02-security-scan.yml
    with:
      python-version: "3.13"
```

## Migration from Monolithic Workflow

The original `lambda-deployment.yml` has been replaced with these modular approaches. The new structure provides:

1. **Complete Modularity**: Every workflow is now reusable
2. **Better Organization**: Each workflow has a single responsibility
3. **Improved Performance**: Single container approach reduces overhead
4. **Enhanced Flexibility**: Choose between single container or fully modular execution
5. **Easier Maintenance**: Individual files are easier to understand and modify
6. **Better Testing**: Each workflow can be tested independently
7. **Maximum Reusability**: Any workflow can be called from any other workflow

## Troubleshooting

### Common Issues

1. **Package Size Exceeded**
   - Check the `LAMBDA_LIMIT_MB` environment variable
   - Optimize dependencies in `pyproject.toml`
   - Use the Lambda layer for large dependencies

2. **Deployment Failures**
   - Verify AWS credentials and permissions
   - Check Lambda function configuration
   - Review CloudWatch logs for detailed error messages

3. **Migration Failures**
   - Ensure migration Lambda function exists
   - Verify database connection parameters
   - Check Alembic migration files

4. **Reusable Workflow Issues**
   - Verify input parameters are correctly passed
   - Check output values are properly consumed
   - Ensure all required secrets are available

### Debugging

- **Single Container**: All logs are in one job, making debugging easier
- **Reusable Workflows**: Check individual job logs for specific step failures
- **Independent Workflows**: Test individual workflows in isolation

## Future Enhancements

- [ ] Add performance monitoring
- [ ] Implement blue-green deployments
- [ ] Add automated rollback triggers
- [ ] Integrate with monitoring tools
- [ ] Add deployment notifications
- [ ] Create workflow templates for common use cases
- [ ] Add workflow dependency visualization
