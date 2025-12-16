# src/analyzers/performance_predictor.py
"""Performance Predictor for BrandTruth AI - Slice 9

Predicts ad performance before launch using AI analysis.

Features:
- Overall performance score (0-100)
- CTR prediction (low/medium/high)
- Conversion prediction
- Component breakdown scores
- Actionable recommendations
- A/B test suggestions

Uses Claude to analyze:
- Copy effectiveness (headline, body, CTA)
- Image-copy alignment
- Emotional resonance
- Platform best practices
- Competitive positioning
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from anthropic import Anthropic

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class PerformanceTier(str, Enum):
    """Performance prediction tiers."""
    EXCEPTIONAL = "exceptional"  # 90-100
    STRONG = "strong"            # 75-89
    GOOD = "good"                # 60-74
    AVERAGE = "average"          # 40-59
    WEAK = "weak"                # 20-39
    POOR = "poor"                # 0-19


class CTRPrediction(str, Enum):
    """Click-through rate prediction."""
    VERY_HIGH = "very_high"      # Top 10%
    HIGH = "high"                # Top 25%
    ABOVE_AVERAGE = "above_average"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    LOW = "low"


class ImprovementPriority(str, Enum):
    """Priority level for improvements."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# DATA MODELS
# =============================================================================

class ComponentScore(BaseModel):
    """Score for a specific ad component."""
    name: str
    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    analysis: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class Improvement(BaseModel):
    """Suggested improvement for the ad."""
    component: str
    priority: ImprovementPriority
    suggestion: str
    expected_impact: str
    example: Optional[str] = None


class ABTestSuggestion(BaseModel):
    """A/B test suggestion."""
    variant_name: str
    change_description: str
    hypothesis: str
    expected_lift: str


class PerformancePrediction(BaseModel):
    """Complete performance prediction for an ad."""
    # Overall scores
    overall_score: int = Field(ge=0, le=100)
    performance_tier: PerformanceTier
    confidence: float = Field(ge=0, le=1)
    
    # Predictions
    ctr_prediction: CTRPrediction
    estimated_ctr_range: tuple[float, float]  # e.g., (1.2, 1.8) = 1.2%-1.8%
    conversion_potential: str  # "High", "Medium", "Low"
    
    # Component breakdown
    component_scores: list[ComponentScore]
    
    # Recommendations
    improvements: list[Improvement]
    ab_test_suggestions: list[ABTestSuggestion]
    
    # Meta
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "1.0"
    
    def get_summary(self) -> str:
        """Get a human-readable summary."""
        emoji = {
            PerformanceTier.EXCEPTIONAL: "🌟",
            PerformanceTier.STRONG: "💪",
            PerformanceTier.GOOD: "👍",
            PerformanceTier.AVERAGE: "📊",
            PerformanceTier.WEAK: "⚠️",
            PerformanceTier.POOR: "❌",
        }
        return f"{emoji.get(self.performance_tier, '📊')} {self.overall_score}/100 - {self.performance_tier.value.title()} Performance"


class AdToAnalyze(BaseModel):
    """Ad content to analyze."""
    headline: str
    primary_text: str
    cta: str
    image_url: Optional[str] = None
    image_description: Optional[str] = None
    landing_page_url: Optional[str] = None
    target_audience: Optional[str] = None
    platform: str = "meta"
    objective: str = "conversions"
    industry: Optional[str] = None
    brand_name: Optional[str] = None


# =============================================================================
# PERFORMANCE PREDICTOR
# =============================================================================

