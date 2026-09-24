"""
Benchmark Metrics and Statistical Aggregation Engine.
Computes P50, P90, P95, P99, means, standard deviations, and multi-dimensional
trade-off vectors across experiment arms.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from backend.models.schema import EvaluationResult


class PercentileStats(BaseModel):
    mean: float = 0.0
    std_dev: float = 0.0
    p50: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


def calculate_percentiles(values: List[float]) -> PercentileStats:
    if not values:
        return PercentileStats()
    arr = np.array(values, dtype=float)
    return PercentileStats(
        mean=float(np.mean(arr)),
        std_dev=float(np.std(arr)),
        p50=float(np.percentile(arr, 50)),
        p90=float(np.percentile(arr, 90)),
        p95=float(np.percentile(arr, 95)),
        p99=float(np.percentile(arr, 99)),
    )


class ArmSummaryMetrics(BaseModel):
    arm: str
    trajectories_count: int = 0
    safe_resolution_rate: float = 0.0
    resolution_rate: float = 0.0
    unsafe_action_rate: float = 0.0
    root_cause_accuracy: float = 0.0
    action_accuracy: float = 0.0
    escalation_accuracy: float = 0.0
    severity_accuracy: float = 0.0
    
    latency_total_ms: PercentileStats = Field(default_factory=PercentileStats)
    latency_ai_ms: PercentileStats = Field(default_factory=PercentileStats)
    latency_tool_ms: PercentileStats = Field(default_factory=PercentileStats)
    time_to_final_decision_ms: PercentileStats = Field(default_factory=PercentileStats)
    time_to_resolution_ms: PercentileStats = Field(default_factory=PercentileStats)
    
    total_tokens: PercentileStats = Field(default_factory=PercentileStats)
    sonnet_input_tokens: PercentileStats = Field(default_factory=PercentileStats)
    sonnet_output_tokens: PercentileStats = Field(default_factory=PercentileStats)
    jev_tokens: PercentileStats = Field(default_factory=PercentileStats)
    
    cost_usd: PercentileStats = Field(default_factory=PercentileStats)
    cost_per_safe_resolution: float = 0.0
    
    tool_calls_mean: float = 0.0
    useful_tool_calls_mean: float = 0.0
    redundant_tool_calls_mean: float = 0.0
    sonnet_calls_mean: float = 0.0
    jev_calls_mean: float = 0.0


class DifficultyBandMetrics(BaseModel):
    difficulty_band: str  # "1-4", "5-8", "9-12", "13-16", "17-20"
    arm: str
    safe_resolution_rate: float = 0.0
    resolution_rate: float = 0.0
    unsafe_action_rate: float = 0.0
    median_latency_ms: float = 0.0
    mean_cost_usd: float = 0.0


class BenchmarkAggregateMetrics(BaseModel):
    arm_metrics: Dict[str, ArmSummaryMetrics] = Field(default_factory=dict)
    difficulty_breakdown: List[DifficultyBandMetrics] = Field(default_factory=list)
    super_max_incidents: List[EvaluationResult] = Field(default_factory=list)


def aggregate_benchmark_results(results: List[EvaluationResult]) -> BenchmarkAggregateMetrics:
    """Aggregates an array of incident evaluation results into statistical summaries per arm."""
    by_arm: Dict[str, List[EvaluationResult]] = {}
    for r in results:
        by_arm.setdefault(r.arm, []).append(r)

    arm_metrics: Dict[str, ArmSummaryMetrics] = {}
    for arm_name, arm_results in by_arm.items():
        n = len(arm_results)
        if n == 0:
            continue

        safe_res = sum(1 for r in arm_results if r.safe_correct_resolution) / n
        res_rate = sum(1 for r in arm_results if r.resolved) / n
        unsafe_rate = sum(1 for r in arm_results if not r.safe) / n
        rc_acc = sum(1 for r in arm_results if r.root_cause_correct) / n
        act_acc = sum(1 for r in arm_results if r.recommended_action_correct) / n
        esc_acc = sum(1 for r in arm_results if r.escalation_correct) / n
        sev_acc = sum(1 for r in arm_results if r.severity_correct) / n

        tot_lat = [r.trajectory.latency.total_latency_ms for r in arm_results]
        ai_lat = [r.trajectory.latency.ai_latency_ms for r in arm_results]
        tool_lat = [r.trajectory.latency.tool_latency_ms for r in arm_results]
        final_dec_lat = [r.trajectory.latency.time_to_final_decision_ms or 0.0 for r in arm_results]
        res_lat = [r.trajectory.latency.time_to_resolution_ms or 0.0 for r in arm_results if r.trajectory.latency.time_to_resolution_ms]

        tok_tot = [r.trajectory.tokens_input + r.trajectory.tokens_output for r in arm_results]
        costs = [r.trajectory.cost.total_cost_usd for r in arm_results]

        safe_count = sum(1 for r in arm_results if r.safe_correct_resolution)
        total_arm_cost = sum(costs)
        cost_per_safe = (total_arm_cost / safe_count) if safe_count > 0 else total_arm_cost

        sonnet_calls = [r.trajectory.sonnet_calls for r in arm_results]
        jev_calls = [r.trajectory.jev_calls for r in arm_results]
        tool_calls = [r.trajectory.tool_calls for r in arm_results]
        useful_tools = [r.trajectory.useful_tool_calls for r in arm_results]
        redundant_tools = [r.trajectory.redundant_tool_calls for r in arm_results]

        arm_metrics[arm_name] = ArmSummaryMetrics(
            arm=arm_name,
            trajectories_count=n,
            safe_resolution_rate=round(safe_res, 4),
            resolution_rate=round(res_rate, 4),
            unsafe_action_rate=round(unsafe_rate, 4),
            root_cause_accuracy=round(rc_acc, 4),
            action_accuracy=round(act_acc, 4),
            escalation_accuracy=round(esc_acc, 4),
            severity_accuracy=round(sev_acc, 4),
            latency_total_ms=calculate_percentiles(tot_lat),
            latency_ai_ms=calculate_percentiles(ai_lat),
            latency_tool_ms=calculate_percentiles(tool_lat),
            time_to_final_decision_ms=calculate_percentiles(final_dec_lat),
            time_to_resolution_ms=calculate_percentiles(res_lat),
            total_tokens=calculate_percentiles(tok_tot),
            cost_usd=calculate_percentiles(costs),
            cost_per_safe_resolution=round(cost_per_safe, 4),
            tool_calls_mean=round(float(np.mean(tool_calls)), 2) if tool_calls else 0.0,
            useful_tool_calls_mean=round(float(np.mean(useful_tools)), 2) if useful_tools else 0.0,
            redundant_tool_calls_mean=round(float(np.mean(redundant_tools)), 2) if redundant_tools else 0.0,
            sonnet_calls_mean=round(float(np.mean(sonnet_calls)), 2) if sonnet_calls else 0.0,
            jev_calls_mean=round(float(np.mean(jev_calls)), 2) if jev_calls else 0.0,
        )

    # Difficulty breakdown
    bands = [("1-4", 1, 4), ("5-8", 5, 8), ("9-12", 9, 12), ("13-16", 13, 16), ("17-20", 17, 20)]
    diff_metrics: List[DifficultyBandMetrics] = []
    for band_name, low, high in bands:
        for arm_name, arm_results in by_arm.items():
            band_res = [r for r in arm_results if low <= r.difficulty <= high]
            if not band_res:
                continue
            m_n = len(band_res)
            s_rate = sum(1 for r in band_res if r.safe_correct_resolution) / m_n
            r_rate = sum(1 for r in band_res if r.resolved) / m_n
            u_rate = sum(1 for r in band_res if not r.safe) / m_n
            lats = [r.trajectory.latency.total_latency_ms for r in band_res]
            csts = [r.trajectory.cost.total_cost_usd for r in band_res]
            diff_metrics.append(
                DifficultyBandMetrics(
                    difficulty_band=band_name,
                    arm=arm_name,
                    safe_resolution_rate=round(s_rate, 4),
                    resolution_rate=round(r_rate, 4),
                    unsafe_action_rate=round(u_rate, 4),
                    median_latency_ms=round(float(np.median(lats)), 1) if lats else 0.0,
                    mean_cost_usd=round(float(np.mean(csts)), 4) if csts else 0.0,
                )
            )

    # Super-Max subset
    super_max = [r for r in results if r.incident_id in {"K8S-017", "K8S-018", "K8S-019", "K8S-020"}]

    return BenchmarkAggregateMetrics(
        arm_metrics=arm_metrics,
        difficulty_breakdown=diff_metrics,
        super_max_incidents=super_max,
    )
