"""
Hybrid Jev + Claude Sonnet 5 Autonomous Kubernetes Agent.
Implements the fast decision controller layer using Jev for routine diagnostic
tool selection and gating, delegating complex synthesis to Claude Sonnet 5.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from backend.agents.base import BaseAgent, HYBRID_SONNET_PROMPT
from backend.models.decisions import JevDecision
from backend.models.schema import TerminationReason, Trajectory
from backend.providers.base import BaseProvider
from backend.simulator.tools import TOOL_SCHEMAS


# Mapping of Jev choice decisions to concrete Kubernetes diagnostic tools
JEV_CHOICE_TO_TOOL = {
    "inspect_pod": "list_pods",
    "inspect_logs": "get_pod_logs",
    "inspect_events": "get_events",
    "inspect_node": "get_nodes",
    "inspect_deployment": "get_deployment",
    "inspect_service": "get_service",
    "inspect_network": "get_network_policies",
    "inspect_dns": "dns_lookup",
    "inspect_dependency": "get_database_health",
}


class HybridJevSonnetAgent(BaseAgent):
    """
    Two-tier hierarchical architecture.
    Tier 1: Jev acts as a low-latency, low-cost operational router.
    Tier 2: Claude Sonnet 5 acts as frontier reasoning synthesizer upon handoff.
    """

    def __init__(
        self,
        sonnet_provider: BaseProvider,
        jev_provider: BaseProvider,
        confidence_threshold: float = 0.70,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.sonnet_provider = sonnet_provider
        self.jev_provider = jev_provider
        self.confidence_threshold = confidence_threshold

    async def run(self, initial_alert: Dict[str, Any]) -> Trajectory:
        self.start_mono_time = time.monotonic()
        available_tools = [t["function"]["name"] for t in TOOL_SCHEMAS]
        last_jev_decision: Optional[JevDecision] = None
        handoff_triggered: bool = False

        while self.step_counter < self.max_steps:
            elapsed_sec = time.monotonic() - self.start_mono_time
            if elapsed_sec > self.timeout_seconds:
                self.trajectory.termination_reason = TerminationReason.WALL_CLOCK_EXCEEDED
                break

            # 1. Ask Jev for the next operational step
            jev_resp = await self.jev_provider.call_jev_decision(
                incident_alert=initial_alert,
                accumulated_evidence=self.accumulated_evidence,
                available_tools=available_tools,
            )

            jev_dec = jev_resp.jev_decision
            last_jev_decision = jev_dec

            self.record_decision(
                actor="jev",
                decision=jev_dec.next_step if jev_dec else "unknown",
                latency_ms=jev_resp.monotonic_latency_ms,
                input_tokens=jev_resp.input_tokens,
                output_tokens=jev_resp.output_tokens,
                cost_usd=jev_resp.estimated_cost_usd,
                confidence=jev_dec.confidence if jev_dec else 0.0,
                second_highest_prob=jev_dec.second_highest_probability if jev_dec else 0.0,
                margin=jev_dec.margin if jev_dec else 0.0,
                payload=jev_dec.model_dump() if jev_dec else {},
            )

            if jev_resp.status_code != 200 or not jev_dec:
                # If Jev fails, fall back to Sonnet immediately
                handoff_triggered = True
                break

            # Check gating condition: handoff requested OR confidence below threshold
            if (
                jev_dec.next_step in {"handoff_to_frontier", "escalate"}
                or jev_dec.confidence < self.confidence_threshold
                or jev_dec.intervention_probability > 0.50
            ):
                handoff_triggered = True
                break

            # 2. Translate routine Jev choice into tool execution
            target_tool = JEV_CHOICE_TO_TOOL.get(jev_dec.next_step, "get_cluster_state")
            tool_args: Dict[str, Any] = {}
            target_ns = initial_alert.get("namespace", "")
            target_dep = initial_alert.get("deployment", "")
            target_svc = initial_alert.get("service", "")
            target_pod = initial_alert.get("pod", "")

            if not target_pod:
                # Resolve candidate pod from simulator state matching namespace or deployment
                for p in self.simulator.state.pods.values():
                    if (target_ns and p.namespace == target_ns) or (target_dep and target_dep in p.name):
                        target_pod = p.name
                        break
                if not target_pod and self.simulator.state.pods:
                    target_pod = next(iter(self.simulator.state.pods.keys()))

            if target_tool in {"list_pods", "get_deployment", "get_service", "get_pod_logs"}:
                if target_ns:
                    tool_args["namespace"] = target_ns
                if target_tool == "get_deployment" and target_dep:
                    tool_args["deployment_name"] = target_dep
                elif target_tool == "get_service" and (target_svc or target_dep):
                    tool_args["service_name"] = target_svc or target_dep
                elif target_tool == "get_pod_logs" and target_pod:
                    tool_args["pod_name"] = target_pod

            # Execute tool in simulator
            output_text, tool_event = self.execute_tool_call(target_tool, tool_args)

            # Check safety violation
            if self.simulator.unsafe_action_occurred:
                self.trajectory.termination_reason = TerminationReason.UNSAFE_ACTION_PROHIBITED
                break

            # Check if simulator recovered
            if self.simulator.evaluate_resolution_state():
                self.trajectory.termination_reason = TerminationReason.RESOLVED
                now_ms = (time.monotonic() - self.start_mono_time) * 1000.0
                self.trajectory.latency.time_to_resolution_ms = now_ms
                break

        # 3. Sonnet Frontier Synthesis (called upon handoff or step completion)
        sonnet_resp = await self.sonnet_provider.call_sonnet_final_decision(
            system_prompt=HYBRID_SONNET_PROMPT,
            incident_alert=initial_alert,
            evidence_history=self.accumulated_evidence,
            jev_recommendation=last_jev_decision,
        )
        now_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        self.trajectory.latency.time_to_final_decision_ms = now_ms

        self.record_decision(
            actor="sonnet",
            decision="final_synthesis",
            latency_ms=sonnet_resp.monotonic_latency_ms,
            input_tokens=sonnet_resp.input_tokens,
            output_tokens=sonnet_resp.output_tokens,
            reasoning_tokens=sonnet_resp.reasoning_tokens,
            cost_usd=sonnet_resp.estimated_cost_usd,
            payload={"sonnet_decision": sonnet_resp.sonnet_decision.model_dump() if sonnet_resp.sonnet_decision else {}},
        )

        # Execute final recommended remediation if required
        if sonnet_resp.sonnet_decision:
            sd = sonnet_resp.sonnet_decision
            if sd.should_escalate:
                self.trajectory.termination_reason = TerminationReason.ESCALATED
            elif sd.requires_action and sd.recommended_action:
                rem_args: Dict[str, Any] = {}
                target_name = initial_alert.get("deployment") or initial_alert.get("service") or initial_alert.get("pod") or ""
                rem_args["target"] = target_name
                rem_args["deployment_name"] = target_name
                if sd.recommended_action == "adjust_resources":
                    rem_args["memory_limit"] = "1024Mi"
                    rem_args["cpu_limit"] = "1000m"
                elif sd.recommended_action == "scale_deployment":
                    rem_args["replicas"] = 3
                elif sd.recommended_action == "restart_pod" and target_name:
                    rem_args["pod_name"] = target_name

                # Execute remediation in simulator
                self.execute_tool_call(
                    sd.recommended_action,
                    rem_args,
                )
                if self.simulator.evaluate_resolution_state():
                    self.trajectory.termination_reason = TerminationReason.RESOLVED
                elif self.simulator.unsafe_action_occurred:
                    self.trajectory.termination_reason = TerminationReason.UNSAFE_ACTION_PROHIBITED

        total_elapsed_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        simulated_total_ms = self.trajectory.latency.ai_latency_ms + self.trajectory.latency.tool_latency_ms
        self.trajectory.latency.total_latency_ms = max(total_elapsed_ms, simulated_total_ms)
        self.trajectory.latency.model_latency_ms = self.trajectory.latency.ai_latency_ms
        return self.trajectory
