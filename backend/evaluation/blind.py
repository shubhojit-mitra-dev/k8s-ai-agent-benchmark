"""
Blinded Evaluation Framework.
Anonymizes experiment arms during scoring to eliminate evaluator bias.
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple
from backend.models.schema import PrimaryArm, Trajectory


class BlindedEvaluatorContext:
    """
    Anonymizes real experiment arm identifiers (e.g. CF-JEV-SONNET) to neutral tokens
    (ARM-A, ARM-B, ARM-C, ARM-D) prior to scoring, and unblinds them strictly post-evaluation.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self.seed = seed
        self.arm_to_blind_map: Dict[str, str] = {}
        self.blind_to_arm_map: Dict[str, str] = {}
        self._initialize_blind_mapping()

    def _initialize_blind_mapping(self) -> None:
        primary_arms = [
            PrimaryArm.CF_SONNET.value,
            PrimaryArm.CF_JEV_SONNET.value,
            PrimaryArm.OR_SONNET.value,
            PrimaryArm.OR_JEV_SONNET.value,
        ]
        rng = random.Random(self.seed)
        shuffled = list(primary_arms)
        rng.shuffle(shuffled)

        blind_labels = ["ARM-A", "ARM-B", "ARM-C", "ARM-D"]
        for arm_name, blind_id in zip(shuffled, blind_labels):
            self.arm_to_blind_map[arm_name] = blind_id
            self.blind_to_arm_map[blind_id] = arm_name

    def blind_trajectory(self, trajectory: Trajectory) -> Trajectory:
        """Returns a copy of the trajectory with arm name anonymized to blind ID."""
        blind_id = self.arm_to_blind_map.get(trajectory.arm, trajectory.arm)
        blinded = trajectory.model_copy(deep=True)
        blinded.arm = blind_id
        return blinded

    def unblind_arm_id(self, blind_id: str) -> str:
        """Restores the true arm name after scoring is finalized."""
        return self.blind_to_arm_map.get(blind_id, blind_id)
