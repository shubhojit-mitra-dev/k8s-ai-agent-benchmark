"""
Autonomous agent architectures package.
"""

from typing import Optional
from backend.agents.base import BaseAgent, BASELINE_SYSTEM_PROMPT, HYBRID_SONNET_PROMPT
from backend.agents.baseline_sonnet import BaselineSonnetAgent
from backend.agents.hybrid_jev_sonnet import HybridJevSonnetAgent
from backend.agents.secondary import JevOnlyAblationAgent, JevShadowAgent
from backend.config import BenchmarkSettings
from backend.models.schema import PrimaryArm, SecondaryExperiment
from backend.providers import get_providers_for_arm
from backend.simulator.cluster import KubernetesSimulator

__all__ = [
    "BaseAgent",
    "BASELINE_SYSTEM_PROMPT",
    "HYBRID_SONNET_PROMPT",
    "BaselineSonnetAgent",
    "HybridJevSonnetAgent",
    "JevOnlyAblationAgent",
    "JevShadowAgent",
    "create_agent_for_arm",
]


def create_agent_for_arm(
    run_id: str,
    arm: PrimaryArm | str,
    incident_id: str,
    difficulty: int,
    simulator: KubernetesSimulator,
    settings: BenchmarkSettings,
    confidence_threshold: float = 0.70,
    force_mock: bool = False,
    max_steps: int = 20,
    timeout_seconds: float = 120.0,
) -> BaseAgent:
    """Factory creating the appropriate autonomous agent architecture for the specified arm."""
    arm_str = arm.value if isinstance(arm, PrimaryArm) else str(arm)
    sonnet_prov, jev_prov = get_providers_for_arm(arm_str, settings, force_mock=force_mock)

    if "JEV" in arm_str and jev_prov is not None:
        return HybridJevSonnetAgent(
            run_id=run_id,
            arm_name=arm_str,
            incident_id=incident_id,
            difficulty=difficulty,
            simulator=simulator,
            sonnet_provider=sonnet_prov,
            jev_provider=jev_prov,
            confidence_threshold=confidence_threshold,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
        )
    else:
        return BaselineSonnetAgent(
            run_id=run_id,
            arm_name=arm_str,
            incident_id=incident_id,
            difficulty=difficulty,
            simulator=simulator,
            provider=sonnet_prov,
            max_steps=max_steps,
            timeout_seconds=timeout_seconds,
        )
