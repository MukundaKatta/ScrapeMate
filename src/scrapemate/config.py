"""Configuration for ScrapeMate."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ScrapeConfig:
    """Scraping configuration."""

    log_level: str = "INFO"
    request_timeout: int = 30
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    user_agent: str = "ScrapeMate/0.1.0"

    @classmethod
    def from_env(cls) -> ScrapeConfig:
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )
