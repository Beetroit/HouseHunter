import os
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(
        "Warning: .env file not found. Using default settings or environment variables."
    )


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "you-should-really-change-this")
    QUART_APP = os.environ.get("QUART_APP", "app:create_app")
    QUART_ENV = os.environ.get("QUART_ENV", "production")
    QUART_DEBUG = False
    TESTING = False

    # Database - Default to SQLite for safety if no specific config is chosen
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite+aiosqlite:///app.db"
    )
    SQLALCHEMY_ECHO = False  # Set to True for debugging SQL queries
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Deprecated and unnecessary

    # Quart-Auth settings
    QUART_AUTH_DURATION = timedelta(days=30)
    QUART_AUTH_COOKIE_SECURE = QUART_ENV == "production"
    QUART_AUTH_COOKIE_HTTPONLY = True
    QUART_AUTH_COOKIE_SAMESITE = "Lax"

    # CORS settings (adjust origin as needed for frontend)
    QUART_CORS_ALLOW_ORIGIN = os.environ.get(
        "FRONTEND_URL", "*"
    )  # Be more specific in production
    QUART_CORS_ALLOW_CREDENTIALS = True

    # Paystack (placeholders - get from environment)
    PAYSTACK_SECRET_KEY = os.environ.get(
        "PAYSTACK_SECRET_KEY", "your_paystack_secret_key"
    )
    PAYSTACK_PUBLIC_KEY = os.environ.get(
        "PAYSTACK_PUBLIC_KEY", "your_paystack_public_key"
    )

    # Redis configuration
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(basedir, "uploads"))
    # Azure Storage (Optional)
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get(
        "AZURE_STORAGE_CONNECTION_STRING", None
    )
    AZURE_STORAGE_CONTAINER_NAME = os.environ.get(
        "AZURE_STORAGE_CONTAINER_NAME", "property-images"
    )
    # Consider adding allowed extensions and max size
    # ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    # MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit


class DevelopmentConfig(Config):
    """Development configuration."""

    QUART_ENV = "development"
    QUART_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite+aiosqlite:///dev_app.db"
    )
    SQLALCHEMY_ECHO = True  # Useful for debugging in development
    QUART_AUTH_COOKIE_SECURE = False  # Allow HTTP for local dev


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    QUART_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"
    )  # Use in-memory DB for tests
    QUART_AUTH_COOKIE_SECURE = False
    # Make tests faster
    QUART_AUTH_DURATION = timedelta(seconds=1)


class ProductionConfig(Config):
    """Production configuration."""

    # Ensure DATABASE_URL and SECRET_KEY are set in the environment for production
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", None
    )  # Require DATABASE_URL in prod
    SECRET_KEY = os.environ.get("SECRET_KEY", None)  # Require SECRET_KEY in prod

    if SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("No DATABASE_URL set for production environment")
    if SECRET_KEY is None:
        raise ValueError("No SECRET_KEY set for production environment")

    # Require REDIS_URL in production as well
    REDIS_URL = os.environ.get("REDIS_URL", None)
    if REDIS_URL is None:
        raise ValueError("No REDIS_URL set for production environment")

    # Production might require Azure Storage or a persistent UPLOAD_FOLDER
    # If using Azure, ensure AZURE_STORAGE_CONNECTION_STRING is set
    # if AZURE_STORAGE_CONNECTION_STRING is None:
    #     raise ValueError("No AZURE_STORAGE_CONNECTION_STRING set for production environment")


# Dictionary to easily select config based on environment variable
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig,  # Default to development if QUART_CONFIG is not set
)


def get_config():
    """Helper function to get the configuration object based on QUART_CONFIG environment variable."""
    config_name = os.getenv("QUART_CONFIG", "default")
    return config_by_name.get(config_name, DevelopmentConfig)()


# Load the configuration
config = get_config()
