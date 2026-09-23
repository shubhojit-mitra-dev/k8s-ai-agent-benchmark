"""
Evaluation, metrics, statistical aggregation, and hypothesis testing package.
"""

from backend.evaluation.blind import BlindedEvaluatorContext
from backend.evaluation.evaluator import TrajectoryEvaluator
from backend.evaluation.metrics import (
    BenchmarkAggregateMetrics,
    ArmSummaryMetrics,
    DifficultyBandMetrics,
    PercentileStats,
    aggregate_benchmark_results,
    calculate_percentiles,
)
from backend.evaluation.hypothesis import (
    HypothesisEvaluator,
    HypothesisAnalysisReport,
    HypothesisTestResult,
    ThresholdSweepPoint,
    ConfidenceMatrix,
    CostScaleProjection,
)

__all__ = [
    "BlindedEvaluatorContext",
    "TrajectoryEvaluator",
    "BenchmarkAggregateMetrics",
    "ArmSummaryMetrics",
    "DifficultyBandMetrics",
    "PercentileStats",
    "aggregate_benchmark_results",
    "calculate_percentiles",
    "HypothesisEvaluator",
    "HypothesisAnalysisReport",
    "HypothesisTestResult",
    "ThresholdSweepPoint",
    "ConfidenceMatrix",
    "CostScaleProjection",
]
