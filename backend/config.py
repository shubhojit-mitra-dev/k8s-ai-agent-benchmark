"""
Configuration and constants for the Kubernetes AI Agent Benchmark.
Adheres strictly to academic evaluation standards and reproducible execution.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Set

# Benchmark Metadata and Versioning (Frozen)
BENCHMARK_VERSION: str = "K8S-AI-JEV-v1.0"
SCENARIO_VERSION: str = "v1.0"
PROMPT_VERSION: str = "v1.0"
EVALUATION_VERSION: str = "v1.0"
TOOL_CATALOG_VERSION: str = "v1.0"

# Model Identifiers
CF_SONNET_DEFAULT_MODEL: str = "anthropic/claude-sonnet-5"
CF_JEV_DEFAULT_MODEL: str = "typesafe/jev"
OR_SONNET_DEFAULT_MODEL: str = "anthropic/claude-sonnet-5"
OR_JEV_DEFAULT_MODEL: str = "~typesafe/jev-latest"

# Execution Constraints
DEFAULT_MAX_STEPS: int = 20
QUICK_MAX_STEPS: int = 10
DEEP_MAX_STEPS: int = 30
DEFAULT_TIMEOUT_SECONDS: float = 120.0
HTTP_REQUEST_TIMEOUT_SECONDS: float = 15.0
MAX_API_RETRIES: int = 1

RETRYABLE_HTTP_STATUS_CODES: Set[int] = {408, 429, 500, 502, 503, 504}
NON_RETRYABLE_HTTP_STATUS_CODES: Set[int] = {401, 403, 404}


class BenchmarkMode(str, Enum):
    SMOKE = "smoke"
    QUICK = "quick"
    FULL = "full"
    DEEP = "deep"
    LATENCY = "latency"
    QUALITY = "quality"
    SAFETY = "safety"
    COST = "cost"
    DIFFICULTY = "difficulty"
    HYBRID = "hybrid"
    CONCURRENCY = "concurrency"


class OpenRouterRoutingMode(str, Enum):
    DEFAULT = "default"
    LATENCY_ORIENTED = "latency-oriented"
    PINNED_PROVIDER = "pinned-provider"


class ReasoningEffort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class PricingConfig:
    """Configurable pricing structure in USD per 1M tokens."""
    sonnet_input_per_million: float = 3.00
    sonnet_output_per_million: float = 15.00
    jev_input_per_million: float = 0.10
    jev_output_per_million: float = 0.30


@dataclass
class BenchmarkSettings:
    cloudflare_account_id: str = field(
        default_factory=lambda: os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    )
    cloudflare_api_token: str = field(
        default_factory=lambda: os.getenv("CLOUDFLARE_API_TOKEN", "")
    )
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    cf_sonnet_model: str = field(
        default_factory=lambda: os.getenv("CF_SONNET_MODEL", CF_SONNET_DEFAULT_MODEL)
    )
    cf_jev_model: str = field(
        default_factory=lambda: os.getenv("CF_JEV_MODEL", CF_JEV_DEFAULT_MODEL)
    )
    or_sonnet_model: str = field(
        default_factory=lambda: os.getenv("OR_SONNET_MODEL", OR_SONNET_DEFAULT_MODEL)
    )
    or_jev_model: str = field(
        default_factory=lambda: os.getenv("OR_JEV_MODEL", OR_JEV_DEFAULT_MODEL)
    )
    routing_mode: OpenRouterRoutingMode = OpenRouterRoutingMode.DEFAULT
    reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH
    pricing: PricingConfig = field(default_factory=PricingConfig)
    results_dir: Path = field(
        default_factory=lambda: Path(os.getenv("RESULTS_DIR", "results/runs"))
    )

    def is_cf_configured(self) -> bool:
        return bool(self.cloudflare_account_id and self.cloudflare_api_token)

    def is_or_configured(self) -> bool:
        return bool(self.openrouter_api_key)


SECRET_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]+['\"]?", re.IGNORECASE),
    re.compile(r"gho_[A-Za-z0-9_]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_\-]+", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Sanitizes text to prevent any credential leaks into logs or reports."""
    if not text:
        return text
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized
