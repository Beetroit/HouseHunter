import logging
import os

import redis.asyncio as redis
from redis.asyncio import Redis
from config import get_config
from models.base import ErrorDetail, ErrorResponse
from quart import Quart, jsonify
from quart_auth import QuartAuth
from quart_cors import cors
from quart_schema import (
    QuartSchema,
    RequestSchemaValidationError,
    ResponseSchemaValidationError,
)
from services.exceptions import ServiceException


# --- Application Factory ---
def create_app(config_name=None):
    """Creates and configures the Quart application."""
    if config_name is None:
        config_name = os.getenv("QUART_CONFIG", "default")
    config = get_config()

    app = Quart(__name__)
    app.config.from_object(config)

    # --- Logging ---
    # Basic logging setup (customize as needed)
    logging.basicConfig(
        level=logging.INFO if config.QUART_ENV != "development" else logging.DEBUG
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
    # from services.database import init_db
    # @app.before_serving
    # async def startup():
    #     if config.QUART_ENV == 'development': # Example: only init in dev if needed
    #         await init_db()

    # --- Redis Broker Setup ---
    @app.before_serving
    async def startup_redis():
        app.logger.info("Connecting to Redis...")
        try:
            # Create pool or client connection
            # Using client here for simplicity, pool might be better for high concurrency
            app.redis_broker = await redis.from_url(
                config.REDIS_URL,
                decode_responses=True,  # Decode responses to strings
            )
            # Test connection
            await app.redis_broker.ping()
            app.logger.info("Successfully connected to Redis.")
        except Exception as e:
            app.logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            # Depending on requirements, you might want to raise the error
            # or allow the app to start without Redis (graceful degradation)
            app.redis_broker = None  # Ensure it's None if connection failed

    @app.after_serving
    async def shutdown_redis():
        if hasattr(app, "redis_broker") and app.redis_broker:
            app.logger.info("Closing Redis connection...")
            try:
                await app.redis_broker.close()
                # await app.redis_broker.wait_closed() # Use if using connection pool
                app.logger.info("Redis connection closed.")
            except Exception as e:
                app.logger.error(f"Error closing Redis connection: {e}", exc_info=True)

    # --- Error Handlers ---
    @app.errorhandler(404)
    async def not_found(error):
        response = ErrorResponse(
            detail="The requested URL was not found on the server."
        )
        return jsonify(response.model_dump()), 404

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
        response = ErrorResponse(
            detail="Internal server error: Invalid response format."
        )
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

    # --- Blueprints ---
    # Import and register blueprints here as they are created
    from routes import (
        admin_routes,  # Import the admin blueprint
        auth_routes,
        chat_routes,  # Import chat routes
        property_routes,
    )

    # Example:
    # from routes import user_routes, property_routes
    app.register_blueprint(auth_routes.bp)  # Prefix is defined in auth_routes.py
    app.register_blueprint(
        property_routes.bp
    )  # Prefix is defined in property_routes.py
    app.register_blueprint(
        admin_routes.bp
    )  # Register admin routes (prefix defined in admin_routes.py)
    app.register_blueprint(chat_routes.bp)  # Register chat routes
    # app.register_blueprint(user_routes.bp, url_prefix='/users')

    @app.route("/health")
    async def health_check():
        """Simple health check endpoint."""
        return jsonify({"status": "ok"}), 200

    return app


# --- Main Execution ---
# This allows running the app directly using `python app.py`
# However, using `hypercorn app:create_app()` is generally preferred for development/production.
if __name__ == "__main__":
    app = create_app()
    # Note: app.run() is not recommended for production. Use a proper ASGI server like Hypercorn.
    # For development, Hypercorn is better: `hypercorn api.app:create_app --reload`
    print("Warning: Running with app.run() is suitable only for basic testing.")
    print("Use 'hypercorn api.app:create_app --reload' for development.")
    app.run(host="0.0.0.0", port=5000, debug=app.config["QUART_DEBUG"])
