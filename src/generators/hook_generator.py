# src/generators/hook_generator.py
"""Hook Generator - Creates scroll-stopping ad hooks.

Generates attention-grabbing first lines using proven patterns:
- Questions, Statistics, Controversy, Pain Points
- Social Proof, Urgency, Curiosity Gap, Direct Benefit
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HookPattern(str, Enum):
    QUESTION = "question"
    STATISTIC = "statistic"
    CONTROVERSY = "controversy"
    PAIN_POINT = "pain_point"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency"
    CURIOSITY_GAP = "curiosity_gap"
    DIRECT_BENEFIT = "direct_benefit"
    STORY = "story"
    COMMAND = "command"


class Hook(BaseModel):
    text: str
    pattern: HookPattern
    character_count: int
    power_words: list[str] = Field(default_factory=list)
    score: int = Field(ge=0, le=100)
    explanation: str = ""


class HookGeneratorRequest(BaseModel):
    product_name: str
    product_description: str
    target_audience: str
    pain_points: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    tone: str = "professional"
    include_emojis: bool = False
    num_hooks: int = 10


class HookGeneratorResult(BaseModel):
    hooks: list[Hook]
    best_hook: Optional[Hook] = None
    pattern_distribution: dict[str, int] = Field(default_factory=dict)
    avg_score: float = 0
    recommendations: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        return f"Generated {len(self.hooks)} hooks (avg score: {self.avg_score:.0f}/100)"


POWER_WORDS = {
    "urgency": ["now", "today", "instantly", "fast", "quick", "limited", "deadline"],
    "exclusivity": ["secret", "exclusive", "insider", "hidden", "private"],
    "curiosity": ["discover", "reveal", "uncover", "surprising", "shocking"],
    "value": ["free", "bonus", "save", "discount", "best", "proven"],
    "emotion": ["amazing", "incredible", "transform", "revolutionary", "breakthrough"],
    "fear": ["mistake", "avoid", "stop", "warning", "fail", "miss", "losing"],
    "results": ["results", "success", "achieve", "boost", "increase", "double"],
}


class HookGenerator:
    def __init__(self):
        self._all_power_words = set()
        for words in POWER_WORDS.values():
            self._all_power_words.update(words)
    
    async def generate(self, request: HookGeneratorRequest) -> HookGeneratorResult:
        logger.info(f"Generating {request.num_hooks} hooks for {request.product_name}...")
        
        hooks = []
        patterns = list(HookPattern)
        
        for i in range(request.num_hooks):
            pattern = patterns[i % len(patterns)]
            hook = self._generate_hook(request, pattern, i)
            hooks.append(hook)
        
        hooks.sort(key=lambda h: h.score, reverse=True)
        
        pattern_dist = {}
        for hook in hooks:
            pattern_dist[hook.pattern.value] = pattern_dist.get(hook.pattern.value, 0) + 1
        
        avg_score = sum(h.score for h in hooks) / len(hooks) if hooks else 0
        
        return HookGeneratorResult(
            hooks=hooks,
            best_hook=hooks[0] if hooks else None,
            pattern_distribution=pattern_dist,
            avg_score=avg_score,
            recommendations=self._get_recommendations(hooks),
        )
    
    def _generate_hook(self, req: HookGeneratorRequest, pattern: HookPattern, idx: int) -> Hook:
        pain = req.pain_points[0] if req.pain_points else "struggling with results"
        benefit = req.benefits[0] if req.benefits else "achieve your goals"
        
        templates = {
            HookPattern.QUESTION: [
                f"Still {pain}?",
                f"What if you could {benefit} in 30 days?",
                f"Why are {req.target_audience} switching to {req.product_name}?",
                f"Tired of {pain}?",
            ],
            HookPattern.STATISTIC: [
                f"87% of {req.target_audience} don't know this",
                f"1,000+ {req.target_audience} already use {req.product_name}",
                f"Save 10+ hours every week with {req.product_name}",
                f"3x faster than traditional methods",
            ],
            HookPattern.CONTROVERSY: [
                f"Stop {pain}. Here's why it's wrong.",
                f"Everything you know about {pain} is outdated",
                f"Unpopular opinion: {req.product_name} isn't for everyone",
                f"The {pain} industry doesn't want you to know this",
            ],
            HookPattern.PAIN_POINT: [
                f"Stop wasting time on {pain}",
                f"{pain.capitalize()} is killing your results",
                f"The real reason you're {pain}",
                f"If you're {pain}, read this",
            ],
            HookPattern.SOCIAL_PROOF: [
                f"See why 1,000+ {req.target_audience} chose {req.product_name}",
                f"Top companies use this to {benefit}",
                f"Join thousands who already {benefit}",
                f"Rated #1 by {req.target_audience}",
            ],
            HookPattern.URGENCY: [
                f"Last chance to {benefit}",
                f"Only 48 hours left",
                f"Before Friday: {benefit}",
                f"Don't miss this opportunity to {benefit}",
            ],
            HookPattern.CURIOSITY_GAP: [
                f"The simple trick to {benefit} nobody talks about",
                f"I discovered how to {benefit}. Here's the secret.",
                f"This one change transformed everything",
                f"What top performers know about {benefit}",
            ],
            HookPattern.DIRECT_BENEFIT: [
                f"{benefit.capitalize()} in 30 days or less",
                f"Finally, {benefit} without the hassle",
                f"The fastest way to {benefit}",
                f"{benefit.capitalize()}. Guaranteed.",
            ],
            HookPattern.STORY: [
                f"I was {pain}. Then I found {req.product_name}.",
                f"6 months ago, I couldn't {benefit}. Now...",
                f"From {pain} to {benefit} in 30 days",
                f"My {pain} story (and how I fixed it)",
            ],
            HookPattern.COMMAND: [
                f"Stop {pain}. Start winning.",
                f"Try this before your next launch",
                f"Read this if you want to {benefit}",
                f"Watch how {req.product_name} works",
            ],
        }
        
        options = templates.get(pattern, [f"Check out {req.product_name}"])
        text = options[idx % len(options)]
        
        if req.include_emojis:
            emojis = {"question": "🤔", "statistic": "📊", "controversy": "🔥", 
                     "pain_point": "😫", "social_proof": "⭐", "urgency": "⚡",
                     "curiosity_gap": "👀", "direct_benefit": "✅", "story": "📖", "command": "👉"}
            text = f"{emojis.get(pattern.value, '')} {text}"
        
        power_words = [w for w in self._all_power_words if w in text.lower()]
        score = 60 + len(power_words) * 5 + (10 if len(text) < 80 else 0)
        score = min(score, 100)
        
        return Hook(
            text=text,
            pattern=pattern,
            character_count=len(text),
            power_words=power_words,
            score=score,
            explanation=f"Uses {pattern.value} pattern to capture attention",
        )
    
    def _get_recommendations(self, hooks: list[Hook]) -> list[str]:
        recs = []
        if hooks:
            best = hooks[0]
            recs.append(f"Your strongest hook uses '{best.pattern.value}' - create more variations")
        recs.append("Test 3-5 hooks in your first campaign to find what resonates")
        recs.append("Question and pain point hooks typically have highest engagement")
        return recs
    
    def get_patterns(self) -> list[dict]:
        return [{"id": p.value, "name": p.value.replace("_", " ").title()} for p in HookPattern]
    
    def get_power_words(self) -> dict:
        return POWER_WORDS


_instance: Optional[HookGenerator] = None

def get_hook_generator() -> HookGenerator:
    global _instance
    if _instance is None:
        _instance = HookGenerator()
    return _instance
