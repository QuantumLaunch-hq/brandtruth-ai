# src/analyzers/fatigue_predictor.py
"""Creative Fatigue Predictor for BrandTruth AI - Slice 14

Predicts when ads will experience creative fatigue and need refreshing.

Features:
- Fatigue score prediction (0-100)
- Days until fatigue estimate
- Refresh urgency level
- Performance decay detection
- Recommendation engine
- Historical pattern analysis

Creative Fatigue Indicators:
- Frequency (how often same user sees ad)
- CTR decline over time
- CPM increase
- Engagement drop
- Audience saturation
- Market competition changes
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FatigueLevel(str, Enum):
    """Fatigue urgency levels."""
    FRESH = "fresh"           # 0-20: Ad is performing well
    HEALTHY = "healthy"       # 21-40: Normal wear, monitor
    MODERATE = "moderate"     # 41-60: Starting to fatigue
    HIGH = "high"             # 61-80: Needs refresh soon
    CRITICAL = "critical"     # 81-100: Immediate refresh needed


class RefreshUrgency(str, Enum):
    """How urgently the ad needs refreshing."""
    NONE = "none"             # No action needed
    PLAN = "plan"             # Start planning refresh
    PREPARE = "prepare"       # Prepare new creative
    URGENT = "urgent"         # Refresh within days
    IMMEDIATE = "immediate"   # Refresh now


class DecayPattern(str, Enum):
    """Type of performance decay."""
    NONE = "none"
    GRADUAL = "gradual"       # Slow steady decline
    SUDDEN = "sudden"         # Sharp drop
    CYCLICAL = "cyclical"     # Periodic dips
    PLATEAU = "plateau"       # Flat but not growing


# =============================================================================
# DATA MODELS
# =============================================================================

class AdPerformanceData(BaseModel):
    """Historical performance data for an ad."""
    ad_id: str
    campaign_id: Optional[str] = None
    start_date: datetime
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    frequency: float = 1.0  # Avg times shown per user
    reach: int = 0
    ctr_history: list[float] = Field(default_factory=list)  # Daily CTR values
    cpm_history: list[float] = Field(default_factory=list)  # Daily CPM values
    days_running: int = 0
    audience_size: int = 100000
    industry: str = "general"
    platform: str = "meta"


class FatiguePrediction(BaseModel):
    """Fatigue prediction result."""
    ad_id: str
    fatigue_score: int = Field(ge=0, le=100)
    fatigue_level: FatigueLevel
    days_until_fatigue: int
    refresh_urgency: RefreshUrgency
    
    # Performance indicators
    ctr_decline_percent: float
    cpm_increase_percent: float
    frequency_risk: float  # 0-1
    audience_saturation: float  # 0-1
    
    # Decay analysis
    decay_pattern: DecayPattern
    decay_rate: float  # % per day
    
    # Projections
    projected_ctr_7d: float
    projected_cpm_7d: float
    projected_frequency_7d: float
    
    # Recommendations
    recommendations: list[str]
    refresh_strategies: list[str]
    
    # Timing
    optimal_refresh_date: datetime
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        emoji_map = {
            FatigueLevel.FRESH: "🌱",
            FatigueLevel.HEALTHY: "✅",
            FatigueLevel.MODERATE: "⚠️",
            FatigueLevel.HIGH: "🔶",
            FatigueLevel.CRITICAL: "🔴",
        }
        emoji = emoji_map.get(self.fatigue_level, "❓")
        return f"{emoji} Fatigue: {self.fatigue_score}/100 ({self.fatigue_level.value}) | Refresh in {self.days_until_fatigue} days"


class FatigueConfig(BaseModel):
    """Configuration for fatigue prediction."""
    # Thresholds
    ctr_decline_threshold: float = 0.2  # 20% decline
    cpm_increase_threshold: float = 0.3  # 30% increase
    frequency_warning: float = 2.5  # Times per user
    frequency_critical: float = 4.0
    saturation_threshold: float = 0.7  # 70% of audience
    
    # Industry benchmarks (days until typical fatigue)
    industry_benchmarks: dict[str, int] = Field(default_factory=lambda: {
        "general": 21,
        "ecommerce": 14,
        "saas": 28,
        "finance": 30,
        "entertainment": 10,
        "travel": 18,
        "healthcare": 25,
        "education": 21,
        "real_estate": 30,
        "retail": 12,
    })


# =============================================================================
# FATIGUE PREDICTOR
# =============================================================================

class FatiguePredictor:
    """Predicts creative fatigue for ads."""
    
    def __init__(self, config: Optional[FatigueConfig] = None):
        self.config = config or FatigueConfig()
    
    async def predict(self, data: AdPerformanceData) -> FatiguePrediction:
        """
        Predict fatigue for an ad based on performance data.
        
        Args:
            data: Historical performance data
        
        Returns:
            FatiguePrediction with scores and recommendations
        """
        logger.info(f"Predicting fatigue for ad {data.ad_id}...")
        
        # Calculate individual risk factors
        ctr_decline = self._calculate_ctr_decline(data.ctr_history)
        cpm_increase = self._calculate_cpm_increase(data.cpm_history)
        frequency_risk = self._calculate_frequency_risk(data.frequency)
        saturation = self._calculate_saturation(data.reach, data.audience_size)
        
        # Detect decay pattern
        decay_pattern, decay_rate = self._detect_decay_pattern(data.ctr_history)
        
        # Calculate overall fatigue score
        fatigue_score = self._calculate_fatigue_score(
            ctr_decline=ctr_decline,
            cpm_increase=cpm_increase,
            frequency_risk=frequency_risk,
            saturation=saturation,
            days_running=data.days_running,
            industry=data.industry,
        )
        
        # Determine level and urgency
        fatigue_level = self._get_fatigue_level(fatigue_score)
        refresh_urgency = self._get_refresh_urgency(fatigue_score, decay_pattern)
        
        # Estimate days until critical fatigue
        days_until_fatigue = self._estimate_days_until_fatigue(
            current_score=fatigue_score,
            decay_rate=decay_rate,
            industry=data.industry,
        )
        
        # Make projections
        projected_ctr = self._project_metric(
            current=data.ctr_history[-1] if data.ctr_history else 1.0,
            decay_rate=decay_rate,
            days=7,
        )
        projected_cpm = self._project_cpm(
            current=data.cpm_history[-1] if data.cpm_history else 10.0,
            fatigue_score=fatigue_score,
            days=7,
        )
        projected_frequency = min(data.frequency * 1.15, 10.0)  # ~15% increase
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            fatigue_score=fatigue_score,
            ctr_decline=ctr_decline,
            frequency_risk=frequency_risk,
            saturation=saturation,
            decay_pattern=decay_pattern,
        )
        
        refresh_strategies = self._generate_refresh_strategies(
            fatigue_level=fatigue_level,
            decay_pattern=decay_pattern,
        )
        
        # Calculate optimal refresh date
        optimal_refresh_date = datetime.utcnow() + timedelta(days=max(0, days_until_fatigue - 3))
        
        return FatiguePrediction(
            ad_id=data.ad_id,
            fatigue_score=fatigue_score,
            fatigue_level=fatigue_level,
            days_until_fatigue=days_until_fatigue,
            refresh_urgency=refresh_urgency,
            ctr_decline_percent=ctr_decline * 100,
            cpm_increase_percent=cpm_increase * 100,
            frequency_risk=frequency_risk,
            audience_saturation=saturation,
            decay_pattern=decay_pattern,
            decay_rate=decay_rate * 100,
            projected_ctr_7d=projected_ctr,
            projected_cpm_7d=projected_cpm,
            projected_frequency_7d=projected_frequency,
            recommendations=recommendations,
            refresh_strategies=refresh_strategies,
            optimal_refresh_date=optimal_refresh_date,
        )
    
    def _calculate_ctr_decline(self, ctr_history: list[float]) -> float:
        """Calculate CTR decline from history."""
        if len(ctr_history) < 3:
            return 0.0
        
        # Compare recent avg to initial avg
        initial_avg = sum(ctr_history[:3]) / 3
        recent_avg = sum(ctr_history[-3:]) / 3
        
        if initial_avg == 0:
            return 0.0
        
        decline = (initial_avg - recent_avg) / initial_avg
        return max(0, decline)  # Only count declines
    
    def _calculate_cpm_increase(self, cpm_history: list[float]) -> float:
        """Calculate CPM increase from history."""
        if len(cpm_history) < 3:
            return 0.0
        
        initial_avg = sum(cpm_history[:3]) / 3
        recent_avg = sum(cpm_history[-3:]) / 3
        
        if initial_avg == 0:
            return 0.0
        
        increase = (recent_avg - initial_avg) / initial_avg
        return max(0, increase)  # Only count increases
    
    def _calculate_frequency_risk(self, frequency: float) -> float:
        """Calculate risk from ad frequency."""
        if frequency < self.config.frequency_warning:
            return frequency / self.config.frequency_warning * 0.3
        elif frequency < self.config.frequency_critical:
            return 0.3 + (frequency - self.config.frequency_warning) / (self.config.frequency_critical - self.config.frequency_warning) * 0.4
        else:
            return min(1.0, 0.7 + (frequency - self.config.frequency_critical) / 3 * 0.3)
    
    def _calculate_saturation(self, reach: int, audience_size: int) -> float:
        """Calculate audience saturation."""
        if audience_size == 0:
            return 0.5
        return min(1.0, reach / audience_size)
    
    def _detect_decay_pattern(self, ctr_history: list[float]) -> tuple[DecayPattern, float]:
        """Detect the pattern of performance decay."""
        if len(ctr_history) < 5:
            return DecayPattern.NONE, 0.0
        
        # Calculate daily changes
        changes = []
        for i in range(1, len(ctr_history)):
            if ctr_history[i-1] > 0:
                change = (ctr_history[i] - ctr_history[i-1]) / ctr_history[i-1]
                changes.append(change)
        
        if not changes:
            return DecayPattern.NONE, 0.0
        
        avg_change = sum(changes) / len(changes)
        
        # Check for sudden drop (any day with >20% decline)
        if any(c < -0.2 for c in changes):
            return DecayPattern.SUDDEN, abs(min(changes))
        
        # Check for plateau (very small changes)
        if all(abs(c) < 0.02 for c in changes):
            return DecayPattern.PLATEAU, 0.01
        
        # Check for cyclical (alternating ups and downs)
        sign_changes = sum(1 for i in range(1, len(changes)) if changes[i] * changes[i-1] < 0)
        if sign_changes > len(changes) * 0.6:
            return DecayPattern.CYCLICAL, abs(avg_change)
        
        # Default to gradual if overall declining
        if avg_change < -0.01:
            return DecayPattern.GRADUAL, abs(avg_change)
        
        return DecayPattern.NONE, 0.0
    
    def _calculate_fatigue_score(
        self,
        ctr_decline: float,
        cpm_increase: float,
        frequency_risk: float,
        saturation: float,
        days_running: int,
        industry: str,
    ) -> int:
        """Calculate overall fatigue score 0-100."""
        # Weight factors
        ctr_weight = 0.30
        cpm_weight = 0.20
        frequency_weight = 0.25
        saturation_weight = 0.15
        time_weight = 0.10
        
        # Normalize each factor to 0-100
        ctr_score = min(100, ctr_decline / self.config.ctr_decline_threshold * 100)
        cpm_score = min(100, cpm_increase / self.config.cpm_increase_threshold * 100)
        frequency_score = frequency_risk * 100
        saturation_score = saturation / self.config.saturation_threshold * 100 if saturation < self.config.saturation_threshold else 100
        
        # Time-based score (relative to industry benchmark)
        benchmark_days = self.config.industry_benchmarks.get(industry, 21)
        time_score = min(100, days_running / benchmark_days * 100)
        
        # Weighted sum
        total = (
            ctr_score * ctr_weight +
            cpm_score * cpm_weight +
            frequency_score * frequency_weight +
            saturation_score * saturation_weight +
            time_score * time_weight
        )
        
        return int(min(100, max(0, total)))
    
    def _get_fatigue_level(self, score: int) -> FatigueLevel:
        """Convert score to fatigue level."""
        if score <= 20:
            return FatigueLevel.FRESH
        elif score <= 40:
            return FatigueLevel.HEALTHY
        elif score <= 60:
            return FatigueLevel.MODERATE
        elif score <= 80:
            return FatigueLevel.HIGH
        else:
            return FatigueLevel.CRITICAL
    
    def _get_refresh_urgency(self, score: int, pattern: DecayPattern) -> RefreshUrgency:
        """Determine refresh urgency."""
        # Sudden decay always escalates urgency
        if pattern == DecayPattern.SUDDEN:
            if score > 40:
                return RefreshUrgency.IMMEDIATE
            elif score > 20:
                return RefreshUrgency.URGENT
        
        if score <= 20:
            return RefreshUrgency.NONE
        elif score <= 40:
            return RefreshUrgency.PLAN
        elif score <= 60:
            return RefreshUrgency.PREPARE
        elif score <= 80:
            return RefreshUrgency.URGENT
        else:
            return RefreshUrgency.IMMEDIATE
    
    def _estimate_days_until_fatigue(
        self,
        current_score: int,
        decay_rate: float,
        industry: str,
    ) -> int:
        """Estimate days until critical fatigue."""
        if current_score >= 80:
            return 0
        
        benchmark = self.config.industry_benchmarks.get(industry, 21)
        
        # Calculate based on decay rate and current score
        points_until_critical = 80 - current_score
        
        if decay_rate > 0:
            # Faster decay = fewer days
            days = int(points_until_critical / (decay_rate * 100 + 3))
        else:
            # Use industry benchmark
            remaining_pct = 1 - (current_score / 80)
            days = int(benchmark * remaining_pct)
        
        return max(0, min(90, days))
    
    def _project_metric(self, current: float, decay_rate: float, days: int) -> float:
        """Project a metric forward."""
        return current * ((1 - decay_rate) ** days)
    
    def _project_cpm(self, current: float, fatigue_score: int, days: int) -> float:
        """Project CPM forward (increases with fatigue)."""
        increase_rate = fatigue_score / 100 * 0.05  # Up to 5% per day at max fatigue
        return current * ((1 + increase_rate) ** days)
    
    def _generate_recommendations(
        self,
        fatigue_score: int,
        ctr_decline: float,
        frequency_risk: float,
        saturation: float,
        decay_pattern: DecayPattern,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if fatigue_score < 30:
            recs.append("✅ Ad is performing well - continue monitoring")
            return recs
        
        if ctr_decline > 0.15:
            recs.append("Refresh headline and primary text - CTR declining significantly")
        
        if frequency_risk > 0.5:
            recs.append("Expand audience targeting to reduce frequency")
            recs.append("Consider frequency capping at 3-4x per week")
        
        if saturation > 0.6:
            recs.append("Create lookalike audiences to reach new users")
            recs.append("Test different interest categories")
        
        if decay_pattern == DecayPattern.SUDDEN:
            recs.append("⚠️ Sudden performance drop detected - investigate immediately")
            recs.append("Check for external factors (competition, market events)")
        
        if decay_pattern == DecayPattern.PLATEAU:
            recs.append("Ad has plateaued - test new creative angles")
        
        if fatigue_score > 60:
            recs.append("Prepare replacement creative within 1 week")
        
        if fatigue_score > 80:
            recs.append("🔴 URGENT: Launch new creative immediately")
        
        return recs[:5]
    
    def _generate_refresh_strategies(
        self,
        fatigue_level: FatigueLevel,
        decay_pattern: DecayPattern,
    ) -> list[str]:
        """Generate creative refresh strategies."""
        strategies = []
        
        if fatigue_level in [FatigueLevel.FRESH, FatigueLevel.HEALTHY]:
            strategies.append("Minor tweaks: Update CTA button color or text")
            strategies.append("A/B test: Try different headline variations")
            return strategies
        
        strategies.append("Update visual: New hero image or background")
        strategies.append("Reframe angle: Try problem-focused vs solution-focused")
        strategies.append("Social proof: Add testimonials or user counts")
        
        if fatigue_level in [FatigueLevel.HIGH, FatigueLevel.CRITICAL]:
            strategies.append("Full refresh: New concept, copy, and visuals")
            strategies.append("Format change: Try video or carousel format")
            strategies.append("Audience pivot: Target different segments")
        
        if decay_pattern == DecayPattern.CYCLICAL:
            strategies.append("Rotate creatives: Use 3-4 variants in rotation")
        
        return strategies[:4]


# =============================================================================
# MOCK PREDICTOR FOR DEMO
# =============================================================================

class MockFatiguePredictor:
    """Mock predictor for demo/testing."""
    
    async def predict(self, data: AdPerformanceData) -> FatiguePrediction:
        """Generate realistic mock prediction."""
        await asyncio.sleep(0.3)
        
        # Simulate based on days running
        if data.days_running < 7:
            fatigue_score = 15
            fatigue_level = FatigueLevel.FRESH
            days_until = 25
            urgency = RefreshUrgency.NONE
        elif data.days_running < 14:
            fatigue_score = 35
            fatigue_level = FatigueLevel.HEALTHY
            days_until = 14
            urgency = RefreshUrgency.PLAN
        elif data.days_running < 21:
            fatigue_score = 55
            fatigue_level = FatigueLevel.MODERATE
            days_until = 7
            urgency = RefreshUrgency.PREPARE
        elif data.days_running < 28:
            fatigue_score = 72
            fatigue_level = FatigueLevel.HIGH
            days_until = 3
            urgency = RefreshUrgency.URGENT
        else:
            fatigue_score = 88
            fatigue_level = FatigueLevel.CRITICAL
            days_until = 0
            urgency = RefreshUrgency.IMMEDIATE
        
        return FatiguePrediction(
            ad_id=data.ad_id,
            fatigue_score=fatigue_score,
            fatigue_level=fatigue_level,
            days_until_fatigue=days_until,
            refresh_urgency=urgency,
            ctr_decline_percent=data.days_running * 0.8,
            cpm_increase_percent=data.days_running * 1.2,
            frequency_risk=min(1.0, data.frequency / 5),
            audience_saturation=min(1.0, data.days_running / 30),
            decay_pattern=DecayPattern.GRADUAL if data.days_running > 7 else DecayPattern.NONE,
            decay_rate=data.days_running * 0.3,
            projected_ctr_7d=max(0.5, 2.0 - data.days_running * 0.05),
            projected_cpm_7d=10 + data.days_running * 0.5,
            projected_frequency_7d=min(6.0, data.frequency * 1.2),
            recommendations=[
                "Update headline with fresh angle" if fatigue_score > 40 else "Continue monitoring performance",
                "Expand audience targeting" if fatigue_score > 50 else "Test minor variations",
                "Prepare replacement creative" if fatigue_score > 60 else "A/B test current creative",
            ],
            refresh_strategies=[
                "Update hero image with new visual",
                "Reframe from problem to solution angle",
                "Add social proof (testimonials, stats)",
                "Test video format",
            ][:3 if fatigue_score > 50 else 2],
            optimal_refresh_date=datetime.utcnow() + timedelta(days=max(0, days_until - 2)),
        )


def get_fatigue_predictor() -> FatiguePredictor | MockFatiguePredictor:
    """Get appropriate predictor."""
    # Always use real predictor (no API needed)
    return FatiguePredictor()


# =============================================================================
# DEMO
# =============================================================================

async def demo_fatigue_predictor():
    """Demo the fatigue predictor."""
    print("\n" + "="*60)
    print("CREATIVE FATIGUE PREDICTOR DEMO")
    print("="*60)
    
    predictor = FatiguePredictor()
    
    # Test different scenarios
    scenarios = [
        ("Fresh Ad (3 days)", 3, 1.2, [2.1, 2.0, 2.05]),
        ("Healthy Ad (10 days)", 10, 2.0, [2.1, 2.0, 1.95, 1.9, 1.85, 1.82, 1.8, 1.78, 1.75, 1.72]),
        ("Fatiguing Ad (21 days)", 21, 3.5, [2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.55, 1.5, 1.45, 1.4, 1.35, 1.3, 1.28, 1.25, 1.22, 1.2, 1.18, 1.15, 1.12, 1.1, 1.08]),
        ("Critical Ad (35 days)", 35, 5.0, [2.1, 2.0, 1.8, 1.6, 1.4, 1.2, 1.1, 1.0, 0.95, 0.9, 0.85, 0.82, 0.8, 0.78, 0.76, 0.74, 0.72, 0.7, 0.68, 0.66]),
    ]
    
    for name, days, freq, ctr_history in scenarios:
        print(f"\n📊 {name}")
        print("-" * 40)
        
        data = AdPerformanceData(
            ad_id=f"ad_{days}d",
            start_date=datetime.utcnow() - timedelta(days=days),
            days_running=days,
            frequency=freq,
            ctr_history=ctr_history,
            cpm_history=[10 + i * 0.5 for i in range(len(ctr_history))],
            reach=days * 5000,
            audience_size=200000,
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        print(f"   {prediction.get_summary()}")
        print(f"   CTR Decline: {prediction.ctr_decline_percent:.1f}%")
        print(f"   CPM Increase: {prediction.cpm_increase_percent:.1f}%")
        print(f"   Frequency Risk: {prediction.frequency_risk:.0%}")
        print(f"   Decay Pattern: {prediction.decay_pattern.value}")
        print(f"   Urgency: {prediction.refresh_urgency.value}")
        print(f"   Top Rec: {prediction.recommendations[0]}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_fatigue_predictor())
