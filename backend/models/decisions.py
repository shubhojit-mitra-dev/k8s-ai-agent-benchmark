"""
Decision schemas for Jev structured calls and Claude Sonnet 5 frontier reasoning.
Strictly validated data contracts for autonomous agent decisions.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class JevChoiceOption(BaseModel):
    name: str
    probability: float
    description: Optional[str] = None


class JevDecision(BaseModel):
    """
    Consolidated decision object returned by the Jev fast decision controller.
    Covers the 4 questions: next_step choice, intervention probability,
    severity score, and escalation probability.
    """
    next_step: str
    selected_probability: float = 0.0
    second_highest_probability: float = 0.0
    margin: float = 0.0
    confidence: float = 0.0
    choices: List[JevChoiceOption] = Field(default_factory=list)
    
    # Question 2: Intervention justified (Noul probability)
    intervention_probability: float = 0.0
    
    # Question 3: Severity (Score 1-5)
    severity_score: int = 1
    
    # Question 4: Escalation justified (Noul probability)
    escalation_probability: float = 0.0
    
    raw_response: Optional[Dict[str, float]] = None


class SonnetDecision(BaseModel):
    """
    Structured final incident decision produced by Claude Sonnet 5.
    Must adhere strictly to section 40 of benchmark specification.
    """
    incident_class: str
    root_cause: str
    severity: int = Field(ge=1, le=5)
    recommended_action: str
    requires_action: bool
    should_escalate: bool
    confidence: float = Field(ge=0.0, le=1.0)
    brief_rationale: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Severity must be an integer between 1 and 5.")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be a float between 0.0 and 1.0.")
        return v
