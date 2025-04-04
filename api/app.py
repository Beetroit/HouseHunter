import logging
import os

import redis.asyncio as redis
import rich
from config import get_config
from models.base import ErrorDetail, ErrorResponse
from quart import Quart, jsonify
from quart_auth import QuartAuth, Unauthorized
from quart_cors import cors
from quart_schema import (
    QuartSchema,
    RequestSchemaValidationError,
    ResponseSchemaValidationError,
)

# --- Blueprints ---
# Import and register blueprints here as they are created
from routes import (
    admin_routes,  # Import the admin blueprint
    auth_routes,
    chat_routes,  # Import chat routes
    favorite_routes,  # Import favorite routes
    property_routes,
    review_routes,  # Import review routes
    user_routes,  # Import user routes
)
from services.database import init_db
from services.exceptions import ServiceException
from services.storage import get_storage_manager  # Import storage manager factory

config_name = os.getenv("QUART_CONFIG", "default")
config = get_config()

app = Quart("HouseHunter")
app.config.from_object(config)
rich.print(app.config)
# --- Logging ---
# Basic logging setup (customize as needed)
logging.basicConfig(
    level=logging.INFO if config.QUART_ENV != "development" else logging.INFO
)
app.logger.info(f"Starting app in {config.QUART_ENV} mode")

# Optional: Integrate Logfire
# logfire.configure(
#     send_to_logfire=config.QUART_ENV == 'production', # Only send in prod
#     # pydantic_plugin=logfire.PydanticPlugin(include=[...]), # Configure as needed
# )
# logfire.instrument_quart(app)
# logfire.instrument_sqlalchemy()

# --- Extensions ---
QuartSchema(app)
QuartAuth(app)
cors(
    app,
    allow_origin=config.QUART_CORS_ALLOW_ORIGIN,
    allow_credentials=config.QUART_CORS_ALLOW_CREDENTIALS,
)


# --- Database ---
# Database initialization is typically handled by Alembic migrations
# You might add a check here or a startup task if needed
@app.before_serving
async def startup_db():  # Renamed for clarity
    await init_db()


# --- Redis Broker & Storage Manager Setup ---
@app.before_serving
async def startup_services():
    # Redis Setup
    app.logger.info("Connecting to Redis...")
    try:
        app.redis_broker = await redis.from_url(config.REDIS_URL, decode_responses=True)
        await app.redis_broker.ping()
        app.logger.info("Successfully connected to Redis.")
    except Exception as e:
        app.logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
        app.redis_broker = None  # Allow app to start without Redis?

    # Storage Manager Setup
    app.logger.info("Initializing storage manager...")
    try:
        # Pass the config object to the factory function
        app.storage_manager = get_storage_manager(config)
        app.logger.info(
            f"Storage manager initialized: {type(app.storage_manager).__name__}"
        )
        # If using Azure, might want to ensure container exists here
        # if isinstance(app.storage_manager, AzureBlobStorage):
        #     await app.storage_manager._create_container_if_not_exists()
    except Exception as e:
        app.logger.error(f"Failed to initialize storage manager: {e}", exc_info=True)
        app.storage_manager = None  # Allow app to start? Or raise?


@app.after_serving
async def shutdown_services():
    # Redis Shutdown
    if hasattr(app, "redis_broker") and app.redis_broker:
        app.logger.info("Closing Redis connection...")
        try:
            await app.redis_broker.close()
            app.logger.info("Redis connection closed.")
        except Exception as e:
            app.logger.error(f"Error closing Redis connection: {e}", exc_info=True)
    # Add shutdown logic for storage manager if needed (e.g., closing clients)
    # if hasattr(app, "storage_manager") and hasattr(app.storage_manager, "close"):
    #     await app.storage_manager.close()


# --- Error Handlers ---
@app.errorhandler(404)
async def not_found(error):
    response = ErrorResponse(detail="The requested URL was not found on the server.")
    return jsonify(response.model_dump()), 404


@app.errorhandler(Unauthorized)
async def unauthorized_error(error: Unauthorized):
    return ErrorResponse(
        detail=str(error),
    ), int(error.code)


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error: RequestSchemaValidationError):
    # Convert Pydantic validation errors to our ErrorResponse format
    error_details = [
        ErrorDetail(
            loc=list(e.get("loc", [])), msg=e.get("msg", ""), type=e.get("type", "")
        )
        for e in error.validation_error.errors()
    ]
    response = ErrorResponse(detail=error_details)
    return jsonify(response.model_dump()), 422  # 422 Unprocessable Entity


@app.errorhandler(ResponseSchemaValidationError)
async def handle_response_validation_error(error: ResponseSchemaValidationError):
    # Log this error server-side, as it indicates an issue with our response models
    app.logger.error(f"Response schema validation error: {error.validation_error}")
    response = ErrorResponse(detail="Internal server error: Invalid response format.")
    return jsonify(response.model_dump()), 500


@app.errorhandler(ServiceException)
async def handle_service_exception(error: ServiceException):
    app.logger.warning(
        f"Service Exception: {error.message} (Status: {error.status_code})"
    )
    response = ErrorResponse(detail=error.message)
    return jsonify(response.model_dump()), error.status_code


@app.errorhandler(Exception)
async def handle_generic_exception(error: Exception):
    # Catch-all for unexpected errors
    app.logger.exception(
        f"Unhandled exception occurred: {error}"
    )  # Log the full traceback
    response = ErrorResponse(detail="An unexpected internal server error occurred.")
    return jsonify(response.model_dump()), 500


# Example:
# from routes import user_routes, property_routes
app.register_blueprint(auth_routes.bp)  # Prefix is defined in auth_routes.py
app.register_blueprint(property_routes.bp)  # Prefix is defined in property_routes.py
app.register_blueprint(
    admin_routes.bp
)  # Register admin routes (prefix defined in admin_routes.py)
app.register_blueprint(chat_routes.bp)  # Register chat routes
app.register_blueprint(
    user_routes.bp
)  # Register user routes (prefix defined in user_routes.py)
app.register_blueprint(favorite_routes.bp)  # Register favorite routes
app.register_blueprint(review_routes.bp)  # Register review routes


@app.route("/health")
async def health_check():
    """Simple health check endpoint."""
    # Could add checks for DB, Redis, Storage here later
    return jsonify({"status": "ok"}), 200


# --- Main Execution ---
# This allows running the app directly using `python app.py`
# However, using `hypercorn app:create_app()` is generally preferred for development/production.
if __name__ == "__main__":
    # Note: app.run() is not recommended for production. Use a proper ASGI server like Hypercorn.
    # For development, Hypercorn is better: `hypercorn api.app:create_app --reload`
    print("Warning: Running with app.run() is suitable only for basic testing.")
    print("Use 'hypercorn api.app:create_app --reload' for development.")
    app.run(host="0.0.0.0", port=5000, debug=app.config["QUART_DEBUG"])
