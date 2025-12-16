# src/analyzers/iteration_assistant.py
"""Ad Iteration Assistant - Diagnoses and improves underperforming ads.

Provides:
- Performance diagnosis
- Root cause analysis
- Improved variants
- Next test suggestions
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PerformanceIssue(str, Enum):
    LOW_CTR = "low_ctr"
    LOW_CVR = "low_cvr"
    HIGH_CPA = "high_cpa"
    LOW_ROAS = "low_roas"
    HIGH_FREQUENCY = "high_frequency"
    DECLINING_PERFORMANCE = "declining_performance"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Diagnosis(BaseModel):
    issue: PerformanceIssue
    severity: IssueSeverity
    description: str
    likely_cause: str
    impact: str


class ImprovedVariant(BaseModel):
    element: str  # headline, primary_text, cta
    original: str
    improved: str
    rationale: str
    expected_improvement: str


class IterationPlan(BaseModel):
    diagnoses: list[Diagnosis]
    improved_variants: list[ImprovedVariant]
    priority_fixes: list[str]
    testing_roadmap: list[str]
    quick_wins: list[str]
    estimated_improvement: str
    
    def get_summary(self) -> str:
        critical = sum(1 for d in self.diagnoses if d.severity == IssueSeverity.CRITICAL)
        return f"{critical} critical issues | {len(self.improved_variants)} improvements suggested"


class IterationRequest(BaseModel):
    headline: str
    primary_text: str
    cta: str
    current_ctr: float = 0.8  # percentage
    current_cvr: float = 1.5  # percentage
    current_cpa: float = 80
    target_cpa: float = 50
    impressions: int = 10000
    frequency: float = 2.0
    days_running: int = 7
    industry_avg_ctr: float = 1.0
    industry_avg_cvr: float = 2.5


# Benchmarks
BENCHMARKS = {
    "ctr": {"poor": 0.5, "average": 1.0, "good": 1.5, "excellent": 2.5},
    "cvr": {"poor": 1.0, "average": 2.0, "good": 3.5, "excellent": 5.0},
}


class IterationAssistant:
    def __init__(self):
        self.benchmarks = BENCHMARKS
    
    async def analyze(self, request: IterationRequest) -> IterationPlan:
        logger.info("Analyzing ad performance for iteration...")
        
        # Diagnose issues
        diagnoses = self._diagnose(request)
        
        # Generate improved variants
        improved = self._generate_improvements(request, diagnoses)
        
        # Priority fixes
        priority_fixes = self._prioritize_fixes(diagnoses)
        
        # Testing roadmap
        roadmap = self._create_roadmap(diagnoses, improved)
        
        # Quick wins
        quick_wins = self._identify_quick_wins(request, diagnoses)
        
        # Estimate improvement
        estimated = self._estimate_improvement(diagnoses)
        
        return IterationPlan(
            diagnoses=diagnoses,
            improved_variants=improved,
            priority_fixes=priority_fixes,
            testing_roadmap=roadmap,
            quick_wins=quick_wins,
            estimated_improvement=estimated,
        )
    
    def _diagnose(self, request: IterationRequest) -> list[Diagnosis]:
        diagnoses = []
        
        # CTR analysis
        if request.current_ctr < self.benchmarks["ctr"]["poor"]:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.LOW_CTR,
                severity=IssueSeverity.CRITICAL,
                description=f"CTR of {request.current_ctr}% is significantly below average",
                likely_cause="Hook/headline not compelling enough or poor audience-message fit",
                impact="Low traffic to landing page, wasted impressions",
            ))
        elif request.current_ctr < self.benchmarks["ctr"]["average"]:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.LOW_CTR,
                severity=IssueSeverity.WARNING,
                description=f"CTR of {request.current_ctr}% is below industry average",
                likely_cause="Headline may not stand out or lacks urgency",
                impact="Paying for impressions that don't convert to clicks",
            ))
        
        # CVR analysis
        if request.current_cvr < self.benchmarks["cvr"]["poor"]:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.LOW_CVR,
                severity=IssueSeverity.CRITICAL,
                description=f"CVR of {request.current_cvr}% is critically low",
                likely_cause="Landing page mismatch, wrong audience, or unclear value prop",
                impact="High CPA, unprofitable campaigns",
            ))
        elif request.current_cvr < self.benchmarks["cvr"]["average"]:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.LOW_CVR,
                severity=IssueSeverity.WARNING,
                description=f"CVR of {request.current_cvr}% has room for improvement",
                likely_cause="Ad copy may overpromise or LP underdelivers",
                impact="Leaving conversions on the table",
            ))
        
        # CPA analysis
        if request.current_cpa > request.target_cpa * 1.5:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.HIGH_CPA,
                severity=IssueSeverity.CRITICAL,
                description=f"CPA of ${request.current_cpa} is 50%+ above target",
                likely_cause="Combination of CTR and CVR issues, or wrong audience",
                impact="Unprofitable unit economics",
            ))
        elif request.current_cpa > request.target_cpa:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.HIGH_CPA,
                severity=IssueSeverity.WARNING,
                description=f"CPA of ${request.current_cpa} is above ${request.target_cpa} target",
                likely_cause="Optimization needed on ad or landing page",
                impact="Marginal profitability",
            ))
        
        # Frequency analysis
        if request.frequency > 3.0:
            diagnoses.append(Diagnosis(
                issue=PerformanceIssue.HIGH_FREQUENCY,
                severity=IssueSeverity.WARNING,
                description=f"Frequency of {request.frequency} indicates ad fatigue",
                likely_cause="Audience too narrow or budget too high for audience size",
                impact="Declining performance, wasted spend on repeat views",
            ))
        
        return diagnoses
    
    def _generate_improvements(self, request: IterationRequest, diagnoses: list[Diagnosis]) -> list[ImprovedVariant]:
        improvements = []
        issues = [d.issue for d in diagnoses]
        
        # Headline improvements for CTR issues
        if PerformanceIssue.LOW_CTR in issues:
            improvements.append(ImprovedVariant(
                element="headline",
                original=request.headline,
                improved=self._improve_headline(request.headline),
                rationale="Added urgency and specificity to increase scroll-stopping power",
                expected_improvement="+20-40% CTR",
            ))
        
        # Primary text improvements for CVR issues
        if PerformanceIssue.LOW_CVR in issues:
            improvements.append(ImprovedVariant(
                element="primary_text",
                original=request.primary_text[:100] + "..." if len(request.primary_text) > 100 else request.primary_text,
                improved=self._improve_primary_text(request.primary_text),
                rationale="Strengthened value proposition and added social proof",
                expected_improvement="+15-30% CVR",
            ))
        
        # CTA improvements
        if any(i in issues for i in [PerformanceIssue.LOW_CVR, PerformanceIssue.HIGH_CPA]):
            improvements.append(ImprovedVariant(
                element="cta",
                original=request.cta,
                improved=self._improve_cta(request.cta),
                rationale="Made CTA more action-oriented and reduced friction",
                expected_improvement="+10-20% click-through on CTA",
            ))
        
        return improvements
    
    def _improve_headline(self, headline: str) -> str:
        """Generate improved headline."""
        # Simple improvements - would use Claude in production
        improvements = [
            f"🔥 {headline}",
            f"Stop. {headline}",
            f"Finally: {headline}",
            f"[New] {headline}",
        ]
        # Pick based on original length
        if len(headline) < 30:
            return improvements[0]
        return improvements[1]
    
    def _improve_primary_text(self, text: str) -> str:
        """Generate improved primary text."""
        # Add social proof and urgency
        improved = text
        if "trusted" not in text.lower():
            improved = f"Trusted by 1,000+ users. {text}"
        if "today" not in text.lower() and "now" not in text.lower():
            improved = f"{improved} Start today."
        return improved[:150] + "..." if len(improved) > 150 else improved
    
    def _improve_cta(self, cta: str) -> str:
        """Generate improved CTA."""
        cta_upgrades = {
            "Learn More": "See How It Works",
            "Sign Up": "Start Free Trial",
            "Get Started": "Try Free for 14 Days",
            "Buy Now": "Get Instant Access",
            "Subscribe": "Join Free",
        }
        return cta_upgrades.get(cta, f"Get {cta.split()[-1] if cta.split() else 'Started'} Free")
    
    def _prioritize_fixes(self, diagnoses: list[Diagnosis]) -> list[str]:
        fixes = []
        critical = [d for d in diagnoses if d.severity == IssueSeverity.CRITICAL]
        
        if any(d.issue == PerformanceIssue.LOW_CTR for d in critical):
            fixes.append("1. Fix CTR first - test new headlines immediately")
        
        if any(d.issue == PerformanceIssue.LOW_CVR for d in critical):
            fixes.append("2. Check landing page - ensure message match with ad")
        
        if any(d.issue == PerformanceIssue.HIGH_CPA for d in critical):
            fixes.append("3. Review audience targeting - may be too broad or wrong fit")
        
        if not fixes:
            fixes.append("Performance is acceptable - focus on incremental testing")
        
        return fixes
    
    def _create_roadmap(self, diagnoses: list[Diagnosis], improved: list[ImprovedVariant]) -> list[str]:
        return [
            "Week 1: Implement headline changes, A/B test vs control",
            "Week 2: Apply winning headline, test primary text",
            "Week 3: Test CTA variations on winning combination",
            "Week 4: Review results, scale winners or iterate again",
        ]
    
    def _identify_quick_wins(self, request: IterationRequest, diagnoses: list[Diagnosis]) -> list[str]:
        wins = []
        
        if "?" not in request.headline:
            wins.append("Add a question to your headline - questions increase engagement")
        
        if len(request.primary_text) > 200:
            wins.append("Shorten primary text - mobile users don't read long copy")
        
        if request.cta in ["Learn More", "Click Here"]:
            wins.append("Use specific CTA like 'Start Free Trial' instead of generic 'Learn More'")
        
        if request.frequency > 2.5:
            wins.append("Expand audience size or add new ad creative to reduce fatigue")
        
        return wins
    
    def _estimate_improvement(self, diagnoses: list[Diagnosis]) -> str:
        critical_count = sum(1 for d in diagnoses if d.severity == IssueSeverity.CRITICAL)
        
        if critical_count >= 2:
            return "Potential 40-60% improvement in CPA with recommended changes"
        elif critical_count == 1:
            return "Potential 20-40% improvement in primary metric"
        else:
            return "Potential 10-20% incremental improvement"


_instance: Optional[IterationAssistant] = None

def get_iteration_assistant() -> IterationAssistant:
    global _instance
    if _instance is None:
        _instance = IterationAssistant()
    return _instance
