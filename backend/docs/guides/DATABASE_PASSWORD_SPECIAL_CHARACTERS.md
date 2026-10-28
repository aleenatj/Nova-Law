# Database Password Special Characters Guide

## Overview

When using passwords with special characters in database connection URLs, proper URL encoding is essential to prevent connection failures. This guide explains how our application handles special characters and what you need to know.

## Common Special Characters in Passwords

The following characters require URL encoding when used in database URLs:

| Character | Description | URL Encoded |
|-----------|-------------|-------------|
| `@`       | At symbol   | `%40`       |
| `#`       | Hash/Pound  | `%23`       |
| `:`       | Colon       | `%3A`       |
| `/`       | Forward slash | `%2F`     |
| `?`       | Question mark | `%3F`     |
| `&`       | Ampersand   | `%26`       |
| `%`       | Percent     | `%25`       |
| `+`       | Plus        | `%2B`       |
| ` `       | Space       | `%20`       |

## Example Problem

If your password is `jk2rht122dfs#kkjk@ejk`, using it directly in a database URL like this:

```
postgresql://user:jk2rht122dfs#kkjk@ejk@localhost:5432/mydb
```

Will fail because:
- The `#` character is interpreted as a URL fragment
- The `@` character confuses the URL parser about where the credentials end

## Our Solution

### Automatic URL Encoding (Recommended)

Our application automatically handles URL encoding when you use individual database parameters:

```env
# .env file - No manual encoding needed!
POSTGRES_USER=myuser
POSTGRES_PASSWORD=jk2rht122dfs#kkjk@ejk
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydb
```

The application will automatically encode the password to `jk2rht122dfs%23kkjk%40ejk` when constructing the database URL.

### Manual DATABASE_URL (Legacy)

If you must use the `DATABASE_URL` environment variable directly, you need to manually encode the password:

```env
# Manual encoding required for DATABASE_URL
DATABASE_URL=postgresql://myuser:jk2rht122dfs%23kkjk%40ejk@localhost:5432/mydb
```

## Implementation Details

### FastAPI Application

The URL encoding is handled in `app/core/config.py`:

```python
from urllib.parse import quote

@property
def database_url(self) -> str:
    """Construct database URL with proper URL encoding."""
    if self.DATABASE_URL:
        return self.DATABASE_URL

    # URL-encode credentials to handle special characters
    encoded_user = quote(self.POSTGRES_USER, safe="")
    encoded_password = quote(self.POSTGRES_PASSWORD, safe="")

    return f"postgresql://{encoded_user}:{encoded_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
```

### GitHub Actions Workflow

For CI/CD pipelines, we securely encode credentials in the workflow by passing secrets via environment variables to prevent code injection:

```yaml
- name: Construct DATABASE_URL
  run: |
    DB_USER_ENCODED=$(python3 -c "import urllib.parse, os; print(urllib.parse.quote(os.environ['DB_USER'], safe=''))")
    DB_PASSWORD_ENCODED=$(python3 -c "import urllib.parse, os; print(urllib.parse.quote(os.environ['DB_PASSWORD'], safe=''))")
    echo "DATABASE_URL=postgresql://${DB_USER_ENCODED}:${DB_PASSWORD_ENCODED}@${{ secrets.DB_HOST }}:${{ secrets.DB_PORT }}/${{ secrets.DB_NAME }}" >> $GITHUB_ENV
  env:
    DB_USER: ${{ secrets.DB_USER }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

## Testing Your Database Connection

### Using Python

You can test URL encoding with Python:

```python
from urllib.parse import quote

password = "jk2rht122dfs#kkjk@ejk"
encoded = quote(password, safe="")
print(f"Original: {password}")
print(f"Encoded:  {encoded}")
# Output: jk2rht122dfs%23kkjk%40ejk
```

### Using Our Utility Functions

We provide utility functions for safe database URL construction:

```python
from app.utils.database_url import construct_postgresql_url

url = construct_postgresql_url(
    user="myuser",
    password="jk2rht122dfs#kkjk@ejk",
    host="localhost",
    port=5432,
    database="mydb"
)
print(url)
# Output: postgresql://myuser:jk2rht122dfs%23kkjk%40ejk@localhost:5432/mydb
```

## Best Practices

1. **Use Individual Parameters**: Always prefer individual database parameters (`POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.) over `DATABASE_URL`

2. **Avoid Manual Encoding**: Let the application handle URL encoding automatically

3. **Test Locally**: Always test database connections locally with your actual passwords before deploying

4. **Secure Storage**: Store database credentials securely using environment variables or secret management systems

5. **Documentation**: Document any special password requirements for your team

## Troubleshooting

### Connection Fails with Special Characters

**Problem**: Database connection fails with passwords containing `@`, `#`, `:`, etc.

**Solution**:
- Use individual database parameters instead of `DATABASE_URL`
- Ensure you're using the latest version of the application with URL encoding support

### GitHub Actions Migration Fails

**Problem**: Alembic migrations fail in GitHub Actions with special character passwords

**Solution**:
- Verify that the workflow uses the updated database URL construction step
- Check that all database secrets are properly set in GitHub repository settings

### Manual DATABASE_URL Issues

**Problem**: Using `DATABASE_URL` directly with special characters

**Solution**:
- Either switch to individual parameters (recommended)
- Or manually URL-encode the password using `urllib.parse.quote(password, safe="")`

## Migration Guide

If you're currently using `DATABASE_URL` with special character passwords:

1. **Update your `.env` file**:
   ```env
   # Remove or comment out DATABASE_URL
   # DATABASE_URL=postgresql://user:complex#pass@word@localhost:5432/db

   # Add individual parameters
   POSTGRES_USER=user
   POSTGRES_PASSWORD=complex#pass@word
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=db
   ```

2. **Test the connection**:
   ```bash
   python -c "from app.core.config import settings; print('Database URL:', settings.database_url)"
   ```

3. **Update any deployment scripts** to use individual parameters instead of constructing `DATABASE_URL` manually

## Support

If you encounter issues with database passwords containing special characters:

1. Check this guide for common solutions
2. Verify your environment variables are set correctly
3. Test URL encoding manually using Python's `urllib.parse.quote(password, safe="")`
4. Review application logs for specific connection error messages
