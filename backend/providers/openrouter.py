"""
OpenRouter Provider Adapter for Claude Sonnet 5 and Jev.
Tracks OpenRouter provider routing metadata, pricing, and latency.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
import httpx
from backend.config import BenchmarkSettings, redact_secrets
from backend.models.decisions import JevDecision, JevChoiceOption, SonnetDecision
from backend.providers.base import BaseProvider, ProviderResponse


class OpenRouterSonnetProvider(BaseProvider):
    """Adapter for Claude Sonnet 5 hosted via OpenRouter."""

    def __init__(self, model_id: str, settings: BenchmarkSettings) -> None:
        super().__init__(model_id=model_id, provider_name="OpenRouter", settings=settings)
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def call_sonnet_investigation(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        req_start_ms = time.time() * 1000

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/shubhojit-mitra-dev/k8s-ai-agent-benchmark",
            "X-Title": "Kubernetes AI Agent Benchmark",
            "Content-Type": "application/json",
        }

        # Configure OpenRouter routing preferences
        provider_routing: Dict[str, Any] = {}
        if self.settings.routing_mode.value == "latency-oriented":
            provider_routing["sort"] = "throughput"
        elif self.settings.routing_mode.value == "pinned-provider":
            provider_routing["order"] = ["Anthropic"]

        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "tools": tools,
            "temperature": 0.0,
            "max_tokens": 1024,
        }
        if provider_routing:
            payload["provider"] = provider_routing

        retries = 0
        status_code = 500
        routed_provider = None
        inp_tokens = 0
        out_tokens = 0
        reasoning_tokens = 0
        rep_cost = None
        tool_call = None
        raw_text = ""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        routed_provider = data.get("provider", "Anthropic (routed)")
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        reasoning_tokens = usage.get("reasoning_tokens", 0)
                        rep_cost = usage.get("cost")

                        choice = data.get("choices", [{}])[0]
                        message = choice.get("message", {})
                        if "tool_calls" in message and message["tool_calls"]:
                            tc = message["tool_calls"][0]
                            fn = tc.get("function", {})
                            args = json.loads(fn.get("arguments", "{}"))
                            tool_call = {"name": fn.get("name"), "arguments": args}
                        break
                    elif status_code in {408, 429, 500, 502, 503, 504} and attempt == 0:
                        retries += 1
                        time.sleep(1.0)
                        continue
                    else:
                        raw_text = redact_secrets(resp.text)
                        break
        except Exception as e:
            raw_text = f"Connection error: {redact_secrets(str(e))}"

        end_mono = time.monotonic()
        latency_ms = (end_mono - start_mono) * 1000.0
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=False)

        return ProviderResponse(
            status_code=status_code,
            monotonic_latency_ms=latency_ms,
            request_start_ms=req_start_ms,
            request_end_ms=time.time() * 1000,
            model=self.model_id,
            provider="OpenRouter",
            routed_provider=routed_provider,
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=reasoning_tokens,
            reported_cost_usd=rep_cost,
            estimated_cost_usd=est_cost,
            cost_source="provider_reported" if rep_cost is not None else "estimated",
            retries=retries,
            raw_payload=raw_text,
            tool_call=tool_call,
        )

    async def call_sonnet_final_decision(
        self,
        system_prompt: str,
        incident_alert: Dict[str, Any],
        evidence_history: List[Dict[str, Any]],
        jev_recommendation: Optional[JevDecision] = None,
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        req_start_ms = time.time() * 1000

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/shubhojit-mitra-dev/k8s-ai-agent-benchmark",
            "X-Title": "Kubernetes AI Agent Benchmark",
            "Content-Type": "application/json",
        }

        user_content = {
            "incident_alert": incident_alert,
            "accumulated_evidence": evidence_history,
        }
        if jev_recommendation:
            user_content["untrusted_jev_assessment"] = {
                "next_step": jev_recommendation.next_step,
                "confidence": jev_recommendation.confidence,
                "severity_score": jev_recommendation.severity_score,
                "intervention_probability": jev_recommendation.intervention_probability,
            }

        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Produce final incident synthesis JSON according to strict schema.\nData: {json.dumps(user_content)}",
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 1024,
        }

        status_code = 500
        routed_provider = None
        inp_tokens = 0
        out_tokens = 0
        reasoning_tokens = 0
        rep_cost = None
        sonnet_decision = None
        raw_text = ""
        retries = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        routed_provider = data.get("provider", "Anthropic (routed)")
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        reasoning_tokens = usage.get("reasoning_tokens", 0)
                        rep_cost = usage.get("cost")

                        choice = data.get("choices", [{}])[0]
                        content = choice.get("message", {}).get("content", "{}")
                        parsed = json.loads(content)
                        sonnet_decision = SonnetDecision(**parsed)
                        break
                    elif status_code in {408, 429, 500, 502, 503, 504} and attempt == 0:
                        retries += 1
                        time.sleep(1.0)
                        continue
                    else:
                        raw_text = redact_secrets(resp.text)
                        break
        except Exception as e:
            raw_text = f"Connection error: {redact_secrets(str(e))}"

        end_mono = time.monotonic()
        latency_ms = (end_mono - start_mono) * 1000.0
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=False)

        return ProviderResponse(
            status_code=status_code,
            monotonic_latency_ms=latency_ms,
            request_start_ms=req_start_ms,
            request_end_ms=time.time() * 1000,
            model=self.model_id,
            provider="OpenRouter",
            routed_provider=routed_provider,
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=reasoning_tokens,
            reported_cost_usd=rep_cost,
            estimated_cost_usd=est_cost,
            cost_source="provider_reported" if rep_cost is not None else "estimated",
            retries=retries,
            raw_payload=raw_text,
            sonnet_decision=sonnet_decision,
        )

    async def call_jev_decision(
        self,
        incident_alert: Dict[str, Any],
        accumulated_evidence: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ProviderResponse:
        raise NotImplementedError("OpenRouterSonnetProvider does not handle Jev decisions directly")

    async def smoke_test(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return res.status_code == 200
        except Exception:
            return False


class OpenRouterJevProvider(BaseProvider):
    """Adapter for Jev fast decision model via OpenRouter."""

    def __init__(self, model_id: str, settings: BenchmarkSettings) -> None:
        super().__init__(model_id=model_id, provider_name="OpenRouter-Jev", settings=settings)
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def call_jev_decision(
        self,
        incident_alert: Dict[str, Any],
        accumulated_evidence: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        req_start_ms = time.time() * 1000

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/shubhojit-mitra-dev/k8s-ai-agent-benchmark",
            "Content-Type": "application/json",
        }

        instructions = (
            "Select the most useful next operational step supported by current incident evidence. "
            "Questions: 1. next_step choice, 2. intervention_justified (0.0-1.0), "
            "3. severity_score (1-5), 4. escalation_justified (0.0-1.0)."
        )
        prompt_data = {
            "instructions": instructions,
            "incident": incident_alert,
            "evidence": accumulated_evidence,
            "available_tools": available_tools,
        }

        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": json.dumps(prompt_data)}],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
            "max_tokens": 256,
        }

        status_code = 500
        routed_provider = None
        inp_tokens = 0
        out_tokens = 0
        rep_cost = None
        jev_decision = None
        raw_text = ""
        retries = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        routed_provider = data.get("provider", "Jev (routed)")
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        rep_cost = usage.get("cost")

                        choice = data.get("choices", [{}])[0]
                        content = choice.get("message", {}).get("content", "{}")
                        parsed = json.loads(content)
                        jev_decision = JevDecision(**parsed)
                        break
                    elif status_code in {408, 429, 500, 502, 503, 504} and attempt == 0:
                        retries += 1
                        time.sleep(0.5)
                        continue
                    else:
                        raw_text = redact_secrets(resp.text)
                        break
        except Exception as e:
            raw_text = f"Connection error: {redact_secrets(str(e))}"

        end_mono = time.monotonic()
        latency_ms = (end_mono - start_mono) * 1000.0
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=True)

        return ProviderResponse(
            status_code=status_code,
            monotonic_latency_ms=latency_ms,
            request_start_ms=req_start_ms,
            request_end_ms=time.time() * 1000,
            model=self.model_id,
            provider="OpenRouter-Jev",
            routed_provider=routed_provider,
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reported_cost_usd=rep_cost,
            estimated_cost_usd=est_cost,
            cost_source="provider_reported" if rep_cost is not None else "estimated",
            retries=retries,
            raw_payload=raw_text,
            jev_decision=jev_decision,
        )

    async def call_sonnet_investigation(self, *args, **kwargs) -> ProviderResponse:
        raise NotImplementedError("JevProvider does not execute Sonnet investigation loops")

    async def call_sonnet_final_decision(self, *args, **kwargs) -> ProviderResponse:
        raise NotImplementedError("JevProvider does not execute Sonnet final decisions")

    async def smoke_test(self) -> bool:
        return bool(self.api_key)
