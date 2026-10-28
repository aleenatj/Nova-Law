from urllib.parse import quote

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Nova Law AI Backend"
    APP_ENV: str = "development"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Server settings
    HOST: str = "127.0.0.1"  # Use localhost by default for security
    PORT: int = 8000

    # CORS settings
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Frontend URL for password reset links
    FRONTEND_URL: str = "http://localhost:3000"
    LOGO_URL: str = "https://di2ljh1xtvw5x.cloudfront.net/nova/logos/nova_logo.png"
    ENGAGE_AUTH_URL: str = "https://engage.novalaw.co.uk/login"
    ENGAGE_API_KEY: str = ""
    
    # Database settings - individual parameters for security
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""

    # Legacy DATABASE_URL for backward compatibility (deprecated)
    DATABASE_URL: str = ""

    # JWT settings
    SECRET_KEY: str = ""
    JWE_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    JWE_ALGORITHM: str = "dir"
    ENCRYPTION_ALGORITHM: str = "A256GCM"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    INITIAL_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES: int = 30
    #analytics settings
    ANALYTICS_JWE_SECRET_KEY: str = ""

    # S3 settings
    AWS_S3_ACCESS_KEY_ID: str = ""
    AWS_S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_PRESIGNED_URL_EXPIRY_SECONDS: int = 3600  # 1 hour default

    # CloudFront settings
    CLOUDFRONT_DOMAIN: str = ""
    CLOUDFRONT_DISTRIBUTION_ID: str = ""
    WEBSOCKET_ENDPOINT: str = ""
    WEBSOCKET_API_KEY: str = ""

    # AI/LLM settings
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str | None = None

    # AWS settings
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-2"
    DEFAULT_EMAIL_SENDER: str = ""

    # AWS SES SMTP settings
    AWS_SES_SMTP_USERNAME: str = ""
    AWS_SES_SMTP_PASSWORD: str = ""
    AWS_SES_SMTP_HOST: str = "email-smtp.eu-west-2.amazonaws.com"
    AWS_SES_SMTP_PORT: int = 587

    # LangChain settings
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str | None = None
    LANGCHAIN_API_KEY: str | None = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Date format
    DATE_FORMAT: str = "%d/%m/%Y"

    ENCRYPTION_SECRET_KEY: str = ""
    ENCRYPTION_SALT: str = ""
    QUESTIONS_FILE_PATH: str = "app/config/questions/resolve.json"
    RESOLVE_MAP_FILE_PATH: str = "app/config/questions/resolve_map.json"
    RESOLVE_RESULT_FILE_PATH: str = "app/config/results/resolve.json"
    KYC_QUESTIONS_FILE_PATH: str = "app/config/questions/kyc.json"
    KYC_MAP_FILE_PATH: str = "app/config/questions/kyc_map.json"
    TRIAGE_QUESTIONS_FILE_PATH: str = "app/config/questions/triage.json"
    ENGAGE_FEEDBACK_CSV_QUESTIONS_FILE_PATH: str = "app/config/questions/engage_feedback_questions.json"
    ENGAGE_SUPPORT_CSV_QUESTIONS_FILE_PATH: str = "app/config/questions/engage_support.json"
    BASE_COMPONENTS_PATH: str = "app/config/components"
    KIM_LAWYER_ID: int = 0
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    CHECKOUT_SESSION_EXPIRATION_TIME: int = 1800 # 30 minutes

    #engage support email settings
    ENGAGE_SUPPORT_EMAILS: str = ""
    
    # AI Case Summary settings
    CASE_SUMMARY_PROMPT_PATH: str = "app/config/prompts/case_summary"
    RESOLVE_RECOMMENDATION_PROMPT_PATH: str = "app/config/prompts/resolve_recommendation"
    DEFAULT_CASE_SUMMARY_MODEL: str = "gpt-4o-mini"
    CASE_SUMMARY_MAX_TOKENS: int = 1000
    CASE_SUMMARY_TEMPERATURE: float = 0.7

    INIT_PMT_AMOUNT: float = 50.00
    RESOLVE_EXPIRY_HOURS: float = 24

    STRATEGIC_ADVICE_CONSULTATION: int = 299

    #cal integration
    CAL_API_KEY: str = ""
    CAL_WEBHOOK_SECRET: str = ""
    CAL_API_BASE_URL: str = "https://api.cal.com/v2"
    CAL_API_VERSION: str = "2024-09-04"
    CAL_NN_CALL_BACK_SLUG: str = ""
    CAL_MEETING_SLUG: str = ""
    CAL_USERNAME: str = ""

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow",  # This allows extra fields from environment variables
    }

    WEBSOCKET_TOKEN_ENCRYPTION_KEY: str = ""

    # Contact us settings hello@novalaw.co.uk
    CONTACT_US_EMAIL: str = ""


    @staticmethod
    def _encode_database_credential(credential: str) -> str:
        """Safely URL-encode database credentials to handle special characters.

        Args:
            credential: The credential string to encode

        Returns:
            URL-encoded credential string safe for use in database URLs
        """
        return quote(credential, safe="") if credential else ""

    @property
    def database_url(self) -> str:
        """Construct database URL from individual parameters with proper URL encoding.

        This method safely handles special characters in passwords by URL-encoding
        the username and password components. Characters like @, #, :, /, etc.
        are properly encoded to prevent URL parsing issues.

        Returns:
            Constructed PostgreSQL connection string with URL-encoded credentials

        Examples:
            Password "jk2rht122dfs#kkjk@ejk" becomes "jk2rht122dfs%23kkjk%40ejk"
        """
        # If DATABASE_URL is explicitly set, use it (for backward compatibility)
        if self.DATABASE_URL:
            return self.DATABASE_URL

        # URL-encode username and password to handle special characters
        encoded_user = self._encode_database_credential(self.POSTGRES_USER)
        encoded_password = self._encode_database_credential(self.POSTGRES_PASSWORD)

        # Construct URL from individual parameters with encoded credentials
        return f"postgresql://{encoded_user}:{encoded_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


# Create settings instance
settings = Settings()
