"""
Base provider abstraction and common telemetric interfaces.
Enforces monotonic time tracking, secret redaction, and retry policies.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.config import (
    BenchmarkSettings,
    PricingConfig,
    RETRYABLE_HTTP_STATUS_CODES,
    NON_RETRYABLE_HTTP_STATUS_CODES,
    redact_secrets,
)
from backend.models.decisions import JevDecision, SonnetDecision


class ProviderResponse(BaseModel):
    status_code: int
    monotonic_latency_ms: float
    request_start_ms: float
    request_end_ms: float
    model: str
    provider: str
    routed_provider: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    reported_cost_usd: Optional[float] = None
    estimated_cost_usd: float = 0.0
    cost_source: str = "estimated"
    retries: int = 0
    raw_payload: Optional[str] = None
    jev_decision: Optional[JevDecision] = None
    sonnet_decision: Optional[SonnetDecision] = None
    tool_call: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for all LLM and decision model provider adapters."""

    def __init__(self, model_id: str, provider_name: str, settings: BenchmarkSettings) -> None:
        self.model_id = model_id
        self.provider_name = provider_name
        self.settings = settings
        self.pricing: PricingConfig = settings.pricing

    def calculate_cost(
        self, input_tokens: int, output_tokens: int, is_jev: bool = False
    ) -> float:
        """Calculates standard estimated cost in USD based on frozen benchmark pricing."""
        if is_jev:
            inp_rate = self.pricing.jev_input_per_million / 1_000_000.0
            out_rate = self.pricing.jev_output_per_million / 1_000_000.0
        else:
            inp_rate = self.pricing.sonnet_input_per_million / 1_000_000.0
            out_rate = self.pricing.sonnet_output_per_million / 1_000_000.0
        return (input_tokens * inp_rate) + (output_tokens * out_rate)

    @abstractmethod
    async def call_jev_decision(
        self,
        incident_alert: Dict[str, Any],
        accumulated_evidence: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ProviderResponse:
        """Invokes the Jev fast decision controller."""
        pass

    @abstractmethod
    async def call_sonnet_investigation(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        """Invokes Claude Sonnet 5 for autonomous tool calling investigation."""
        pass

    @abstractmethod
    async def call_sonnet_final_decision(
        self,
        system_prompt: str,
        incident_alert: Dict[str, Any],
        evidence_history: List[Dict[str, Any]],
        jev_recommendation: Optional[JevDecision] = None,
    ) -> ProviderResponse:
        """Invokes Claude Sonnet 5 for final structured synthesis and decision."""
        pass

    @abstractmethod
    async def smoke_test(self) -> bool:
        """Performs a lightweight sanity check against the live endpoint."""
        pass
