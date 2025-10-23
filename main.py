"""Main entry point for Frame AI application."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from api.routes import router
from config.langfuse_config import langfuse_config
from config.logger import get_logger

logger = get_logger(__name__)

# Suppress noisy OpenTelemetry error logs (these are background export errors that don't affect functionality)
logging.getLogger("opentelemetry.sdk._shared_internal").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp").setLevel(logging.CRITICAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    # Startup: Initialize Langfuse client
    if langfuse_config.is_configured:
        try:
            langfuse_client = langfuse_config.get_client()
            if langfuse_client:
                logger.info(
                    "Langfuse observability enabled (using @observe decorators)"
                )
            else:
                logger.warning("Langfuse is enabled but client initialization failed")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}")

    yield

    # Shutdown: Flush pending traces
    if langfuse_config.is_configured:
        try:
            langfuse_config.flush()
            logger.info("Langfuse traces flushed on shutdown")
        except Exception as e:
            logger.warning(f"Failed to flush Langfuse traces on shutdown: {e}")


app = FastAPI(
    title="Frame AI",
    description="AI-powered photography coach and analysis tool",
    version="0.1.0",
    lifespan=lifespan,
)


# Middleware to flush Langfuse traces after each request
@app.middleware("http")
async def langfuse_flush_middleware(request: Request, call_next):
    """Flush Langfuse traces after each request to ensure data is sent."""
    response = await call_next(request)

    # Flush traces after request completes
    if langfuse_config.is_configured:
        try:
            from langfuse import get_client

            langfuse_client = get_client()
            langfuse_client.flush()
        except Exception as e:
            logger.debug(f"Failed to flush Langfuse in middleware: {e}")

    return response


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
