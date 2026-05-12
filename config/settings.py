from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "IntelliBank"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://intellibank_user:password@localhost:5432/intellibank_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM — NLP Query Engine
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Email
    SENDGRID_API_KEY: str = ""
    ALERT_EMAIL_FROM: str = "noreply@intellibank.com"
    ALERT_EMAIL_TO: str = "admin@intellibank.com"

    # SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    ALERT_SMS_TO: str = ""

    # Thresholds
    FRAUD_ALERT_THRESHOLD: float = 0.75
    CHURN_ALERT_THRESHOLD: float = 0.80

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Reports
    REPORT_SCHEDULE_CRON: str = "0 8 * * 1"
    REPORT_RECIPIENTS: str = "manager@bank.com"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
