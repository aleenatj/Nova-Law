# Lambda Optimization Quick Reference

## 🚀 Essential Commands

```bash
# Activate environment
source venv-be/bin/activate

# Quick analysis
python scripts/lambda_tools.py analyze

# Build for deployment
python scripts/lambda_tools.py build --create-layer

# Full optimization pipeline
python scripts/lambda_tools.py optimize

# CI size check
python scripts/lambda_tools.py check --fail-on-limit
```

## 📊 Current Status

- **Package Size**: 18.53 MB ✅
- **Lambda Limit**: 250 MB
- **Dependencies**: 23 production
- **Status**: Well within limits

## 🛠️ Tool Commands

### Lambda Optimizer
```bash
# Basic analysis
python scripts/lambda_optimizer.py

# Generate optimized config
python scripts/lambda_optimizer.py --generate-optimized

# Create layer script
python scripts/lambda_optimizer.py --create-layer-script

# Custom threshold
python scripts/lambda_optimizer.py --threshold-mb 5
```

### Package Builder
```bash
# Basic build
python scripts/build_lambda_package.py

# Build with layer
python scripts/build_lambda_package.py --create-layer

# Build with Dockerfile
python scripts/build_lambda_package.py --create-dockerfile

# Custom package name
python scripts/build_lambda_package.py --package-name my-app.zip

# Clean only
python scripts/build_lambda_package.py --clean-only
```

### CI Size Checker
```bash
# Basic check
python scripts/ci_size_check.py

# Check groups
python scripts/ci_size_check.py --check-groups

# GitHub comment
python scripts/ci_size_check.py --github-comment

# Slack notification
python scripts/ci_size_check.py --slack-notification

# Fail on limit
python scripts/ci_size_check.py --fail-on-limit
```

## 📋 Development Workflow

### Adding Dependencies
```bash
# Production
poetry add --group prod <package>

# Development
poetry add --group dev <package>

# Test
poetry add --group test <package>

# Check impact
python scripts/lambda_tools.py analyze
```

### Before Committing
```bash
# Check size
python scripts/lambda_tools.py check --fail-on-limit

# Ensure < 250MB
# Commit changes
```

### Regular Maintenance
```bash
# Weekly analysis
python scripts/lambda_tools.py analyze

# Update dependencies
poetry update
python scripts/lambda_tools.py check
```

## 🚀 Deployment

### Local Testing
```bash
# Build package
python scripts/lambda_tools.py build --create-layer

# Check size
ls -lh dist/lambda-package.zip

# Test locally
unzip dist/lambda-package.zip -d test-package/
cd test-package/
python -c "import app; print('Package works!')"
```

### Lambda Deployment
```bash
# Deploy function
aws lambda update-function-code \
  --function-name nova-law-api \
  --zip-file fileb://dist/lambda-package.zip

# Deploy layer (if created)
aws lambda publish-layer-version \
  --layer-name nova-law-dependencies \
  --zip-file fileb://dist/lambda-layer.zip \
  --compatible-runtimes python3.11
```

### Docker Deployment
```bash
# Build image
docker build -f Dockerfile.lambda -t nova-law-lambda .

# Deploy to ECR
aws ecr get-login-password --region region | docker login --username AWS --password-stdin account.dkr.ecr.region.amazonaws.com
docker tag nova-law-lambda:latest account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest
docker push account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest

# Update Lambda
aws lambda update-function-code \
  --function-name nova-law-api \
  --image-uri account.dkr.ecr.region.amazonaws.com/nova-law-lambda:latest
```

## 🔧 Troubleshooting

### Common Issues

**Poetry not found**:
```bash
source venv-be/bin/activate
```

**Package too large**:
```bash
python scripts/lambda_optimizer.py --threshold-mb 10
# Review large dependencies and consider alternatives
```

**Build failures**:
```bash
python scripts/lambda_tools.py build --clean-only
python scripts/lambda_tools.py build
```

**Runtime errors**:
- Check Lambda layer compatibility
- Verify Python version (3.11)
- Ensure all dependencies included
- Check for missing native extensions

### Debug Commands
```bash
# Check Poetry
poetry --version

# List dependencies
poetry show --tree

# Check environment
which python
which poetry

# Verify package
ls -la dist/
```

## 📊 Size Limits

- **Lambda ZIP**: 250MB (unzipped)
- **Lambda Layer**: 250MB (unzipped)
- **Lambda Container**: 10GB
- **Warning Threshold**: 200MB

## 🔄 CI/CD Integration

### GitHub Actions
- Automatically runs on PRs and main branch
- Comments on PRs with size information
- Fails builds if >250MB
- Deploys to Lambda on main branch

### Required Secrets
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## 📁 File Structure

```
backend/
├── scripts/                          # Tools (keep in git)
│   ├── lambda_optimizer.py
│   ├── build_lambda_package.py
│   ├── ci_size_check.py
│   ├── lambda_tools.py
│   └── makefile
├── .github/workflows/                # CI/CD (keep in git)
│   └── lambda-deployment.yml
├── docs/guides/                      # Documentation (keep in git)
│   ├── lambda-optimization-guide.md
│   └── lambda-optimization-quick-reference.md
├── pyproject.lambda.toml            # Config template (keep in git)
├── build/                           # Generated (don't keep in git)
├── dist/                            # Generated (don't keep in git)
├── *.zip                           # Generated (don't keep in git)
└── requirements.txt                 # Generated (don't keep in git)
```

## 🎯 Best Practices

1. **Use Poetry groups** for dependency management
2. **Check size impact** when adding new dependencies
3. **Consider alternatives** for large packages
4. **Use Lambda layers** for heavy dependencies
5. **Monitor size trends** over time
6. **Automate CI/CD** checks

## 📞 Support

- Check `docs/guides/lambda-optimization-guide.md` for detailed instructions
- Review troubleshooting section for common issues
- Check logs in `logs/` directory
- Run debug commands to identify problems

---

*Last updated: [Current Date]*
*Version: 1.0*
