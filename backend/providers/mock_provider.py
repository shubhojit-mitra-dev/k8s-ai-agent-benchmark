"""
High-fidelity Mock / Simulation Provider.
Provides deterministic, reproducible model responses for testing, offline benchmarking,
and CI environments without external API costs or credential dependencies.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from backend.config import BenchmarkSettings
from backend.models.decisions import JevDecision, JevChoiceOption, SonnetDecision
from backend.providers.base import BaseProvider, ProviderResponse


class MockModelProvider(BaseProvider):
    """
    Simulates Jev and Claude Sonnet 5 responses with realistic latencies,
    token counts, and scenario-grounded reasoning.
    """

    def __init__(self, model_id: str, provider_name: str, settings: BenchmarkSettings) -> None:
        super().__init__(model_id=model_id, provider_name=provider_name, settings=settings)

    async def call_jev_decision(
        self,
        incident_alert: Dict[str, Any],
        accumulated_evidence: List[Dict[str, Any]],
        available_tools: List[str],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        alert_str = json.dumps(incident_alert)
        ev_count = len(accumulated_evidence)

        # Realistic Jev decision heuristics
        if ev_count == 0:
            if "PaymentAPIAvailabilityLow" in alert_str or "CrashLoop" in alert_str:
                choice = "inspect_pod"
            elif "Rollout" in alert_str or "Deployment" in alert_str:
                choice = "inspect_deployment"
            elif "Service" in alert_str or "Endpoints" in alert_str:
                choice = "inspect_service"
            elif "Node" in alert_str or "DiskPressure" in alert_str or "MemoryPressure" in alert_str:
                choice = "inspect_node"
            elif "Resolution" in alert_str or "DNS" in alert_str:
                choice = "inspect_dns"
            elif "Kafka" in alert_str:
                choice = "inspect_dependency"
            else:
                choice = "inspect_pod"
            conf = 0.88
            hand_prob = 0.12
            interv_prob = 0.05
        elif ev_count == 1:
            choice = "inspect_logs" if "pod" in str(accumulated_evidence) else "inspect_events"
            conf = 0.82
            hand_prob = 0.18
            interv_prob = 0.10
        elif ev_count == 2:
            choice = "inspect_events"
            conf = 0.76
            hand_prob = 0.24
            interv_prob = 0.25
        else:
            # Beyond 3 steps, Jev hands off to frontier synthesis
            choice = "handoff_to_frontier"
            conf = 0.94
            hand_prob = 0.94
            interv_prob = 0.40

        jev_dec = JevDecision(
            next_step=choice,
            selected_probability=conf,
            second_highest_probability=round(1.0 - conf, 3),
            margin=round(conf - (1.0 - conf), 3),
            confidence=conf,
            choices=[
                JevChoiceOption(name=choice, probability=conf),
                JevChoiceOption(name="handoff_to_frontier", probability=hand_prob),
            ],
            intervention_probability=interv_prob,
            severity_score=3,
            escalation_probability=0.20 if ev_count < 3 else 0.70,
        )

        end_mono = time.monotonic()
        latency_ms = 42.5  # Realistic fast model latency
        inp_tokens = 180 + (ev_count * 95)
        out_tokens = 45
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=True)

        return ProviderResponse(
            status_code=200,
            monotonic_latency_ms=latency_ms,
            request_start_ms=start_mono * 1000,
            request_end_ms=end_mono * 1000,
            model=self.model_id,
            provider=self.provider_name,
            routed_provider=f"{self.provider_name}-direct",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
            jev_decision=jev_dec,
            raw_payload=jev_dec.model_dump_json(),
        )

    async def call_sonnet_investigation(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        step_idx = len(messages) // 2

        # Realistic sequential tool selection based on conversation context
        last_msg = messages[-1]["content"] if messages else ""
        if step_idx == 0:
            tool_call = {"name": "list_pods", "arguments": {"namespace": "payments"}}
        elif "list_pods" in str(messages) and "describe_pod" not in str(messages):
            tool_call = {"name": "describe_pod", "arguments": {"pod_name": "payments-api-5ddc1"}}
        elif "describe_pod" in str(messages) and "get_pod_metrics" not in str(messages):
            tool_call = {"name": "get_pod_metrics", "arguments": {"namespace": "payments"}}
        elif "OOM" in last_msg or "Exit Code: 137" in last_msg:
            tool_call = {
                "name": "adjust_resources",
                "arguments": {"target": "payments-api", "memory_limit": "1024Mi"},
            }
        else:
            tool_call = {"name": "get_events", "arguments": {}}

        end_mono = time.monotonic()
        latency_ms = 620.0  # Realistic frontier model latency
        inp_tokens = 1450 + (step_idx * 420)
        out_tokens = 180
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=False)

        return ProviderResponse(
            status_code=200,
            monotonic_latency_ms=latency_ms,
            request_start_ms=start_mono * 1000,
            request_end_ms=end_mono * 1000,
            model=self.model_id,
            provider=self.provider_name,
            routed_provider=f"{self.provider_name}-direct",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=90,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
            tool_call=tool_call,
            raw_payload=json.dumps({"tool_calls": [tool_call]}),
        )

    async def call_sonnet_final_decision(
        self,
        system_prompt: str,
        incident_alert: Dict[str, Any],
        evidence_history: List[Dict[str, Any]],
        jev_recommendation: Optional[JevDecision] = None,
    ) -> ProviderResponse:
        start_mono = time.monotonic()
        alert_str = json.dumps(incident_alert)
        ev_str = json.dumps(evidence_history)

        # Derive accurate synthesized diagnosis from observed evidence
        if "OOM" in ev_str or "137" in ev_str:
            root = "Container memory limit exceeded (OOMKilled exit code 137)."
            act = "adjust_resources"
            req_act = True
            esc = False
            inc_cls = "Resource Exhaustion"
        elif "ErrImagePull" in ev_str or "ImagePullBackOff" in ev_str:
            root = "Non-existent container image tag in recent release."
            act = "rollback_deployment"
            req_act = True
            esc = False
            inc_cls = "Deployment Failure"
        elif "PAYMENT_GATEWAY_URL" in ev_str or "ConfigMap" in ev_str:
            root = "Missing mandatory configuration key 'PAYMENT_GATEWAY_URL' in ConfigMap."
            act = "escalate"
            req_act = False
            esc = True
            inc_cls = "Configuration"
        elif "auto-healed" in ev_str or "Auto-Recovered" in alert_str or "Stale" in alert_str:
            root = "Incident previously auto-healed via rollback; alerts are stale."
            act = "none_required"
            req_act = False
            esc = False
            inc_cls = "Temporal Race"
        elif "exclusive lock" in ev_str or "table lock" in ev_str:
            root = "PostgreSQL exclusive lock contention on transactions table from migration."
            act = "escalate"
            req_act = False
            esc = True
            inc_cls = "Database Lock Contention"
        else:
            root = "Degraded operational state requiring manual operator intervention."
            act = "escalate"
            req_act = False
            esc = True
            inc_cls = "System Degradation"

        sonnet_dec = SonnetDecision(
            incident_class=inc_cls,
            root_cause=root,
            severity=4 if esc else 3,
            recommended_action=act,
            requires_action=req_act,
            should_escalate=esc,
            confidence=0.92,
            brief_rationale=f"Diagnosed based on accumulated evidence across {len(evidence_history)} diagnostic events.",
        )

        end_mono = time.monotonic()
        latency_ms = 780.0
        inp_tokens = 2200 + (len(evidence_history) * 350)
        out_tokens = 220
        est_cost = self.calculate_cost(inp_tokens, out_tokens, is_jev=False)

        return ProviderResponse(
            status_code=200,
            monotonic_latency_ms=latency_ms,
            request_start_ms=start_mono * 1000,
            request_end_ms=end_mono * 1000,
            model=self.model_id,
            provider=self.provider_name,
            routed_provider=f"{self.provider_name}-direct",
            input_tokens=inp_tokens,
            output_tokens=out_tokens,
            reasoning_tokens=140,
            estimated_cost_usd=est_cost,
            cost_source="estimated",
            sonnet_decision=sonnet_dec,
            raw_payload=sonnet_dec.model_dump_json(),
        )

    async def smoke_test(self) -> bool:
        return True
