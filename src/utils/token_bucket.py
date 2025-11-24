"""
Token Bucket Rate Limiting

Implements token bucket algorithm for API rate limiting.
Supports multiple APIs with independent buckets.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimitStatus(Enum):
    """Rate limit status levels."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.

    Tokens are added at a constant rate (refill_rate per second).
    Each API call consumes tokens (cost).
    When bucket is empty, requests must wait or be rejected.
    """

    capacity: int  # Maximum tokens in bucket
    refill_rate: float  # Tokens per second
    tokens: float = None  # Current tokens
    last_refill: float = None  # Timestamp of last refill
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        """Initialize tokens to capacity."""
        if self.tokens is None:
            self.tokens = float(self.capacity)
        if self.last_refill is None:
            self.last_refill = time.time()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed > 0:
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

    def check(self, cost: int = 1) -> bool:
        """
        Check if request can be made (non-consuming peek).

        Args:
            cost: Number of tokens required

        Returns:
            True if enough tokens available, False otherwise
        """
        with self.lock:
            self._refill()
            return self.tokens >= cost

    def consume(self, cost: int = 1) -> bool:
        """
        Consume tokens for a request.

        Args:
            cost: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        with self.lock:
            self._refill()

            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False

    def get_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        with self.lock:
            self._refill()

            pct_remaining = self.tokens / self.capacity

            if pct_remaining >= 0.5:
                return RateLimitStatus.OK
            elif pct_remaining >= 0.1:
                return RateLimitStatus.WARNING
            elif pct_remaining > 0:
                return RateLimitStatus.CRITICAL
            else:
                return RateLimitStatus.EXHAUSTED

    def get_tokens_remaining(self) -> float:
        """Get number of tokens remaining."""
        with self.lock:
            self._refill()
            return self.tokens

    def reset(self):
        """Reset bucket to full capacity."""
        with self.lock:
            self.tokens = float(self.capacity)
            self.last_refill = time.time()


class MultiAPITokenBucket:
    """
    Manages token buckets for multiple APIs.

    Each API has its own bucket with independent limits.
    """

    def __init__(self):
        """Initialize multi-API token bucket manager."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

        # Default configurations for common APIs
        self.default_configs = {
            "odds_api": {
                "capacity": 500,  # Monthly limit
                "refill_rate": 500 / (30 * 24 * 3600),  # Per second
            },
            "espn_api": {
                "capacity": 100,  # Daily limit
                "refill_rate": 100 / (24 * 3600),  # Per second
            },
            "noaa_api": {
                "capacity": 1000,  # Daily limit
                "refill_rate": 1000 / (24 * 3600),  # Per second
            },
        }

    def register_api(self, api_name: str, capacity: int, refill_rate: float):
        """
        Register an API with its rate limits.

        Args:
            api_name: Name of the API
            capacity: Maximum tokens
            refill_rate: Tokens per second
        """
        with self.lock:
            self.buckets[api_name] = TokenBucket(
                capacity=capacity, refill_rate=refill_rate
            )
            logger.info(
                f"Registered API: {api_name} (capacity={capacity}, rate={refill_rate:.6f}/s)"
            )

    def register_default(self, api_name: str):
        """Register API with default configuration."""
        if api_name in self.default_configs:
            config = self.default_configs[api_name]
            self.register_api(api_name, config["capacity"], config["refill_rate"])
        else:
            # Use generic defaults if no specific config
            logger.warning(f"No default config for {api_name}, using generic defaults")
            self.register_api(
                api_name, capacity=100, refill_rate=100 / (24 * 3600)
            )  # 100/day default

    def check(self, api_name: str, cost: int = 1) -> bool:
        """
        Check if API call can be made (non-consuming).

        Args:
            api_name: Name of the API
            cost: Token cost of the request

        Returns:
            True if call can be made, False otherwise
        """
        with self.lock:
            if api_name not in self.buckets:
                self.register_default(api_name)

            bucket = self.buckets[api_name]
            return bucket.check(cost)

    def can_call_api(self, api_name: str, cost: int = 1) -> bool:
        """
        Check if API can be called (alias for check).

        Args:
            api_name: Name of the API
            cost: Token cost of the request

        Returns:
            True if call can be made, False otherwise
        """
        return self.check(api_name, cost)

    def consume(self, api_name: str, cost: int = 1) -> bool:
        """
        Consume tokens for an API call.

        Args:
            api_name: Name of the API
            cost: Token cost of the request

        Returns:
            True if tokens consumed, False if insufficient
        """
        with self.lock:
            if api_name not in self.buckets:
                self.register_default(api_name)

            bucket = self.buckets[api_name]
            success = bucket.consume(cost)

            if success:
                logger.debug(f"Consumed {cost} tokens from {api_name} bucket")
            else:
                logger.warning(
                    f"Insufficient tokens for {api_name} (need {cost}, have {bucket.get_tokens_remaining():.2f})"
                )

            return success

    def record_api_call(self, api_name: str, cost: int = 1) -> bool:
        """
        Record an API call (alias for consume).

        Args:
            api_name: Name of the API
            cost: Token cost of the request

        Returns:
            True if call recorded, False if rate limited
        """
        return self.consume(api_name, cost)

    def get_status(self, api_name: str) -> RateLimitStatus:
        """Get rate limit status for an API."""
        with self.lock:
            if api_name not in self.buckets:
                return RateLimitStatus.OK  # Unknown API, assume OK

            return self.buckets[api_name].get_status()

    def get_tokens_remaining(self, api_name: str) -> float:
        """Get tokens remaining for an API."""
        with self.lock:
            if api_name not in self.buckets:
                return float("inf")  # Unknown API, assume unlimited

            return self.buckets[api_name].get_tokens_remaining()

    def get_rate_limit_stats(self) -> Dict:
        """Get statistics for all APIs."""
        with self.lock:
            stats = {}
            for api_name, bucket in self.buckets.items():
                tokens = bucket.get_tokens_remaining()
                status = bucket.get_status()
                capacity = bucket.capacity

                stats[api_name] = {
                    "tokens_remaining": tokens,
                    "capacity": capacity,
                    "utilization_pct": (
                        ((capacity - tokens) / capacity * 100) if capacity > 0 else 0
                    ),
                    "status": status.value,
                }

            return stats

    def reset(self, api_name: Optional[str] = None):
        """
        Reset token bucket(s).

        Args:
            api_name: API to reset (None = reset all)
        """
        with self.lock:
            if api_name:
                if api_name in self.buckets:
                    self.buckets[api_name].reset()
                    logger.info(f"Reset token bucket for {api_name}")
            else:
                for api_name, bucket in self.buckets.items():
                    bucket.reset()
                logger.info("Reset all token buckets")
