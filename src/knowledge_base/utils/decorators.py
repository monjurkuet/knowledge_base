"""
Common decorators for error handling, logging, and retry logic.
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_errors(func: F) -> F:
    """
    Decorator to log errors from function calls.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {e}",
                exc_info=True,
                extra={"function": func.__name__, "args": args, "kwargs": kwargs},
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {e}",
                exc_info=True,
                extra={"function": func.__name__, "args": args, "kwargs": kwargs},
            )
            raise

    if hasattr(func, "__await__"):
        return cast(F, async_wrapper)
    else:
        return cast(F, sync_wrapper)


def handle_errors(
    default: Any = None, error_types: tuple[type[Exception], ...] = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator to handle errors and return default value.

    Args:
        default: Default value to return on error
        error_types: Tuple of exception types to catch

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                logger.warning(
                    f"Error in {func.__name__}: {e}, returning default",
                    extra={"function": func.__name__},
                )
                return default

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                logger.warning(
                    f"Error in {func.__name__}: {e}, returning default",
                    extra={"function": func.__name__},
                )
                return default

        if hasattr(func, "__await__"):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator to retry function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry on

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            if last_exception:
                raise last_exception
            raise RuntimeError("Retry failed without exception")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            if last_exception:
                raise last_exception
            raise RuntimeError("Retry failed without exception")

        if hasattr(func, "__await__"):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def validate_args(**validators: Callable[[Any], bool]) -> Callable[[F], F]:
    """
    Decorator to validate function arguments.

    Args:
        **validators: Mapping of argument names to validation functions

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if not validator(value):
                        from .errors import ValidationError

                        raise ValidationError(
                            f"Validation failed for argument '{arg_name}'",
                            field=arg_name,
                            value=value,
                        )

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if not validator(value):
                        from .errors import ValidationError

                        raise ValidationError(
                            f"Validation failed for argument '{arg_name}'",
                            field=arg_name,
                            value=value,
                        )

            return func(*args, **kwargs)

        if hasattr(func, "__await__"):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
