"""
Prometheus metrics collection for observability and monitoring.
Follows 2026 Agentic AI Engineering standards for production observability.
"""

import time

from prometheus_client import Counter, Gauge, Histogram, Info

request_count = Counter(
    "knowledge_base_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

request_duration = Histogram(
    "knowledge_base_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

database_connections = Gauge(
    "knowledge_base_database_connections_active",
    "Number of active database connections",
)

database_queries = Counter(
    "knowledge_base_database_queries_total",
    "Total number of database queries",
    ["operation", "table"],
)

database_query_duration = Histogram(
    "knowledge_base_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
)

llm_api_calls = Counter(
    "knowledge_base_llm_api_calls_total",
    "Total number of LLM API calls",
    ["model", "operation", "status"],
)

llm_api_duration = Histogram(
    "knowledge_base_llm_api_duration_seconds",
    "LLM API call duration in seconds",
    ["model", "operation"],
)

circuit_breaker_state = Gauge(
    "knowledge_base_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["name"],
)

circuit_breaker_failures = Counter(
    "knowledge_base_circuit_breaker_failures_total",
    "Total circuit breaker failures",
    ["name"],
)

system_info = Info("knowledge_base_system", "System information")

pipeline_executions = Counter(
    "knowledge_base_pipeline_executions_total",
    "Total pipeline executions",
    ["stage", "status"],
)

pipeline_duration = Histogram(
    "knowledge_base_pipeline_duration_seconds",
    "Pipeline execution duration in seconds",
    ["stage"],
)


class MetricsMiddleware:
    """FastAPI middleware for automatic request metrics collection"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        endpoint = scope["path"]

        start_time = time.time()
        status_code = 500

        try:

            async def wrapped_send(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)

            await self.app(scope, receive, wrapped_send)
        finally:
            duration = time.time() - start_time
            request_count.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)
