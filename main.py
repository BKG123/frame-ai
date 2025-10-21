"""Main entry point for Frame AI application."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from api.routes import router
from config.langfuse_config import langfuse_config
from config.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    # Startup: Initialize Langfuse instrumentation
    if langfuse_config.is_configured:
        try:
            from openinference.instrumentation.google_genai import (
                GoogleGenAIInstrumentor,
            )
            from langfuse.opentelemetry import LangfuseSpanProcessor
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider

            # Set up OpenTelemetry tracer provider
            tracer_provider = TracerProvider()
            trace.set_tracer_provider(tracer_provider)

            # Add Langfuse span processor
            langfuse_client = langfuse_config.get_client()
            if langfuse_client:
                span_processor = LangfuseSpanProcessor()
                tracer_provider.add_span_processor(span_processor)

                # Instrument Google GenAI
                GoogleGenAIInstrumentor().instrument()
                logger.info("Langfuse instrumentation initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse instrumentation: {e}")

    yield

    # Shutdown: Flush pending traces
    if langfuse_config.is_configured:
        langfuse_config.flush()
        logger.info("Langfuse traces flushed on shutdown")


app = FastAPI(
    title="Frame AI",
    description="AI-powered photography coach and analysis tool",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
