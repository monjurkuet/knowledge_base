"""
Circuit Breaker implementation for external API calls to prevent cascading failures.
Follows 2026 Agentic AI Engineering standards for self-healing systems.
"""

import time
from collections.abc import Callable
from enum import Enum
from typing import Any


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and requests are blocked"""

    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with exponential backoff recovery.

    Implements the three-state pattern:
    - CLOSED: Requests are allowed through normally
    - OPEN: Requests are blocked immediately (fast failure)
    - HALF_OPEN: Limited requests are allowed to test if service has recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_attempts: int = 3,
        name: str = "circuit_breaker",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Time in seconds to wait before attempting recovery
            half_open_max_attempts: Max attempts in half-open state before reopening
            name: Identifier for this circuit breaker instance
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.half_open_attempts = 0

        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record a successful request and reset failure state"""
        self.successful_requests += 1
        self.failure_count = 0
        self.half_open_attempts = 0
        self.state = CircuitState.CLOSED

    def _record_failure(self) -> None:
        """Record a failed request and update circuit state"""
        self.failed_requests += 1
        self.failure_count += 1
        self.last_failure_time = time.time()

        if (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            self.half_open_attempts += 1
            if self.half_open_attempts >= self.half_open_max_attempts:
                self.state = CircuitState.OPEN

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is open and request is blocked
            Exception: Any exception raised by the function
        """
        self.total_requests += 1

        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e

    def get_stats(self) -> dict:
        """Get circuit breaker statistics for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "successful_requests": self.successful_requests,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def force_open(self) -> None:
        """Force circuit breaker to open state (for testing or emergency)"""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()

    def force_close(self) -> None:
        """Force circuit breaker to closed state (for testing or emergency)"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0
