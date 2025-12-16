# src/analyzers/budget_simulator.py
"""Budget Simulator - Predicts ad performance based on budget.

Provides:
- Recommended daily/monthly budget
- Expected reach, impressions, clicks
- Estimated CPA/ROAS
- Break-even analysis
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Industry(str, Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    AGENCY = "agency"
    CONSUMER_APP = "consumer_app"
    OTHER = "other"


class CampaignGoal(str, Enum):
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    LEADS = "leads"
    SALES = "sales"
    APP_INSTALLS = "app_installs"


class BudgetTier(str, Enum):
    STARTER = "starter"
    GROWTH = "growth"
    SCALE = "scale"
    ENTERPRISE = "enterprise"


class BudgetSimulation(BaseModel):
    daily_budget: float
    monthly_budget: float
    tier: BudgetTier
    expected_impressions: int
    expected_reach: int
    expected_clicks: int
    expected_ctr: float
    expected_cpc: float
    expected_conversions: int
    expected_cpa: float
    expected_roas: float
    confidence_level: str
    break_even_days: int
    recommendations: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        return f"${self.daily_budget}/day → ~{self.expected_conversions} conversions @ ${self.expected_cpa:.2f} CPA"


class BudgetRequest(BaseModel):
    industry: Industry
    goal: CampaignGoal
    product_price: float = 99.0
    target_monthly_conversions: int = 50
    target_cpa: Optional[float] = None


# Industry benchmarks (Meta Ads averages)
INDUSTRY_BENCHMARKS = {
    Industry.SAAS: {"cpm": 15.0, "ctr": 0.9, "cvr": 2.5, "avg_cpa": 150},
    Industry.ECOMMERCE: {"cpm": 12.0, "ctr": 1.2, "cvr": 3.0, "avg_cpa": 45},
    Industry.FINTECH: {"cpm": 25.0, "ctr": 0.7, "cvr": 1.5, "avg_cpa": 200},
    Industry.HEALTHCARE: {"cpm": 18.0, "ctr": 0.8, "cvr": 2.0, "avg_cpa": 120},
    Industry.EDUCATION: {"cpm": 10.0, "ctr": 1.0, "cvr": 3.5, "avg_cpa": 80},
    Industry.AGENCY: {"cpm": 20.0, "ctr": 0.8, "cvr": 2.0, "avg_cpa": 180},
    Industry.CONSUMER_APP: {"cpm": 8.0, "ctr": 1.5, "cvr": 5.0, "avg_cpa": 25},
    Industry.OTHER: {"cpm": 14.0, "ctr": 1.0, "cvr": 2.5, "avg_cpa": 100},
}


class BudgetSimulator:
    def __init__(self):
        self.benchmarks = INDUSTRY_BENCHMARKS
    
    async def simulate(self, request: BudgetRequest) -> BudgetSimulation:
        logger.info(f"Simulating budget for {request.industry.value} / {request.goal.value}")
        
        benchmarks = self.benchmarks.get(request.industry, self.benchmarks[Industry.OTHER])
        
        # Calculate required budget based on target conversions
        target_cpa = request.target_cpa or benchmarks["avg_cpa"]
        required_monthly = request.target_monthly_conversions * target_cpa
        daily_budget = required_monthly / 30
        
        # Determine tier
        if daily_budget < 20:
            tier = BudgetTier.STARTER
            daily_budget = max(daily_budget, 10)  # Minimum viable
        elif daily_budget < 100:
            tier = BudgetTier.GROWTH
        elif daily_budget < 500:
            tier = BudgetTier.SCALE
        else:
            tier = BudgetTier.ENTERPRISE
        
        monthly_budget = daily_budget * 30
        
        # Calculate expected metrics
        cpm = benchmarks["cpm"]
        ctr = benchmarks["ctr"] / 100
        cvr = benchmarks["cvr"] / 100
        
        impressions = int((monthly_budget / cpm) * 1000)
        reach = int(impressions * 0.4)  # ~40% reach to impression ratio
        clicks = int(impressions * ctr)
        conversions = int(clicks * cvr)
        
        cpc = monthly_budget / max(clicks, 1)
        actual_cpa = monthly_budget / max(conversions, 1)
        
        # Calculate ROAS
        revenue = conversions * request.product_price
        roas = revenue / monthly_budget if monthly_budget > 0 else 0
        
        # Break-even analysis
        break_even_conversions = monthly_budget / request.product_price
        break_even_days = int((break_even_conversions / max(conversions, 1)) * 30)
        
        # Confidence based on budget level
        if tier == BudgetTier.STARTER:
            confidence = "Low - Limited data for optimization"
        elif tier == BudgetTier.GROWTH:
            confidence = "Medium - Enough for basic optimization"
        else:
            confidence = "High - Sufficient for A/B testing and scaling"
        
        recommendations = self._get_recommendations(tier, roas, request)
        
        return BudgetSimulation(
            daily_budget=round(daily_budget, 2),
            monthly_budget=round(monthly_budget, 2),
            tier=tier,
            expected_impressions=impressions,
            expected_reach=reach,
            expected_clicks=clicks,
            expected_ctr=round(ctr * 100, 2),
            expected_cpc=round(cpc, 2),
            expected_conversions=conversions,
            expected_cpa=round(actual_cpa, 2),
            expected_roas=round(roas, 2),
            confidence_level=confidence,
            break_even_days=min(break_even_days, 90),
            recommendations=recommendations,
        )
    
    def _get_recommendations(self, tier: BudgetTier, roas: float, request: BudgetRequest) -> list[str]:
        recs = []
        
        if tier == BudgetTier.STARTER:
            recs.append("Start with 1-2 ad sets to avoid spreading budget too thin")
            recs.append("Focus on one platform (Meta) before expanding")
            recs.append("Run for 7-14 days minimum before making optimization decisions")
        elif tier == BudgetTier.GROWTH:
            recs.append("Test 3-5 ad variations to find winners")
            recs.append("Consider expanding to additional placements")
        else:
            recs.append("Implement A/B testing for continuous optimization")
            recs.append("Consider lookalike audiences for scaling")
        
        if roas < 1:
            recs.append(f"Target CPA of ${request.product_price * 0.3:.0f} or less for profitability")
        elif roas > 3:
            recs.append("Strong unit economics - consider increasing budget to scale")
        
        return recs
    
    def get_benchmarks(self, industry: Optional[Industry] = None) -> dict:
        if industry:
            return {industry.value: self.benchmarks.get(industry, {})}
        return {k.value: v for k, v in self.benchmarks.items()}


_instance: Optional[BudgetSimulator] = None

def get_budget_simulator() -> BudgetSimulator:
    global _instance
    if _instance is None:
        _instance = BudgetSimulator()
    return _instance
