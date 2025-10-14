"""Utility decorators for various purposes."""
from __future__ import annotations

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Optional, ParamSpec, TypeVar
from collections.abc import Awaitable, Callable, Coroutine

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class RetryError(RuntimeError):
    """Raised when the retry attempts are exhausted."""


def retry_async(
    *,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: Optional[float] = None,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    retry_on_none: bool = True,
    jitter: float = 0.1,
    on_retry: Optional[Callable[[int, BaseException | None], None]] = None,
) -> Callable[[Callable[P, Coroutine[Any, Any, R | None]]], Callable[P, Awaitable[R | None]]]:
    """
    Decorator to retry an async function on specific exceptions and/or None results.

    Args:
        max_retries: Number of retries after the initial attempt (total attempts = max_retries + 1).
        base_delay: Initial backoff delay in seconds (exponential backoff is applied).
        max_delay: Optional cap for backoff delay.
        exceptions: A tuple of exception types that should trigger a retry.
        retry_on_none: Whether to retry when the function returns None.
        jitter: Random jitter factor (0~1-ish) added/subtracted to delay to avoid thundering herd.
        on_retry: Optional callback called on each retry attempt with (attempt_index, last_exception).

    Returns:
        A decorator that retries the decorated async function on specified conditions.
    """

    def decorator(func: Callable[P, Coroutine[Any, Any, R | None]]) -> Callable[P, Awaitable[R | None]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            max_attempts = max_retries + 1
            last_exc: BaseException | None = None

            for attempt in range(max_attempts):
                is_last = attempt == max_attempts - 1
                try:
                    logger.debug("Attempt %d/%d for %s", attempt + 1, max_attempts, func.__name__)
                    result = await func(*args, **kwargs)

                    if (result is None) and retry_on_none and not is_last:
                        delay = _compute_delay(base_delay, attempt, max_delay, jitter)
                        logger.warning(
                            "Got None from %s (attempt %d/%d); retrying after %.2fs",
                            func.__name__, attempt + 1, max_attempts, delay,
                        )
                        if on_retry:
                            on_retry(attempt, None)
                        await asyncio.sleep(delay)
                        continue

                    return result

                except exceptions as e:  # only retry for the configured exceptions
                    last_exc = e
                    if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
                        raise  # never swallow task cancellation / interrupts

                    if not is_last:
                        delay = _compute_delay(base_delay, attempt, max_delay, jitter)
                        logger.warning(
                            "Error on attempt %d/%d in %s: %s; retrying after %.2fs",
                            attempt + 1, max_attempts, func.__name__, e, delay,
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        await asyncio.sleep(delay)
                        continue

                    # last attempt failed: re-raise to caller
                    logger.error("Max retries reached for %s; raising last exception", func.__name__)
                    raise
            # If we break out without returning (shouldn't happen), raise a clear error.
            raise RetryError(f"Retry loop exhausted for {func.__name__}") from last_exc

        return wrapper

    return decorator


def _compute_delay(base: float, attempt: int, cap: Optional[float], jitter: float) -> float:
    """Exponential backoff with jitter."""
    delay = base * (2 ** attempt)
    if cap is not None:
        delay = min(delay, cap)
    if jitter:
        # jitter in range ~[-jitter*delay, +jitter*delay]
        delta = delay * jitter
        delay = max(0.0, delay + random.uniform(-delta, delta))
    return delay
