# src/analyzers/ab_test_planner.py
"""A/B Test Planner - Creates statistically sound test plans.

Provides:
- Recommended test pairs
- Sample size calculation
- Test duration estimates
- Statistical significance guidance
"""

import logging
import math
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TestElement(str, Enum):
    HEADLINE = "headline"
    PRIMARY_TEXT = "primary_text"
    CTA = "cta"
    IMAGE = "image"
    AUDIENCE = "audience"
    PLACEMENT = "placement"


class TestPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestPair(BaseModel):
    element: TestElement
    variant_a: str
    variant_b: str
    hypothesis: str
    priority: TestPriority
    expected_lift: str
    test_order: int


class ABTestPlan(BaseModel):
    test_pairs: list[TestPair]
    required_sample_size: int
    required_conversions: int
    estimated_days: int
    daily_budget_needed: float
    confidence_level: float
    minimum_detectable_effect: float
    recommendations: list[str] = Field(default_factory=list)
    testing_sequence: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        return f"{len(self.test_pairs)} tests planned | ~{self.estimated_days} days | ${self.daily_budget_needed}/day minimum"


class ABTestRequest(BaseModel):
    variants: list[dict]  # List of ad variants with headline, primary_text, cta, etc.
    baseline_ctr: float = 1.0
    baseline_cvr: float = 2.0
    daily_budget: float = 50
    confidence_level: float = 0.95
    minimum_lift: float = 0.20  # 20% minimum detectable effect


