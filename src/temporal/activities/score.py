# src/temporal/activities/score.py
"""Performance scoring activity for Temporal workflow.

This activity wraps the performance_predictor module, providing:
- AI-powered ad scoring
- Batch scoring for multiple variants
- Score persistence for comparison
"""

from dataclasses import dataclass
from temporalio import activity

from src.analyzers.performance_predictor import PerformancePredictor, AdToAnalyze
from src.temporal.activities.generate import CopyVariantResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceScore:
    """Serializable performance score for Temporal."""
    variant_id: str
    score: int  # 0-100
    confidence: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


@dataclass
class PerformanceScoringResult:
    """Result of performance scoring activity."""
    scores: list[PerformanceScore]
    scoring_time_ms: int


@activity.defn
async def predict_performance_activity(
    variants: list[CopyVariantResult],
) -> PerformanceScoringResult:
    """Score ad variants for predicted performance.

    This activity wraps the performance predictor with:
    - AI-powered scoring analysis
    - Batch processing with heartbeats
    - Detailed feedback for each variant

    Args:
        variants: Copy variants to score

    Returns:
        PerformanceScoringResult with scores and feedback

    Raises:
        Exception: On scoring failure (will be retried)
    """
    import time
    start_time = time.time()

    activity.logger.info(f"Scoring {len(variants)} variants")
    activity.heartbeat(f"Starting performance scoring for {len(variants)} variants")

    try:
        predictor = PerformancePredictor()
        scores = []

        for i, variant in enumerate(variants):
            activity.heartbeat(f"Scoring variant {i + 1}/{len(variants)}")

            # Create AdToAnalyze object for predictor
            ad_copy = AdToAnalyze(
                headline=variant.headline,
                primary_text=variant.primary_text,
                cta=variant.cta,
            )

            # Get prediction (async method)
            prediction = await predictor.predict(ad_copy)

            # Extract strengths/weaknesses from component scores
            # ComponentScore has: name, score, analysis, strengths, weaknesses, weight
            strengths = []
            weaknesses = []
            for c in prediction.component_scores:
                if c.score >= 70:
                    strengths.extend(c.strengths[:1])  # Take first strength
                if c.score < 50:
                    weaknesses.extend(c.weaknesses[:1])  # Take first weakness
            recommendations = [imp.suggestion for imp in prediction.improvements[:3]]

            scores.append(
                PerformanceScore(
                    variant_id=variant.id,
                    score=prediction.overall_score,
                    confidence=prediction.confidence,
                    strengths=strengths[:3],
                    weaknesses=weaknesses[:3],
                    recommendations=recommendations,
                )
            )

        result = PerformanceScoringResult(
            scores=scores,
            scoring_time_ms=int((time.time() - start_time) * 1000),
        )

        # Log summary
        avg_score = sum(s.score for s in scores) / len(scores) if scores else 0
        activity.logger.info(
            f"Scored {len(scores)} variants (avg: {avg_score:.0f}) "
            f"in {result.scoring_time_ms}ms"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Performance scoring failed: {e}")
        raise
