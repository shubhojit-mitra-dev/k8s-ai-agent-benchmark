"""
Core schema definitions for the Kubernetes AI Agent Benchmark.
Enforces type safety and reproducible data contracts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionRisk(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PrimaryArm(str, Enum):
    CF_SONNET = "CF-SONNET"
    CF_JEV_SONNET = "CF-JEV-SONNET"
    OR_SONNET = "OR-SONNET"
    OR_JEV_SONNET = "OR-JEV-SONNET"


class SecondaryExperiment(str, Enum):
    JEV_ONLY = "JEV_ONLY"
    SONNET_ONLY = "SONNET_ONLY"
    JEV_SHADOW = "JEV_SHADOW"
    JEV_GUIDED_SONNET = "JEV_GUIDED_SONNET"
    JEV_GATED_SONNET = "JEV_GATED_SONNET"


class TerminationReason(str, Enum):
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    UNSAFE_ACTION_PROHIBITED = "UNSAFE_ACTION_PROHIBITED"
    MAX_STEPS_EXCEEDED = "MAX_STEPS_EXCEEDED"
    WALL_CLOCK_EXCEEDED = "WALL_CLOCK_EXCEEDED"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"


class ToolCallClassification(str, Enum):
    USEFUL = "useful"
    NEUTRAL = "neutral"
    REDUNDANT = "redundant"
    MISLEADING = "misleading"
    UNSAFE = "unsafe"


class InformationGain(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionEvent(BaseModel):
    step: int
    monotonic_ms: float
    actor: str  # "jev" or "sonnet"
    decision: str
    selected_probability: Optional[float] = None
    second_highest_probability: Optional[float] = None
    margin: Optional[float] = None
    confidence: Optional[float] = None
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    payload: Optional[Dict[str, Any]] = None


class ToolEvent(BaseModel):
    step: int
    monotonic_ms: float
    actor: str = "tool"
    tool: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    tool_output: str
    latency_ms: float
    risk_level: ActionRisk = ActionRisk.READ_ONLY
    information_gain: InformationGain = InformationGain.LOW
    classification: ToolCallClassification = ToolCallClassification.NEUTRAL
    evidence_id: str
    content_hash: str
    is_state_mutating: bool = False
    mutation_success: Optional[bool] = None


class CostResult(BaseModel):
    provider_reported_cost: float = 0.0
    estimated_cost: float = 0.0
    cost_source: str = "estimated"
    total_cost_usd: float = 0.0


class LatencyResult(BaseModel):
    model_latency_ms: float = 0.0
    ai_latency_ms: float = 0.0
    tool_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    time_to_first_decision_ms: Optional[float] = None
    time_to_root_cause_ms: Optional[float] = None
    time_to_final_decision_ms: Optional[float] = None
    time_to_resolution_ms: Optional[float] = None


class ProviderResult(BaseModel):
    status_code: int
    request_start_ms: float
    request_end_ms: float
    latency_ms: float
    model: str
    provider: str
    routed_provider: Optional[str] = None
    routing_mode: Optional[str] = None
    usage: Dict[str, int] = Field(default_factory=dict)
    cost_usd: float = 0.0
    retries: int = 0
    raw_response: Optional[str] = None


class Trajectory(BaseModel):
    run_id: str
    incident_id: str
    arm: str
    difficulty: int
    events: List[Any] = Field(default_factory=list)
    total_steps: int = 0
    tool_calls: int = 0
    useful_tool_calls: int = 0
    redundant_tool_calls: int = 0
    wrong_branch_tool_calls: int = 0
    high_information_tool_calls: int = 0
    jev_calls: int = 0
    sonnet_calls: int = 0
    latency: LatencyResult = Field(default_factory=LatencyResult)
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_reasoning: int = 0
    cost: CostResult = Field(default_factory=CostResult)
    termination_reason: TerminationReason = TerminationReason.MAX_STEPS_EXCEEDED
    unsafe_action_detected: bool = False
    unsafe_actions_taken: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    incident_id: str
    arm: str
    difficulty: int
    resolved: bool = False
    safe: bool = False
    safe_correct_resolution: bool = False
    final_decision_correct: bool = False
    root_cause_correct: bool = False
    recommended_action_correct: bool = False
    severity_correct: bool = False
    escalation_correct: bool = False
    correct_escalation: bool = False
    premature_escalation: bool = False
    missed_escalation: bool = False
    wrong_turn_count: int = 0
    recoverable_error: bool = False
    irrecoverable_error: bool = False
    trajectory: Trajectory


class IncidentResult(BaseModel):
    evaluation: EvaluationResult


class ScenarioMetadata(BaseModel):
    id: str
    title: str
    difficulty: int
    category: str
    initial_alert: Dict[str, Any]
    hidden_root_cause: str
    hidden_secondary_effects: List[str]
    valid_investigation_paths: List[List[str]]
    unsafe_actions: List[str]
    correct_resolution_conditions: Dict[str, Any]
    ground_truth_rationale: str
    expected_tool_sequences: List[List[str]]
    allowed_alternative_paths: List[List[str]]
    initial_state_sha256: str = ""