class PerformancePredictor:
    """Predicts ad performance using AI analysis."""
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def predict(self, ad: AdToAnalyze) -> PerformancePrediction:
        """
        Predict performance for an ad.
        
        Returns a comprehensive prediction with scores, recommendations, and A/B test suggestions.
        """
        logger.info(f"Analyzing ad performance: {ad.headline[:50]}...")
        
        prompt = self._build_analysis_prompt(ad)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            
            result_text = response.content[0].text
            
            # Parse the JSON response with cleanup
            result_json = self._extract_and_clean_json(result_text)
            if result_json:
                return self._parse_prediction(result_json)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Return a default prediction on error
            return self._default_prediction(str(e))
    
    def _extract_and_clean_json(self, text: str) -> dict | None:
        """Extract and clean JSON from Claude's response."""
        import re
        
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        # Find JSON object
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start < 0 or json_end <= json_start:
            return None
        
        json_str = text[json_start:json_end]
        
        # Clean common JSON issues from LLM output
        # Remove trailing commas before ] or }
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        
        # Remove single-line comments (// ...)
        json_str = re.sub(r'//[^\n]*', '', json_str)
        
        # Remove multi-line comments (/* ... */)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Try to parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse warning: {e}")
            # Try one more cleanup - remove any remaining invalid chars
            json_str = re.sub(r'[\x00-\x1f]+', ' ', json_str)
            try:
                return json.loads(json_str)
            except:
                return None
    
    def _build_analysis_prompt(self, ad: AdToAnalyze) -> str:
        """Build the analysis prompt for Claude."""
        return f"""You are an expert performance marketing analyst with 15+ years experience optimizing Meta ads. Analyze this ad and predict its performance.

## Ad Details
- **Headline:** {ad.headline}
- **Primary Text:** {ad.primary_text}
- **CTA:** {ad.cta}
- **Platform:** {ad.platform}
- **Objective:** {ad.objective}
{f"- **Image Description:** {ad.image_description}" if ad.image_description else ""}
{f"- **Target Audience:** {ad.target_audience}" if ad.target_audience else ""}
{f"- **Industry:** {ad.industry}" if ad.industry else ""}
{f"- **Brand:** {ad.brand_name}" if ad.brand_name else ""}

## Analysis Framework

Score each component 0-100 based on:

1. **Headline (25% weight)**
   - Attention-grabbing power
   - Clarity and specificity
   - Emotional trigger
   - Character count optimization (25-40 ideal)
   - Power words usage

2. **Primary Text (25% weight)**
   - Hook strength (first 125 characters)
   - Value proposition clarity
   - Social proof elements
   - Urgency/scarcity signals
   - Readability and flow

3. **CTA (15% weight)**
   - Action clarity
   - Urgency
   - Benefit alignment
   - Platform best practices

4. **Emotional Resonance (20% weight)**
   - Target emotion identification
   - Emotional journey
   - Pain/gain balance
   - Authenticity

5. **Platform Optimization (15% weight)**
   - Meta best practices
   - Format compliance
   - Policy alignment
   - Mobile optimization

## Response Format

Return a JSON object with this exact structure:

{{
  "overall_score": <0-100>,
  "performance_tier": "<exceptional|strong|good|average|weak|poor>",
  "confidence": <0.0-1.0>,
  "ctr_prediction": "<very_high|high|above_average|average|below_average|low>",
  "estimated_ctr_range": [<min_percent>, <max_percent>],
  "conversion_potential": "<High|Medium|Low>",
  "component_scores": [
    {{
      "name": "Headline",
      "score": <0-100>,
      "weight": 0.25,
      "analysis": "<detailed analysis>",
      "strengths": ["<strength1>", "<strength2>"],
      "weaknesses": ["<weakness1>"]
    }},
    {{
      "name": "Primary Text",
      "score": <0-100>,
      "weight": 0.25,
      "analysis": "<detailed analysis>",
      "strengths": [],
      "weaknesses": []
    }},
    {{
      "name": "CTA",
      "score": <0-100>,
      "weight": 0.15,
      "analysis": "<detailed analysis>",
      "strengths": [],
      "weaknesses": []
    }},
    {{
      "name": "Emotional Resonance",
      "score": <0-100>,
      "weight": 0.20,
      "analysis": "<detailed analysis>",
      "strengths": [],
      "weaknesses": []
    }},
    {{
      "name": "Platform Optimization",
      "score": <0-100>,
      "weight": 0.15,
      "analysis": "<detailed analysis>",
      "strengths": [],
      "weaknesses": []
    }}
  ],
  "improvements": [
    {{
      "component": "<component name>",
      "priority": "<critical|high|medium|low>",
      "suggestion": "<specific actionable suggestion>",
      "expected_impact": "<expected improvement>",
      "example": "<rewritten example if applicable>"
    }}
  ],
  "ab_test_suggestions": [
    {{
      "variant_name": "<variant name>",
      "change_description": "<what to change>",
      "hypothesis": "<why this might improve performance>",
      "expected_lift": "<estimated % improvement>"
    }}
  ]
}}

Be specific, actionable, and data-driven in your analysis. Provide at least 3 improvements and 2 A/B test suggestions."""

    def _parse_prediction(self, data: dict) -> PerformancePrediction:
        """Parse the JSON response into a PerformancePrediction."""
        return PerformancePrediction(
            overall_score=data.get("overall_score", 50),
            performance_tier=PerformanceTier(data.get("performance_tier", "average")),
            confidence=data.get("confidence", 0.7),
            ctr_prediction=CTRPrediction(data.get("ctr_prediction", "average")),
            estimated_ctr_range=tuple(data.get("estimated_ctr_range", [0.8, 1.2])),
            conversion_potential=data.get("conversion_potential", "Medium"),
            component_scores=[
                ComponentScore(**cs) for cs in data.get("component_scores", [])
            ],
            improvements=[
                Improvement(**imp) for imp in data.get("improvements", [])
            ],
            ab_test_suggestions=[
                ABTestSuggestion(**ab) for ab in data.get("ab_test_suggestions", [])
            ],
        )
    
    def _default_prediction(self, error: str) -> PerformancePrediction:
        """Return a default prediction when analysis fails."""
        return PerformancePrediction(
            overall_score=50,
            performance_tier=PerformanceTier.AVERAGE,
            confidence=0.3,
            ctr_prediction=CTRPrediction.AVERAGE,
            estimated_ctr_range=(0.8, 1.2),
            conversion_potential="Medium",
            component_scores=[
                ComponentScore(
                    name="Analysis",
                    score=50,
                    weight=1.0,
                    analysis=f"Analysis could not be completed: {error}",
                    strengths=[],
                    weaknesses=["Unable to fully analyze"],
                )
            ],
            improvements=[
                Improvement(
                    component="Overall",
                    priority=ImprovementPriority.HIGH,
                    suggestion="Re-run analysis for detailed recommendations",
                    expected_impact="Unknown",
                )
            ],
            ab_test_suggestions=[],
        )
    
    async def predict_batch(self, ads: list[AdToAnalyze]) -> list[PerformancePrediction]:
        """Predict performance for multiple ads."""
        results = []
        for ad in ads:
            prediction = await self.predict(ad)
            results.append(prediction)
        return results
    
    async def compare_variants(
        self, 
        variants: list[AdToAnalyze]
    ) -> dict:
        """Compare multiple ad variants and rank them."""
        predictions = await self.predict_batch(variants)
        
        # Sort by overall score
        ranked = sorted(
            zip(variants, predictions),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        return {
            "rankings": [
                {
                    "rank": i + 1,
                    "headline": v.headline,
                    "score": p.overall_score,
                    "tier": p.performance_tier.value,
                    "ctr_prediction": p.ctr_prediction.value,
                }
                for i, (v, p) in enumerate(ranked)
            ],
            "winner": {
                "headline": ranked[0][0].headline,
                "score": ranked[0][1].overall_score,
                "margin": ranked[0][1].overall_score - ranked[1][1].overall_score if len(ranked) > 1 else 0,
            },
            "recommendations": [
                f"Lead with '{ranked[0][0].headline}' - {ranked[0][1].overall_score}/100 score",
                f"Consider A/B testing top 2 variants" if len(ranked) > 1 else "Only one variant analyzed",
            ],
        }


# =============================================================================
# MOCK PREDICTOR FOR DEMO
# =============================================================================

class MockPerformancePredictor:
    """Mock predictor for demo/testing without API calls."""
    
    async def predict(self, ad: AdToAnalyze) -> PerformancePrediction:
        """Generate a realistic mock prediction."""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        # Generate scores based on simple heuristics
        headline_score = self._score_headline(ad.headline)
        text_score = self._score_text(ad.primary_text)
        cta_score = self._score_cta(ad.cta)
        
        # Calculate weighted average
        overall = int(
            headline_score * 0.25 +
            text_score * 0.25 +
            cta_score * 0.15 +
            75 * 0.20 +  # Emotional resonance (default)
            70 * 0.15    # Platform optimization (default)
        )
        
        # Determine tier
        tier = self._get_tier(overall)
        ctr = self._get_ctr_prediction(overall)
        
        return PerformancePrediction(
            overall_score=overall,
            performance_tier=tier,
            confidence=0.78,
            ctr_prediction=ctr,
            estimated_ctr_range=(overall * 0.015, overall * 0.025),
            conversion_potential="High" if overall >= 75 else "Medium" if overall >= 50 else "Low",
            component_scores=[
                ComponentScore(
                    name="Headline",
                    score=headline_score,
                    weight=0.25,
                    analysis=f"Headline is {len(ad.headline)} characters. " + 
                             ("Good length for mobile." if 20 <= len(ad.headline) <= 40 else "Consider optimizing length."),
                    strengths=["Clear value proposition"] if headline_score >= 70 else [],
                    weaknesses=["Could be more specific"] if headline_score < 70 else [],
                ),
                ComponentScore(
                    name="Primary Text",
                    score=text_score,
                    weight=0.25,
                    analysis=f"Primary text is {len(ad.primary_text)} characters. " +
                             ("Strong hook in first 125 chars." if len(ad.primary_text) >= 100 else "Consider expanding."),
                    strengths=["Good storytelling"] if text_score >= 70 else [],
                    weaknesses=["Missing social proof"] if text_score < 80 else [],
                ),
                ComponentScore(
                    name="CTA",
                    score=cta_score,
                    weight=0.15,
                    analysis=f"'{ad.cta}' is a " + ("strong" if cta_score >= 75 else "standard") + " call to action.",
                    strengths=["Action-oriented"] if cta_score >= 70 else [],
                    weaknesses=["Could add urgency"] if cta_score < 80 else [],
                ),
                ComponentScore(
                    name="Emotional Resonance",
                    score=75,
                    weight=0.20,
                    analysis="Good emotional appeal with clear pain/gain messaging.",
                    strengths=["Addresses user pain points"],
                    weaknesses=[],
                ),
                ComponentScore(
                    name="Platform Optimization",
                    score=70,
                    weight=0.15,
                    analysis="Well-formatted for Meta Ads.",
                    strengths=["Mobile-friendly format"],
                    weaknesses=["Could add emoji for engagement"],
                ),
            ],
            improvements=[
                Improvement(
                    component="Headline",
                    priority=ImprovementPriority.HIGH,
                    suggestion="Add a number or statistic for credibility",
                    expected_impact="+15-20% CTR improvement",
                    example=f"10,000+ Users Trust {ad.headline.split()[-1] if ad.headline.split() else 'This'}",
                ),
                Improvement(
                    component="Primary Text",
                    priority=ImprovementPriority.MEDIUM,
                    suggestion="Add social proof in the first line",
                    expected_impact="+10-15% engagement",
                    example="Join 50,000+ professionals who...",
                ),
                Improvement(
                    component="CTA",
                    priority=ImprovementPriority.LOW,
                    suggestion="Test urgency-based CTAs",
                    expected_impact="+5-10% conversion",
                    example="Start Free Today",
                ),
            ],
            ab_test_suggestions=[
                ABTestSuggestion(
                    variant_name="Urgency Test",
                    change_description="Add time-limited offer to headline",
                    hypothesis="Scarcity increases click intent",
                    expected_lift="10-25%",
                ),
                ABTestSuggestion(
                    variant_name="Social Proof Test",
                    change_description="Lead with user count or testimonial",
                    hypothesis="Social validation builds trust",
                    expected_lift="15-30%",
                ),
            ],
        )
    
    def _score_headline(self, headline: str) -> int:
        score = 60
        # Length bonus
        if 20 <= len(headline) <= 40:
            score += 15
        elif len(headline) < 20:
            score += 5
        # Power words
        power_words = ["stop", "get", "how", "why", "free", "new", "now", "best", "easy", "fast"]
        if any(word in headline.lower() for word in power_words):
            score += 10
        # Numbers
        if any(char.isdigit() for char in headline):
            score += 10
        return min(score, 100)
    
    def _score_text(self, text: str) -> int:
        score = 55
        # Length bonus
        if 100 <= len(text) <= 300:
            score += 20
        elif len(text) >= 50:
            score += 10
        # Emoji presence
        if any(ord(char) > 127 for char in text):
            score += 5
        # Question mark (engagement)
        if "?" in text:
            score += 5
        # Social proof keywords
        if any(word in text.lower() for word in ["join", "trusted", "users", "customers", "reviews"]):
            score += 10
        return min(score, 100)
    
    def _score_cta(self, cta: str) -> int:
        strong_ctas = ["get started", "start free", "try now", "sign up free", "claim offer"]
        medium_ctas = ["learn more", "shop now", "book now", "download"]
        
        cta_lower = cta.lower()
        if any(s in cta_lower for s in strong_ctas):
            return 85
        elif any(s in cta_lower for s in medium_ctas):
            return 70
        return 60
    
    def _get_tier(self, score: int) -> PerformanceTier:
        if score >= 90:
            return PerformanceTier.EXCEPTIONAL
        elif score >= 75:
            return PerformanceTier.STRONG
        elif score >= 60:
            return PerformanceTier.GOOD
        elif score >= 40:
            return PerformanceTier.AVERAGE
        elif score >= 20:
            return PerformanceTier.WEAK
        return PerformanceTier.POOR
    
    def _get_ctr_prediction(self, score: int) -> CTRPrediction:
        if score >= 90:
            return CTRPrediction.VERY_HIGH
        elif score >= 80:
            return CTRPrediction.HIGH
        elif score >= 65:
            return CTRPrediction.ABOVE_AVERAGE
        elif score >= 50:
            return CTRPrediction.AVERAGE
        elif score >= 35:
            return CTRPrediction.BELOW_AVERAGE
        return CTRPrediction.LOW
    
    async def predict_batch(self, ads: list[AdToAnalyze]) -> list[PerformancePrediction]:
        return [await self.predict(ad) for ad in ads]
    
    async def compare_variants(self, variants: list[AdToAnalyze]) -> dict:
        predictions = await self.predict_batch(variants)
        ranked = sorted(
            zip(variants, predictions),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        return {
            "rankings": [
                {
                    "rank": i + 1,
                    "headline": v.headline,
                    "score": p.overall_score,
                    "tier": p.performance_tier.value,
                }
                for i, (v, p) in enumerate(ranked)
            ],
            "winner": {
                "headline": ranked[0][0].headline,
                "score": ranked[0][1].overall_score,
            },
        }


def get_predictor() -> PerformancePredictor | MockPerformancePredictor:
    """Get the appropriate predictor based on configuration."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return PerformancePredictor()
    return MockPerformancePredictor()


# =============================================================================
# DEMO
# =============================================================================

async def demo_predictor():
    """Demo the performance predictor."""
    print("\n" + "="*60)
    print("PERFORMANCE PREDICTOR DEMO")
    print("="*60)
    
    predictor = get_predictor()
    
    ad = AdToAnalyze(
        headline="Stop Getting Rejected by ATS",
        primary_text="Your dream job slips away because your resume can't pass automated screening. Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.",
        cta="Get Started",
        platform="meta",
        objective="conversions",
        industry="Career Tech",
        brand_name="Careerfied",
        target_audience="Job seekers aged 25-45",
    )
    
    print(f"\n📝 Analyzing: {ad.headline}")
    print("-" * 40)
    
    prediction = await predictor.predict(ad)
    
    print(f"\n{prediction.get_summary()}")
    print(f"Confidence: {prediction.confidence:.0%}")
    print(f"CTR Prediction: {prediction.ctr_prediction.value.replace('_', ' ').title()}")
    print(f"Estimated CTR: {prediction.estimated_ctr_range[0]:.1f}% - {prediction.estimated_ctr_range[1]:.1f}%")
    print(f"Conversion Potential: {prediction.conversion_potential}")
    
    print("\n📊 Component Breakdown:")
    for cs in prediction.component_scores:
        bar = "█" * (cs.score // 10) + "░" * (10 - cs.score // 10)
        print(f"  {cs.name:20} {bar} {cs.score}")
    
    print("\n💡 Top Improvements:")
    for imp in prediction.improvements[:3]:
        print(f"  [{imp.priority.value.upper():8}] {imp.suggestion}")
        if imp.example:
            print(f"             Example: {imp.example}")
    
    print("\n🧪 A/B Test Suggestions:")
    for ab in prediction.ab_test_suggestions[:2]:
        print(f"  • {ab.variant_name}: {ab.change_description}")
        print(f"    Expected lift: {ab.expected_lift}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_predictor())
