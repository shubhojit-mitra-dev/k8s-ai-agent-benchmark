"""
Cloudflare Workers AI Provider Adapter for Claude Sonnet 5 and Jev.
Handles direct Cloudflare inference APIs with monotonic telemetry and billing.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
import httpx
from backend.config import BenchmarkSettings, redact_secrets
from backend.models.decisions import JevDecision, JevChoiceOption, SonnetDecision
from backend.providers.base import BaseProvider, ProviderResponse


class CloudflareSonnetProvider(BaseProvider):
    """Adapter for Claude Sonnet 5 hosted on Cloudflare Workers AI."""

    def __init__(self, model_id: str, settings: BenchmarkSettings) -> None:
        super().__init__(model_id=model_id, provider_name="Cloudflare", settings=settings)
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"

    async def call_sonnet_investigation(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        req_start_ms = time.time() * 1000

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "tools": tools,
            "max_tokens": 1024,
        }

        status_code = 500
        inp_tokens = 0
        out_tokens = 0
        reasoning_tokens = 0
        tool_call = None
        raw_text = ""
        retries = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/{self.model_id}", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        result = data.get("result", {})
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        reasoning_tokens = usage.get("reasoning_tokens", 0)

                        if "tool_calls" in result and result["tool_calls"]:
                            tc = result["tool_calls"][0]
                            tool_call = {"name": tc.get("name"), "arguments": tc.get("arguments", {})}
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
            provider="Cloudflare",
            routed_provider="Cloudflare Workers AI",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=reasoning_tokens,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
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
            "Authorization": f"Bearer {self.api_token}",
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

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Produce final incident synthesis JSON according to strict schema.\nData: {json.dumps(user_content)}",
                },
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1024,
        }

        status_code = 500
        inp_tokens = 0
        out_tokens = 0
        reasoning_tokens = 0
        sonnet_decision = None
        raw_text = ""
        retries = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/{self.model_id}", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        content = data.get("result", {}).get("response", "{}")
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        reasoning_tokens = usage.get("reasoning_tokens", 0)
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
            provider="Cloudflare",
            routed_provider="Cloudflare Workers AI",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=reasoning_tokens,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
            retries=retries,
            raw_payload=raw_text,
            sonnet_decision=sonnet_decision,
        )

    async def call_jev_decision(self, *args, **kwargs) -> ProviderResponse:
        raise NotImplementedError("CloudflareSonnetProvider does not handle Jev decisions directly")

    async def smoke_test(self) -> bool:
        if not (self.account_id and self.api_token):
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/models/search",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                return res.status_code == 200
        except Exception:
            return False


class CloudflareJevProvider(BaseProvider):
    """Adapter for Jev fast decision model on Cloudflare Workers AI."""

    def __init__(self, model_id: str, settings: BenchmarkSettings) -> None:
        super().__init__(model_id=model_id, provider_name="Cloudflare-Jev", settings=settings)
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"

    async def call_jev_decision(
        self,
        incident_alert: Dict[str, Any],
        accumulated_evidence: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        req_start_ms = time.time() * 1000

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        instructions = (
            "Select the most useful next operational step supported by current incident evidence. "
            "Questions: 1. next_step choice, 2. intervention_justified (0.0-1.0), "
            "3. severity_score (1-5), 4. escalation_justified (0.0-1.0)."
        )
        payload = {
            "instructions": instructions,
            "incident": incident_alert,
            "evidence": accumulated_evidence,
            "tools": available_tools,
        }

        status_code = 500
        inp_tokens = 0
        out_tokens = 0
        jev_decision = None
        raw_text = ""
        retries = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for attempt in range(2):
                    resp = await client.post(
                        f"{self.base_url}/{self.model_id}", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        result = data.get("result", {})
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("prompt_tokens", 0)
                        out_tokens = usage.get("completion_tokens", 0)
                        parsed = result if isinstance(result, dict) else json.loads(result)
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
            provider="Cloudflare-Jev",
            routed_provider="Cloudflare Workers AI",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
            retries=retries,
            raw_payload=raw_text,
            jev_decision=jev_decision,
        )

    async def call_sonnet_investigation(self, *args, **kwargs) -> ProviderResponse:
        raise NotImplementedError("JevProvider does not execute Sonnet investigation loops")

    async def call_sonnet_final_decision(self, *args, **kwargs) -> ProviderResponse:
        raise NotImplementedError("JevProvider does not execute Sonnet final decisions")

    async def smoke_test(self) -> bool:
        return bool(self.account_id and self.api_token)
