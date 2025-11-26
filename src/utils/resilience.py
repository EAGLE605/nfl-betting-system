"""
Resilience Patterns for API Calls

Implements:
1. Circuit Breaker - Prevents cascade failures
2. Exponential Backoff - Smart retry logic
3. Fallback Chains - Graceful degradation

BEGINNER GUIDE:
---------------
Circuit Breaker: Like a home electrical breaker. If an API fails too many times,
the breaker "trips" and stops making calls for a while. This prevents:
- Wasting time on a dead API
- Overwhelming a struggling service
- Cascade failures across your system

States:
- CLOSED: Normal operation, requests go through
- OPEN: Breaker tripped, requests fail immediately (fast-fail)
- HALF-OPEN: Testing if service recovered

Exponential Backoff: Instead of retrying immediately, wait longer each time:
- 1st retry: wait 1 second
- 2nd retry: wait 2 seconds
- 3rd retry: wait 4 seconds
- etc.

This prevents hammering a struggling service and gives it time to recover.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import pybreaker
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar("T")


# =============================================================================
# CIRCUIT BREAKER CONFIGURATION
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal - requests go through
    OPEN = "open"          # Tripped - requests fail fast
    HALF_OPEN = "half_open"  # Testing - limited requests


class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    """
    Custom listener for circuit breaker events.
    Logs state changes for monitoring.
    """

    def __init__(self, name: str):
        self.name = name
        self.state_changes: List[Dict] = []

    def state_change(self, cb: pybreaker.CircuitBreaker, old_state: pybreaker.CircuitBreakerState, new_state: pybreaker.CircuitBreakerState):
        """Called when circuit state changes."""
        change = {
            "timestamp": datetime.now().isoformat(),
            "breaker": self.name,
            "from": old_state.name,
            "to": new_state.name,
        }
        self.state_changes.append(change)

        if new_state.name == "open":
            logger.warning(f"[CIRCUIT BREAKER] {self.name} OPENED - API failing, fast-failing requests")
        elif new_state.name == "closed":
            logger.info(f"[CIRCUIT BREAKER] {self.name} CLOSED - API recovered, resuming normal operation")
        elif new_state.name == "half-open":
            logger.info(f"[CIRCUIT BREAKER] {self.name} HALF-OPEN - Testing if API recovered")

    def failure(self, cb: pybreaker.CircuitBreaker, exc: Exception):
        """Called on each failure."""
        logger.debug(f"[CIRCUIT BREAKER] {self.name} failure recorded: {type(exc).__name__}")

    def success(self, cb: pybreaker.CircuitBreaker):
        """Called on each success."""
        pass  # Don't log every success


# =============================================================================
# CIRCUIT BREAKERS FOR EACH API
# =============================================================================

# ESPN API Circuit Breaker
# - Fails fast after 5 consecutive failures
# - Stays open for 60 seconds before testing again
espn_listener = CircuitBreakerListener("ESPN")
espn_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    listeners=[espn_listener],
    exclude=[ValueError, KeyError],  # Don't trip on validation errors
)

# Odds API Circuit Breaker
# - More conservative (3 failures) because it's rate-limited
# - Longer timeout (120s) to respect rate limits
odds_listener = CircuitBreakerListener("OddsAPI")
odds_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=120,
    listeners=[odds_listener],
    exclude=[ValueError, KeyError],
)

# Weather API Circuit Breaker
# - 5 failures before tripping
# - 60 second reset
weather_listener = CircuitBreakerListener("Weather")
weather_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    listeners=[weather_listener],
    exclude=[ValueError, KeyError],
)

# LLM API Circuit Breaker (for AI council)
# - More lenient (7 failures) because LLMs can be slow
# - Longer timeout (180s) because LLMs are expensive to retry
llm_listener = CircuitBreakerListener("LLM")
llm_breaker = pybreaker.CircuitBreaker(
    fail_max=7,
    reset_timeout=180,
    listeners=[llm_listener],
    exclude=[ValueError, KeyError],
)

# Registry of all breakers for monitoring
CIRCUIT_BREAKERS = {
    "espn": espn_breaker,
    "odds": odds_breaker,
    "weather": weather_breaker,
    "llm": llm_breaker,
}


def get_circuit_status() -> Dict[str, Dict]:
    """
    Get status of all circuit breakers.

    Returns:
        Dict with breaker name -> status info

    Example:
        {
            "espn": {
                "state": "closed",
                "fail_count": 0,
                "success_count": 10,
                "last_failure": None
            }
        }
    """
    status = {}
    for name, breaker in CIRCUIT_BREAKERS.items():
        try:
            # Get state name - handle both string and object states
            state = breaker.current_state
            if hasattr(state, 'name'):
                state_name = state.name
            else:
                state_name = str(state)

            status[name] = {
                "state": state_name,
                "fail_count": breaker.fail_counter,
                "is_open": state_name.lower() == "open",
            }
        except Exception as e:
            status[name] = {
                "state": "unknown",
                "fail_count": 0,
                "is_open": False,
                "error": str(e),
            }
    return status


# =============================================================================
# RETRY DECORATORS WITH EXPONENTIAL BACKOFF
# =============================================================================

def retry_with_backoff(
    max_attempts: int = 5,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for exponential backoff retry.

    Args:
        max_attempts: Maximum retry attempts (default 5)
        min_wait: Minimum wait time in seconds (default 1)
        max_wait: Maximum wait time in seconds (default 60)
        exceptions: Tuple of exceptions to retry on

    Example:
        @retry_with_backoff(max_attempts=3)
        def fetch_data():
            return api.get_data()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )


# Pre-configured retry decorators for common scenarios

# Standard API retry: 5 attempts, 1-60s backoff
api_retry = retry_with_backoff(
    max_attempts=5,
    min_wait=1.0,
    max_wait=60.0,
    exceptions=(ConnectionError, TimeoutError, IOError),
)

# Aggressive retry for critical operations: 7 attempts
critical_retry = retry_with_backoff(
    max_attempts=7,
    min_wait=2.0,
    max_wait=120.0,
    exceptions=(ConnectionError, TimeoutError, IOError),
)

# Quick retry for fast operations: 3 attempts, short waits
quick_retry = retry_with_backoff(
    max_attempts=3,
    min_wait=0.5,
    max_wait=10.0,
    exceptions=(ConnectionError, TimeoutError),
)


# =============================================================================
# COMBINED CIRCUIT BREAKER + RETRY DECORATOR
# =============================================================================

def resilient_call(
    breaker: pybreaker.CircuitBreaker,
    max_retries: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    fallback: Optional[Callable[[], T]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Combined circuit breaker + retry + fallback decorator.

    This is the recommended way to wrap API calls. It:
    1. Retries transient failures with exponential backoff
    2. Trips circuit breaker after repeated failures
    3. Falls back to alternative if circuit is open

    Args:
        breaker: Which circuit breaker to use
        max_retries: Max retry attempts
        min_wait: Min backoff wait
        max_wait: Max backoff wait
        fallback: Optional fallback function if circuit is open

    Example:
        @resilient_call(espn_breaker, fallback=lambda: cached_data())
        def fetch_espn_scores():
            return espn_api.get_scores()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check if circuit is open
            if breaker.current_state == pybreaker.STATE_OPEN:
                logger.warning(f"Circuit breaker OPEN for {func.__name__}, using fallback")
                if fallback:
                    return fallback()
                raise pybreaker.CircuitBreakerError(f"Circuit breaker open for {func.__name__}")

            # Create retry wrapper
            @retry(
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
                reraise=True,
            )
            def call_with_retry():
                return breaker.call(func, *args, **kwargs)

            try:
                return call_with_retry()
            except RetryError as e:
                logger.error(f"All retries exhausted for {func.__name__}: {e}")
                if fallback:
                    return fallback()
                raise
            except pybreaker.CircuitBreakerError as e:
                logger.warning(f"Circuit breaker tripped for {func.__name__}")
                if fallback:
                    return fallback()
                raise

        return wrapper
    return decorator


# =============================================================================
# FALLBACK UTILITIES
# =============================================================================

class FallbackChain:
    """
    Chain of fallback functions for graceful degradation.

    Tries each function in order until one succeeds.

    Example:
        chain = FallbackChain([
            lambda: fetch_from_primary_api(),
            lambda: fetch_from_backup_api(),
            lambda: load_from_cache(),
        ])
        result = chain.execute()
    """

    def __init__(self, fallbacks: List[Callable[[], T]]):
        self.fallbacks = fallbacks
        self.last_error: Optional[Exception] = None
        self.successful_index: Optional[int] = None

    def execute(self) -> T:
        """Execute fallback chain until success."""
        errors = []

        for i, fallback in enumerate(self.fallbacks):
            try:
                result = fallback()
                self.successful_index = i
                if i > 0:
                    logger.info(f"Fallback #{i} succeeded after {i} failures")
                return result
            except Exception as e:
                errors.append((i, type(e).__name__, str(e)))
                self.last_error = e
                logger.warning(f"Fallback #{i} failed: {type(e).__name__}: {e}")
                continue

        # All fallbacks failed
        error_summary = "; ".join([f"#{i}: {t}" for i, t, _ in errors])
        raise RuntimeError(f"All {len(self.fallbacks)} fallbacks failed: {error_summary}")


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Token bucket rate limiter.

    Controls request rate to respect API limits.

    Example:
        limiter = RateLimiter(requests_per_minute=60)

        @limiter.limit
        def make_api_call():
            return api.request()
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_day: Optional[int] = None,
    ):
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.daily_count = 0
        self.daily_reset = datetime.now().date()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Refill at rate of rpm tokens per minute
        refill = elapsed * (self.rpm / 60)
        self.tokens = min(self.rpm, self.tokens + refill)
        self.last_update = now

        # Reset daily counter if new day
        if datetime.now().date() > self.daily_reset:
            self.daily_count = 0
            self.daily_reset = datetime.now().date()

    def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire a token, waiting if necessary.

        Returns:
            True if token acquired, False if timeout
        """
        start = time.time()

        while True:
            self._refill()

            # Check daily limit
            if self.rpd and self.daily_count >= self.rpd:
                logger.warning("Daily rate limit reached")
                return False

            # Check per-minute limit
            if self.tokens >= 1:
                self.tokens -= 1
                self.daily_count += 1
                return True

            # Wait and retry
            if time.time() - start > timeout:
                return False

            time.sleep(0.1)

    def limit(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to rate limit a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.acquire():
                raise RuntimeError("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper

    def get_status(self) -> Dict:
        """Get current rate limiter status."""
        self._refill()
        return {
            "tokens_available": round(self.tokens, 2),
            "daily_used": self.daily_count,
            "daily_limit": self.rpd,
            "daily_remaining": (self.rpd - self.daily_count) if self.rpd else None,
        }


# Pre-configured rate limiters
odds_api_limiter = RateLimiter(
    requests_per_minute=10,
    requests_per_day=500,  # Free tier limit
)

espn_limiter = RateLimiter(
    requests_per_minute=30,  # Be nice to ESPN
)

llm_limiter = RateLimiter(
    requests_per_minute=20,  # Prevent cost overrun
)


# =============================================================================
# MONITORING & METRICS
# =============================================================================

class ResilienceMetrics:
    """
    Tracks resilience metrics for monitoring.
    """

    def __init__(self):
        self.call_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}
        self.retry_counts: Dict[str, int] = {}
        self.fallback_counts: Dict[str, int] = {}
        self.latencies: Dict[str, List[float]] = {}

    def record_call(self, name: str, latency: float, success: bool, retries: int = 0):
        """Record a call's metrics."""
        self.call_counts[name] = self.call_counts.get(name, 0) + 1

        if not success:
            self.failure_counts[name] = self.failure_counts.get(name, 0) + 1

        if retries > 0:
            self.retry_counts[name] = self.retry_counts.get(name, 0) + retries

        if name not in self.latencies:
            self.latencies[name] = []
        self.latencies[name].append(latency)

        # Keep only last 100 latencies
        if len(self.latencies[name]) > 100:
            self.latencies[name] = self.latencies[name][-100:]

    def record_fallback(self, name: str):
        """Record a fallback usage."""
        self.fallback_counts[name] = self.fallback_counts.get(name, 0) + 1

    def get_summary(self) -> Dict:
        """Get metrics summary."""
        summary = {}

        for name in self.call_counts:
            calls = self.call_counts.get(name, 0)
            failures = self.failure_counts.get(name, 0)
            retries = self.retry_counts.get(name, 0)
            fallbacks = self.fallback_counts.get(name, 0)
            latencies = self.latencies.get(name, [])

            summary[name] = {
                "total_calls": calls,
                "failures": failures,
                "success_rate": (calls - failures) / calls if calls > 0 else 0,
                "total_retries": retries,
                "fallback_uses": fallbacks,
                "avg_latency_ms": sum(latencies) / len(latencies) * 1000 if latencies else 0,
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] * 1000 if len(latencies) >= 20 else None,
            }

        return summary


