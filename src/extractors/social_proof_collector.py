# src/extractors/social_proof_collector.py
"""Social Proof Collector - Gathers and formats social proof for ads.

Collects:
- Customer testimonials
- Review snippets (G2, Capterra, etc.)
- Social media mentions
- Stats and metrics
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProofType(str, Enum):
    TESTIMONIAL = "testimonial"
    REVIEW = "review"
    STAT = "stat"
    LOGO = "logo"
    AWARD = "award"
    MEDIA_MENTION = "media_mention"
    SOCIAL_POST = "social_post"


class SocialProof(BaseModel):
    type: ProofType
    content: str
    source: str
    author: Optional[str] = None
    rating: Optional[float] = None
    verified: bool = False
    ad_ready: str  # Formatted for ad copy
    character_count: int


class ProofCollection(BaseModel):
    proofs: list[SocialProof]
    best_testimonial: Optional[SocialProof] = None
    best_stat: Optional[SocialProof] = None
    ad_snippets: list[str]
    trust_score: int = Field(ge=0, le=100)
    recommendations: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        return f"Collected {len(self.proofs)} proof elements | Trust score: {self.trust_score}/100"


class ProofRequest(BaseModel):
    brand_name: str
    brand_url: str
    product_description: str
    existing_testimonials: list[str] = Field(default_factory=list)
    user_count: Optional[int] = None
    rating: Optional[float] = None
    notable_customers: list[str] = Field(default_factory=list)


class SocialProofCollector:
    def __init__(self):
        pass
    
    async def collect(self, request: ProofRequest) -> ProofCollection:
        logger.info(f"Collecting social proof for {request.brand_name}...")
        
        proofs = []
        
        # Process existing testimonials
        for testimonial in request.existing_testimonials:
            proof = self._process_testimonial(testimonial)
            proofs.append(proof)
        
        # Generate stat-based proofs
        if request.user_count:
            proofs.append(self._create_user_stat(request.user_count, request.brand_name))
        
        if request.rating:
            proofs.append(self._create_rating_proof(request.rating))
        
        # Process notable customers
        for customer in request.notable_customers:
            proofs.append(self._create_logo_proof(customer))
        
        # If no proofs, create suggestions
        if not proofs:
            proofs = self._create_suggested_proofs(request)
        
        # Find best ones
        testimonials = [p for p in proofs if p.type == ProofType.TESTIMONIAL]
        stats = [p for p in proofs if p.type == ProofType.STAT]
        
        best_testimonial = max(testimonials, key=lambda p: len(p.content)) if testimonials else None
        best_stat = max(stats, key=lambda p: p.character_count) if stats else None
        
        # Generate ad snippets
        ad_snippets = self._generate_ad_snippets(proofs, request)
        
        # Calculate trust score
        trust_score = self._calculate_trust_score(proofs, request)
        
        # Recommendations
        recommendations = self._generate_recommendations(proofs, request)
        
        return ProofCollection(
            proofs=proofs,
            best_testimonial=best_testimonial,
            best_stat=best_stat,
            ad_snippets=ad_snippets,
            trust_score=trust_score,
            recommendations=recommendations,
        )
    
    def _process_testimonial(self, testimonial: str) -> SocialProof:
        """Process a testimonial into ad-ready format."""
        # Truncate long testimonials
        short = testimonial[:100] + "..." if len(testimonial) > 100 else testimonial
        
        # Format for ads
        ad_ready = f'"{short}"'
        
        return SocialProof(
            type=ProofType.TESTIMONIAL,
            content=testimonial,
            source="Customer",
            ad_ready=ad_ready,
            character_count=len(ad_ready),
            verified=False,
        )
    
    def _create_user_stat(self, user_count: int, brand_name: str) -> SocialProof:
        """Create user count stat."""
        # Format number nicely
        if user_count >= 1000000:
            formatted = f"{user_count // 1000000}M+"
        elif user_count >= 1000:
            formatted = f"{user_count // 1000}K+"
        else:
            formatted = f"{user_count}+"
        
        content = f"{formatted} users trust {brand_name}"
        
        return SocialProof(
            type=ProofType.STAT,
            content=content,
            source="Internal",
            ad_ready=content,
            character_count=len(content),
            verified=True,
        )
    
    def _create_rating_proof(self, rating: float) -> SocialProof:
        """Create rating proof."""
        stars = "⭐" * int(rating)
        content = f"Rated {rating}/5 {stars}"
        
        return SocialProof(
            type=ProofType.REVIEW,
            content=content,
            source="Customer Reviews",
            rating=rating,
            ad_ready=content,
            character_count=len(content),
            verified=False,
        )
    
    def _create_logo_proof(self, customer: str) -> SocialProof:
        """Create logo/customer proof."""
        content = f"Trusted by {customer}"
        
        return SocialProof(
            type=ProofType.LOGO,
            content=content,
            source=customer,
            ad_ready=content,
            character_count=len(content),
            verified=True,
        )
    
    def _create_suggested_proofs(self, request: ProofRequest) -> list[SocialProof]:
        """Create template proofs when none exist."""
        return [
            SocialProof(
                type=ProofType.STAT,
                content="Join thousands of happy users",
                source="Template",
                ad_ready="Join thousands of happy users",
                character_count=30,
                verified=False,
            ),
            SocialProof(
                type=ProofType.TESTIMONIAL,
                content=f"[Collect testimonials from your {request.product_description} users]",
                source="Suggested",
                ad_ready='"This changed everything for me" - Happy User',
                character_count=45,
                verified=False,
            ),
        ]
    
    def _generate_ad_snippets(self, proofs: list[SocialProof], request: ProofRequest) -> list[str]:
        """Generate ready-to-use ad snippets."""
        snippets = []
        
        # User count snippet
        if request.user_count:
            if request.user_count >= 1000:
                snippets.append(f"Join {request.user_count:,}+ users who already love {request.brand_name}")
            else:
                snippets.append(f"Trusted by {request.user_count}+ users")
        
        # Rating snippet
        if request.rating and request.rating >= 4.0:
            snippets.append(f"⭐ {request.rating}/5 rating from real users")
        
        # Notable customers
        if request.notable_customers:
            if len(request.notable_customers) >= 3:
                top3 = request.notable_customers[:3]
                snippets.append(f"Used by {', '.join(top3)} and more")
            elif request.notable_customers:
                snippets.append(f"Trusted by {request.notable_customers[0]}")
        
        # Testimonial snippets
        for proof in proofs:
            if proof.type == ProofType.TESTIMONIAL and len(proof.content) < 80:
                snippets.append(f'"{proof.content}"')
        
        # Default if empty
        if not snippets:
            snippets = [
                f"See why people love {request.brand_name}",
                "Join our growing community",
                "Try it free today",
            ]
        
        return snippets[:5]  # Return top 5
    
    def _calculate_trust_score(self, proofs: list[SocialProof], request: ProofRequest) -> int:
        """Calculate overall trust score."""
        score = 30  # Base score
        
        # User count bonus
        if request.user_count:
            if request.user_count >= 10000:
                score += 25
            elif request.user_count >= 1000:
                score += 15
            elif request.user_count >= 100:
                score += 10
        
        # Rating bonus
        if request.rating:
            if request.rating >= 4.5:
                score += 20
            elif request.rating >= 4.0:
                score += 15
            elif request.rating >= 3.5:
                score += 10
        
        # Notable customers bonus
        score += min(len(request.notable_customers) * 5, 15)
        
        # Testimonials bonus
        testimonials = [p for p in proofs if p.type == ProofType.TESTIMONIAL]
        score += min(len(testimonials) * 5, 15)
        
        # Verified proofs bonus
        verified = sum(1 for p in proofs if p.verified)
        score += min(verified * 3, 10)
        
        return min(score, 100)
    
    def _generate_recommendations(self, proofs: list[SocialProof], request: ProofRequest) -> list[str]:
        """Generate recommendations to improve social proof."""
        recs = []
        
        if not request.existing_testimonials:
            recs.append("Collect 3-5 customer testimonials with specific results")
        
        if not request.user_count:
            recs.append("Add user count - even 'Trusted by 100+ users' adds credibility")
        
        if not request.rating:
            recs.append("Add G2, Capterra, or Trustpilot rating to ads")
        
        if not request.notable_customers:
            recs.append("Feature recognizable customer logos if you have B2B clients")
        
        recs.append("Use specific numbers: '47% faster' beats 'much faster'")
        recs.append("Video testimonials convert 2x better than text")
        
        return recs
    
    def format_for_ad(self, proof: SocialProof, max_length: int = 125) -> str:
        """Format proof for ad copy with length limit."""
        text = proof.ad_ready
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text


_instance: Optional[SocialProofCollector] = None

def get_social_proof_collector() -> SocialProofCollector:
    global _instance
    if _instance is None:
        _instance = SocialProofCollector()
    return _instance
