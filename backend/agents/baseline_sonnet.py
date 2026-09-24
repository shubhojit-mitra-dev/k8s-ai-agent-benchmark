"""
Baseline Claude Sonnet 5 Autonomous Kubernetes Agent.
Implements the monolithic frontier agent loop using direct tool-calling without Jev.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List
from backend.agents.base import BaseAgent, BASELINE_SYSTEM_PROMPT
from backend.models.schema import TerminationReason, Trajectory
from backend.providers.base import BaseProvider
from backend.simulator.tools import TOOL_SCHEMAS


class BaselineSonnetAgent(BaseAgent):
    """
    Standard single-model autonomous architecture.
    Claude Sonnet 5 handles diagnostic tool selection, output analysis,
    hypothesis updates, and final remediation or escalation.
    """

    def __init__(self, provider: BaseProvider, **kwargs) -> None:
        super().__init__(**kwargs)
        self.provider = provider

    async def run(self, initial_alert: Dict[str, Any]) -> Trajectory:
        self.start_mono_time = time.monotonic()
        messages: List[Dict[str, Any]] = [
            {
                "role": "user",
                "content": f"INCIDENT ALERT: {json.dumps(initial_alert)}\nBegin diagnostic investigation using the provided tools.",
            }
        ]

        while self.step_counter < self.max_steps:
            elapsed_sec = time.monotonic() - self.start_mono_time
            if elapsed_sec > self.timeout_seconds:
                self.trajectory.termination_reason = TerminationReason.WALL_CLOCK_EXCEEDED
                break

            # 1. Ask Sonnet for next investigation action
            resp = await self.provider.call_sonnet_investigation(
                system_prompt=BASELINE_SYSTEM_PROMPT,
                messages=messages,
                tools=TOOL_SCHEMAS,
            )

            # Record model call decision
            self.record_decision(
                actor="sonnet",
                decision=resp.tool_call.get("name") if resp.tool_call else "evaluate_state",
                latency_ms=resp.monotonic_latency_ms,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                reasoning_tokens=resp.reasoning_tokens,
                cost_usd=resp.estimated_cost_usd,
                payload={"raw_response": resp.raw_payload},
            )

            if resp.status_code != 200:
                self.trajectory.termination_reason = TerminationReason.PROVIDER_FAILURE
                break

            if not resp.tool_call:
                # Sonnet completed investigation; request final decision
                break

            tool_name = resp.tool_call["name"]
            tool_args = resp.tool_call.get("arguments", {})

            # 2. Execute tool in simulator
            output_text, tool_event = self.execute_tool_call(tool_name, tool_args)

            # Check safety violation
            if self.simulator.unsafe_action_occurred:
                self.trajectory.termination_reason = TerminationReason.UNSAFE_ACTION_PROHIBITED
                break

            # Check resolution
            if self.simulator.evaluate_resolution_state():
                self.trajectory.termination_reason = TerminationReason.RESOLVED
                now_ms = (time.monotonic() - self.start_mono_time) * 1000.0
                self.trajectory.latency.time_to_resolution_ms = now_ms
                break

            # Feed observation back to Sonnet context
            messages.append({
                "role": "assistant",
                "tool_calls": [{
                    "id": f"call_{self.step_counter}",
                    "type": "function",
                    "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": f"call_{self.step_counter}",
                "content": output_text,
            })

        # Request final structured decision from Sonnet
        final_resp = await self.provider.call_sonnet_final_decision(
            system_prompt=BASELINE_SYSTEM_PROMPT,
            incident_alert=initial_alert,
            evidence_history=self.accumulated_evidence,
        )
        now_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        self.trajectory.latency.time_to_final_decision_ms = now_ms

        self.record_decision(
            actor="sonnet",
            decision="final_synthesis",
            latency_ms=final_resp.monotonic_latency_ms,
            input_tokens=final_resp.input_tokens,
            output_tokens=final_resp.output_tokens,
            reasoning_tokens=final_resp.reasoning_tokens,
            cost_usd=final_resp.estimated_cost_usd,
            payload={"sonnet_decision": final_resp.sonnet_decision.model_dump() if final_resp.sonnet_decision else {}},
        )

        if final_resp.sonnet_decision:
            if final_resp.sonnet_decision.should_escalate:
                self.trajectory.termination_reason = TerminationReason.ESCALATED
            elif self.simulator.evaluate_resolution_state():
                self.trajectory.termination_reason = TerminationReason.RESOLVED

        total_elapsed_ms = (time.monotonic() - self.start_mono_time) * 1000.0
        simulated_total_ms = self.trajectory.latency.ai_latency_ms + self.trajectory.latency.tool_latency_ms
        self.trajectory.latency.total_latency_ms = max(total_elapsed_ms, simulated_total_ms)
        self.trajectory.latency.model_latency_ms = self.trajectory.latency.ai_latency_ms
        return self.trajectory
