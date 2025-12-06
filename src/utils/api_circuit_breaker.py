from typing import Any, Awaitable, Callable, TypeVar

from circuitbreaker import CircuitBreaker, CircuitBreakerError  # type: ignore
import httpx
from structlog import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


class APICircuitBreaker(CircuitBreaker):
    """Circuit breaker for API calls."""

    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60
    EXPECTED_EXCEPTION = httpx.HTTPError

    def __init__(self, name: str | None = None):
        super().__init__(
            name=name,
            failure_threshold=self.FAILURE_THRESHOLD,
            recovery_timeout=self.RECOVERY_TIMEOUT,
            expected_exception=self.EXPECTED_EXCEPTION,
        )

    # def _on_state_change(
    #     self,
    #     cb: "CircuitBreaker",
    #     old_state: str,
    #     new_state: str,
    # ) -> None:
    #     """Log state changes."""
    #     logger.warning(
    #         "circuit_breaker_state_change",
    #         circuit=cb.name,
    #         old_state=str(old_state),
    #         new_state=str(new_state),
    #     )


# Create a global instance for DMarket API
dmarket_api_breaker = APICircuitBreaker(name="dmarket_api")


async def call_with_circuit_breaker(
    func: Callable[..., Any],
    *args: Any,
    fallback: Callable[[], Awaitable[Any]] | None = None,
    **kwargs: Any,
) -> Any:
    """Call an async function with circuit breaker protection.

    Args:
        func: Async function to call
        fallback: Optional async callable to execute if circuit is open
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Function result or fallback result

    Raises:
        CircuitBreakerError: If circuit is open and no fallback provided
        Exception: Original exception if call fails

    """

    @dmarket_api_breaker
    async def _wrapper() -> Any:
        return await func(*args, **kwargs)

    try:
        return await _wrapper()
    except CircuitBreakerError as e:
        logger.error(  # noqa: TRY400
            "circuit_breaker_open",
            circuit="dmarket_api",
            error=str(e),
        )
        if fallback:
            logger.info("executing_fallback", circuit="dmarket_api")
            return await fallback()
        raise
