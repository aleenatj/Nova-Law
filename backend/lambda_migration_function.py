import os
import subprocess

from app.core.config import settings


def lambda_handler(event, context):
    """
    Lambda function to run Alembic migrations.
    DB connection parameters are taken from environment variables.
    Returns a status indicating whether the migration completed successfully.
    """

    # Build database URL safely
    db_url = settings.database_url
    os.environ["DATABASE_URL"] = db_url

    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"], capture_output=True, text=True, check=True
        )
        return {
            "status": "success",
            "message": "Migration completed successfully",
            "output": result.stdout,
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": "Migration failed", "error": e.stderr}
