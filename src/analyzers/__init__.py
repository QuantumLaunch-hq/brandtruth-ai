# src/analyzers/__init__.py
"""Ad analyzers for BrandTruth AI."""

from .performance_predictor import (
    PerformancePredictor,
    MockPerformancePredictor,
    PerformancePrediction,
    AdToAnalyze,
    ComponentScore,
    Improvement,
    ABTestSuggestion,
    PerformanceTier,
    CTRPrediction,
    ImprovementPriority,
    get_predictor,
)

from .attention_analyzer import (
    AttentionAnalyzer,
    MockAttentionAnalyzer,
    AttentionAnalysis,
    AttentionPoint,
    VisualFlowStep,
    AttentionLevel,
    ElementType,
    HeatmapConfig,
    get_attention_analyzer,
)

from .fatigue_predictor import (
    FatiguePredictor,
    MockFatiguePredictor,
    FatiguePrediction,
    AdPerformanceData,
    FatigueLevel,
    RefreshUrgency,
    DecayPattern,
    FatigueConfig,
    get_fatigue_predictor,
)

from .competitor_intel import (
    CompetitorIntelAnalyzer,
    CompetitorAnalysis,
    CompetitorProfile,
    CompetitorAd,
    CompetitorInsight,
    CopyPattern,
    VisualStrategy,
    CompetitorThreat,
    AdCategory,
    CompetitorIntelConfig,
    get_competitor_intel_analyzer,
)

__all__ = [
    # Performance Predictor
    "PerformancePredictor",
    "MockPerformancePredictor",
    "PerformancePrediction",
    "AdToAnalyze",
    "ComponentScore",
    "Improvement",
    "ABTestSuggestion",
    "PerformanceTier",
    "CTRPrediction",
    "ImprovementPriority",
    "get_predictor",
    # Attention Analyzer
    "AttentionAnalyzer",
    "MockAttentionAnalyzer",
    "AttentionAnalysis",
    "AttentionPoint",
    "VisualFlowStep",
    "AttentionLevel",
    "ElementType",
    "HeatmapConfig",
    "get_attention_analyzer",
    # Fatigue Predictor
    "FatiguePredictor",
    "MockFatiguePredictor",
    "FatiguePrediction",
    "AdPerformanceData",
    "FatigueLevel",
    "RefreshUrgency",
    "DecayPattern",
    "FatigueConfig",
    "get_fatigue_predictor",
    # Competitor Intel
    "CompetitorIntelAnalyzer",
    "CompetitorAnalysis",
    "CompetitorProfile",
    "CompetitorAd",
    "CompetitorInsight",
    "CopyPattern",
    "VisualStrategy",
    "CompetitorThreat",
    "AdCategory",
    "CompetitorIntelConfig",
    "get_competitor_intel_analyzer",
]
