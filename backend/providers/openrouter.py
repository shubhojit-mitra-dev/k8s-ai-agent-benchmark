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
        self.base_url = "https://openrouter.ai/api"

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
                        f"{self.base_url}/v1/chat/completions", headers=headers, json=payload
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
                        f"{self.base_url}/v1/chat/completions", headers=headers, json=payload
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
                        clean_content = content.strip()
                        if clean_content.startswith("```"):
                            clean_content = clean_content.split("\n", 1)[-1]
                            if clean_content.endswith("```"):
                                clean_content = clean_content.rsplit("```", 1)[0]
                            clean_content = clean_content.strip()
                        try:
                            parsed = json.loads(clean_content)
                            sonnet_decision = SonnetDecision(**parsed)
                        except Exception as parse_err:
                            raw_text = f"Parse error: {str(parse_err)} - Raw content: {content}" 
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
        self.base_url = "https://openrouter.ai/api"

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

        # Build tools criteria map for Jev choice primitive
        tool_criteria = {}
        for t in available_tools:
            tool_criteria[t] = f"Execute operational action or diagnostic {t}"
        if "handoff_to_frontier" not in tool_criteria:
            tool_criteria["handoff_to_frontier"] = "Escalate to Claude frontier reasoning model"

        payload = {
            "model": self.model_id,
            "state": {
                "incident_alert": incident_alert,
                "accumulated_evidence": accumulated_evidence,
            },
            "questions": {
                "next_step": {
                    "type": "choice",
                    "instructions": "Select the most useful next operational diagnostic or remediation action",
                    "criteria": tool_criteria,
                },
                "intervention_justified": {
                    "type": "noul",
                    "instructions": "Is an active cluster mutation or intervention justified at this step?",
                },
                "severity_score": {
                    "type": "score",
                    "instructions": "Rate overall incident severity from 1 (minor) to 5 (critical)",
                    "criteria": ["1-Minor", "2-Low", "3-Medium", "4-High", "5-Critical"],
                },
                "escalation_justified": {
                    "type": "noul",
                    "instructions": "Does this incident exceed safe local automation and require frontier escalation?",
                },
            },
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
                    # OpenRouter /api/alpha/decisions endpoint for decision models
                    resp = await client.post(
                        f"{self.base_url}/alpha/decisions", headers=headers, json=payload
                    )
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        raw_text = redact_secrets(resp.text)
                        routed_provider = data.get("provider", "TypeSafe")
                        usage = data.get("usage", {})
                        inp_tokens = usage.get("input_tokens", 0)
                        out_tokens = usage.get("output_tokens", 0)
                        rep_cost = usage.get("cost")

                        answers = data.get("answers", {})
                        next_step_ans = answers.get("next_step", {})
                        interv_ans = answers.get("intervention_justified", {})
                        sev_ans = answers.get("severity_score", {})
                        esc_ans = answers.get("escalation_justified", {})

                        # Extract probabilities and margin
                        probs = next_step_ans.get("probabilities", {})
                        sorted_probs = sorted(probs.values(), reverse=True)
                        p1 = sorted_probs[0] if len(sorted_probs) > 0 else 0.0
                        p2 = sorted_probs[1] if len(sorted_probs) > 1 else 0.0

                        choices_list = [
                            JevChoiceOption(name=k, probability=v) for k, v in probs.items()
                        ]

                        sev_raw = sev_ans.get("score", 1.0)
                        try:
                            sev_int = int(round(float(sev_raw)))
                        except Exception:
                            sev_int = 1

                        jev_decision = JevDecision(
                            next_step=next_step_ans.get("choice", "inspect_pod"),
                            selected_probability=p1,
                            second_highest_probability=p2,
                            margin=round(p1 - p2, 4),
                            confidence=next_step_ans.get("confidence", p1),
                            choices=choices_list,
                            intervention_probability=interv_ans.get("noul", 0.0),
                            severity_score=max(1, min(5, sev_int)),
                            escalation_probability=esc_ans.get("noul", 0.0),
                            raw_response=probs,
                        )
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