class ABTestPlanner:
    def __init__(self):
        pass
    
    async def plan(self, request: ABTestRequest) -> ABTestPlan:
        logger.info(f"Planning A/B tests for {len(request.variants)} variants")
        
        # Calculate sample size needed
        sample_size = self._calculate_sample_size(
            baseline_rate=request.baseline_cvr / 100,
            mde=request.minimum_lift,
            alpha=1 - request.confidence_level,
        )
        
        # Calculate required conversions per variant
        required_conversions = int(sample_size * (request.baseline_cvr / 100))
        
        # Estimate days needed
        estimated_cpm = 15  # Assume $15 CPM
        daily_impressions = (request.daily_budget / estimated_cpm) * 1000
        daily_clicks = daily_impressions * (request.baseline_ctr / 100)
        daily_conversions = daily_clicks * (request.baseline_cvr / 100)
        
        # Need conversions for 2 variants
        total_conversions_needed = required_conversions * 2
        estimated_days = math.ceil(total_conversions_needed / max(daily_conversions, 1))
        estimated_days = max(7, min(estimated_days, 60))  # Between 1 week and 2 months
        
        # Generate test pairs
        test_pairs = self._generate_test_pairs(request.variants)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(request, estimated_days, test_pairs)
        
        # Testing sequence
        sequence = [
            "1. Test headlines first (highest impact)",
            "2. Winner + new primary text variations",
            "3. Winner + CTA variations",
            "4. Winner + image variations",
            "5. Scale winning combination",
        ]
        
        return ABTestPlan(
            test_pairs=test_pairs,
            required_sample_size=sample_size,
            required_conversions=required_conversions,
            estimated_days=estimated_days,
            daily_budget_needed=request.daily_budget,
            confidence_level=request.confidence_level,
            minimum_detectable_effect=request.minimum_lift,
            recommendations=recommendations,
            testing_sequence=sequence,
        )
    
    def _calculate_sample_size(self, baseline_rate: float, mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
        """Calculate required sample size per variant using simplified formula."""
        # Z-scores for common values
        z_alpha = 1.96  # 95% confidence
        z_power = 0.84  # 80% power
        
        if alpha == 0.1:
            z_alpha = 1.645
        elif alpha == 0.01:
            z_alpha = 2.576
        
        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        p_avg = (p1 + p2) / 2
        
        numerator = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + 
                     z_power * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2
        
        sample_size = int(numerator / max(denominator, 0.0001))
        return max(sample_size, 100)  # Minimum 100 per variant
    
    def _generate_test_pairs(self, variants: list[dict]) -> list[TestPair]:
        """Generate prioritized test pairs from variants."""
        pairs = []
        
        if len(variants) < 2:
            return pairs
        
        # Extract unique elements to test
        headlines = list(set(v.get("headline", "") for v in variants if v.get("headline")))
        texts = list(set(v.get("primary_text", "") for v in variants if v.get("primary_text")))
        ctas = list(set(v.get("cta", "") for v in variants if v.get("cta")))
        
        order = 1
        
        # Headline tests (highest priority)
        if len(headlines) >= 2:
            pairs.append(TestPair(
                element=TestElement.HEADLINE,
                variant_a=headlines[0][:50] + "..." if len(headlines[0]) > 50 else headlines[0],
                variant_b=headlines[1][:50] + "..." if len(headlines[1]) > 50 else headlines[1],
                hypothesis="Different headlines will impact CTR and initial engagement",
                priority=TestPriority.HIGH,
                expected_lift="10-30%",
                test_order=order,
            ))
            order += 1
        
        # Primary text tests
        if len(texts) >= 2:
            pairs.append(TestPair(
                element=TestElement.PRIMARY_TEXT,
                variant_a=texts[0][:50] + "..." if len(texts[0]) > 50 else texts[0],
                variant_b=texts[1][:50] + "..." if len(texts[1]) > 50 else texts[1],
                hypothesis="Different body copy will impact conversion rate",
                priority=TestPriority.MEDIUM,
                expected_lift="5-15%",
                test_order=order,
            ))
            order += 1
        
        # CTA tests
        if len(ctas) >= 2:
            pairs.append(TestPair(
                element=TestElement.CTA,
                variant_a=ctas[0],
                variant_b=ctas[1] if len(ctas) > 1 else "Get Started",
                hypothesis="CTA wording impacts click-through on final action",
                priority=TestPriority.MEDIUM,
                expected_lift="5-20%",
                test_order=order,
            ))
        
        return pairs
    
    def _generate_recommendations(self, request: ABTestRequest, days: int, pairs: list[TestPair]) -> list[str]:
        recs = []
        
        if days > 30:
            recs.append(f"At ${request.daily_budget}/day, tests take {days}+ days. Consider increasing budget.")
        
        if request.daily_budget < 30:
            recs.append("Budget under $30/day may not generate enough data for reliable tests")
        
        if len(pairs) > 3:
            recs.append("Run tests sequentially, not simultaneously, to isolate variables")
        
        recs.append("Don't stop tests early - wait for statistical significance")
        recs.append("Document learnings from each test for future campaigns")
        
        return recs
    
    def calculate_significance(self, control_conversions: int, control_visitors: int,
                               variant_conversions: int, variant_visitors: int) -> dict:
        """Calculate if test results are statistically significant."""
        control_rate = control_conversions / max(control_visitors, 1)
        variant_rate = variant_conversions / max(variant_visitors, 1)
        
        lift = (variant_rate - control_rate) / max(control_rate, 0.001)
        
        # Simplified significance calculation
        pooled_rate = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
        se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_visitors + 1/variant_visitors))
        z_score = (variant_rate - control_rate) / max(se, 0.001)
        
        is_significant = abs(z_score) > 1.96  # 95% confidence
        
        return {
            "control_rate": round(control_rate * 100, 2),
            "variant_rate": round(variant_rate * 100, 2),
            "lift": round(lift * 100, 1),
            "is_significant": is_significant,
            "confidence": "95%" if is_significant else "Not yet significant",
            "recommendation": "Variant wins!" if is_significant and lift > 0 else 
                            "Control wins!" if is_significant and lift < 0 else
                            "Continue testing",
        }


_instance: Optional[ABTestPlanner] = None

def get_ab_test_planner() -> ABTestPlanner:
    global _instance
    if _instance is None:
        _instance = ABTestPlanner()
    return _instance
