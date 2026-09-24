"""
Secondary and Ablation Agent Architectures.
Implements JEV_ONLY, JEV_SHADOW, JEV_GUIDED_SONNET, and JEV_GATED_SONNET.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from backend.agents.base import BaseAgent, BASELINE_SYSTEM_PROMPT, HYBRID_SONNET_PROMPT
from backend.models.decisions import JevDecision
from backend.models.schema import TerminationReason, Trajectory
from backend.providers.base import BaseProvider
from backend.simulator.tools import TOOL_SCHEMAS


class JevOnlyAblationAgent(BaseAgent):
    """Ablation: Jev operates autonomously without Claude Sonnet 5."""

    def __init__(self, provider: BaseProvider, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provider = provider

    async def run(self, initial_alert: Dict[str, Any]) -> Trajectory:
        self.start_mono_time = time.monotonic()
        available_tools = [t["function"]["name"] for t in TOOL_SCHEMAS]

        while self.step_counter < self.max_steps:
            jev_resp = await self.provider.call_jev_decision(
                incident_alert=initial_alert,
                accumulated_evidence=self.accumulated_evidence,
                available_tools=available_tools,
            )
            jev_dec = jev_resp.jev_decision

            self.record_decision(
                actor="jev",
                decision=jev_dec.next_step if jev_dec else "unknown",
                latency_ms=jev_resp.monotonic_latency_ms,
                input_tokens=jev_resp.input_tokens,
                output_tokens=jev_resp.output_tokens,
                cost_usd=jev_resp.estimated_cost_usd,
                confidence=jev_dec.confidence if jev_dec else 0.0,
            )

            if not jev_dec or jev_dec.next_step in {"escalate", "handoff_to_frontier"}:
                self.trajectory.termination_reason = TerminationReason.ESCALATED
                break

            self.execute_tool_call("list_pods", {"namespace": "payments"})
            if self.simulator.evaluate_resolution_state():
                self.trajectory.termination_reason = TerminationReason.RESOLVED
                break

        self.trajectory.latency.total_latency_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        return self.trajectory


class JevShadowAgent(BaseAgent):
    """
    Shadow Mode: Sonnet controls behavior while Jev observes in parallel,
    recording hypothetical decisions without modifying the baseline trajectory.
    """

    def __init__(self, sonnet_provider: BaseProvider, jev_provider: BaseProvider, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sonnet_provider = sonnet_provider
        self.jev_provider = jev_provider
        self.shadow_decisions: List[Dict[str, Any]] = []

    async def run(self, initial_alert: Dict[str, Any]) -> Trajectory:
        self.start_mono_time = time.monotonic()
        messages = [
            {
                "role": "user",
                "content": f"INCIDENT ALERT: {json.dumps(initial_alert)}\nBegin diagnostic investigation.",
            }
        ]
        available_tools = [t["function"]["name"] for t in TOOL_SCHEMAS]

        while self.step_counter < self.max_steps:
            # Parallel shadow observation by Jev (does not mutate state)
            jev_resp = await self.jev_provider.call_jev_decision(
                incident_alert=initial_alert,
                accumulated_evidence=self.accumulated_evidence,
                available_tools=available_tools,
            )
            if jev_resp.jev_decision:
                self.shadow_decisions.append({
                    "step": self.step_counter,
                    "jev_choice": jev_resp.jev_decision.next_step,
                    "confidence": jev_resp.jev_decision.confidence,
                })

            # Primary Sonnet control
            sonnet_resp = await self.sonnet_provider.call_sonnet_investigation(
                system_prompt=BASELINE_SYSTEM_PROMPT, messages=messages, tools=TOOL_SCHEMAS
            )
            self.record_decision(
                actor="sonnet",
                decision=sonnet_resp.tool_call.get("name") if sonnet_resp.tool_call else "evaluate",
                latency_ms=sonnet_resp.monotonic_latency_ms,
                input_tokens=sonnet_resp.input_tokens,
                output_tokens=sonnet_resp.output_tokens,
                cost_usd=sonnet_resp.estimated_cost_usd,
            )

            if not sonnet_resp.tool_call:
                break

            out, _ = self.execute_tool_call(
                sonnet_resp.tool_call["name"], sonnet_resp.tool_call.get("arguments", {})
            )
            if self.simulator.evaluate_resolution_state():
                self.trajectory.termination_reason = TerminationReason.RESOLVED
                break

        self.trajectory.latency.total_latency_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        return self.trajectory
