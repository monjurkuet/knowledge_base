"""
OpenTelemetry distributed tracing implementation for 2026 Agentic AI Engineering standards.
Provides end-to-end request tracing across the entire system.
"""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TracingConfig:
    """Configuration for OpenTelemetry tracing"""

    def __init__(self):
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "knowledge-base")
        self.environment = os.getenv("OTEL_ENVIRONMENT", "development")
        self.sample_rate = float(os.getenv("OTEL_SAMPLE_RATE", "1.0"))


def setup_tracing(app=None, config: TracingConfig = None):
    """
    Set up OpenTelemetry tracing for the application.

    Args:
        app: FastAPI application instance (optional)
        config: Tracing configuration (optional)
    """
    if config is None:
        config = TracingConfig()

    # Set up tracer provider
    tracer_provider = TracerProvider(
        resource={
            "service.name": config.service_name,
            "environment": config.environment,
        }
    )

    # Set up OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=config.otlp_endpoint,
        insecure=True,  # Set to False in production with proper TLS
    )

    # Add batch span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Auto-instrument FastAPI if app is provided
    if app is not None:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # Auto-instrument HTTPX and psycopg2
    HTTPXClientInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()

    return tracer_provider


def get_tracer(name: str = "knowledge_base"):
    """Get a tracer instance for the given name"""
    return trace.get_tracer(name)


# Global tracer instance
tracer = get_tracer()