# Global metrics instance
metrics = ResilienceMetrics()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def with_resilience(
    name: str,
    breaker: Optional[pybreaker.CircuitBreaker] = None,
    rate_limiter: Optional[RateLimiter] = None,
    max_retries: int = 3,
    fallback: Optional[Callable] = None,
):
    """
    All-in-one resilience decorator.

    Combines circuit breaker, rate limiting, retries, and metrics.

    Example:
        @with_resilience("espn", espn_breaker, espn_limiter)
        def fetch_espn_data():
            return requests.get("https://espn.com/api")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            retries_used = 0

            try:
                # Rate limit check
                if rate_limiter and not rate_limiter.acquire(timeout=10):
                    raise RuntimeError(f"Rate limit exceeded for {name}")

                # Circuit breaker check
                if breaker and breaker.current_state == pybreaker.STATE_OPEN:
                    logger.warning(f"Circuit open for {name}, using fallback")
                    metrics.record_fallback(name)
                    if fallback:
                        return fallback()
                    raise pybreaker.CircuitBreakerError(f"Circuit open for {name}")

                # Retry loop
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        if breaker:
                            result = breaker.call(func, *args, **kwargs)
                        else:
                            result = func(*args, **kwargs)

                        # Success
                        latency = time.time() - start_time
                        metrics.record_call(name, latency, success=True, retries=retries_used)
                        return result

                    except (ConnectionError, TimeoutError, IOError) as e:
                        last_error = e
                        retries_used += 1

                        if attempt < max_retries:
                            wait_time = min(2 ** attempt, 30)  # Exponential backoff
                            logger.warning(f"{name} attempt {attempt + 1} failed, retrying in {wait_time}s")
                            time.sleep(wait_time)
                        else:
                            raise

            except Exception as e:
                latency = time.time() - start_time
                metrics.record_call(name, latency, success=False, retries=retries_used)

                if fallback:
                    metrics.record_fallback(name)
                    return fallback()
                raise

        return wrapper
    return decorator
