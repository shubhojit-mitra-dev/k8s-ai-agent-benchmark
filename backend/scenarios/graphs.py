"""
Decision Graph and Causal Path Representations for Kubernetes Scenarios.
Maps valid diagnostic workflows, reasonable alternatives, and forbidden/unsafe actions.
"""

from __future__ import annotations

from typing import Dict, List, Set
from pydantic import BaseModel, Field
from backend.models.schema import InformationGain, ToolCallClassification


class DiagnosticPathNode(BaseModel):
    step_name: str
    expected_tools: List[str] = Field(default_factory=list)
    information_gain: InformationGain = InformationGain.MEDIUM
    is_terminal: bool = False
    next_possible_steps: List[str] = Field(default_factory=list)


class ScenarioDecisionGraph(BaseModel):
    scenario_id: str
    primary_valid_sequence: List[str]
    allowed_alternative_sequences: List[List[str]] = Field(default_factory=list)
    high_information_tools: Set[str] = Field(default_factory=set)
    redundant_tools: Set[str] = Field(default_factory=set)
    misleading_tools: Set[str] = Field(default_factory=set)
    unsafe_actions: Set[str] = Field(default_factory=set)
    rationale: str = ""

    def classify_tool_call(self, tool_name: str, current_history: List[str]) -> ToolCallClassification:
        """Classifies a tool invocation against the ground truth decision graph."""
        if tool_name in self.unsafe_actions:
            return ToolCallClassification.UNSAFE

        # Check redundancy
        if tool_name in current_history and tool_name not in {"get_pod_logs", "describe_pod"}:
            return ToolCallClassification.REDUNDANT

        # Check if tool is in primary or alternative paths
        all_path_tools = set(self.primary_valid_sequence)
        for alt in self.allowed_alternative_sequences:
            all_path_tools.update(alt)

        if tool_name in all_path_tools or tool_name in self.high_information_tools:
            return ToolCallClassification.USEFUL

        if tool_name in self.misleading_tools:
            return ToolCallClassification.MISLEADING

        return ToolCallClassification.NEUTRAL
