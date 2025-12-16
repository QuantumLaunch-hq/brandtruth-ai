# tests/unit/test_social_proof_collector.py
"""Unit tests for Social Proof Collector (Slice 23)."""

import pytest
from src.extractors.social_proof_collector import (
    SocialProofCollector, SocialProofRequest, ProofType,
    get_social_proof_collector,
)


class TestSocialProofCollector:
    """Test SocialProofCollector class."""

    @pytest.fixture
    def collector(self):
        return SocialProofCollector()

    @pytest.fixture
    def sample_request(self):
        return SocialProofRequest(
            brand_name="Careerfied",
            brand_url="https://careerfied.ai",
            product_description="AI-powered resume builder",
            existing_testimonials=[
                "This helped me land my dream job!",
                "Got 3 interviews in the first week",
            ],
            user_count=1500,
            rating=4.8,
            notable_customers=["Google", "Meta", "Microsoft"],
        )

    @pytest.mark.asyncio
    async def test_collect_returns_proofs(self, collector, sample_request):
        """Test proofs are collected."""
        result = await collector.collect(sample_request)
        assert len(result.proofs) > 0

    @pytest.mark.asyncio
    async def test_collect_returns_trust_score(self, collector, sample_request):
        """Test trust score is calculated."""
        result = await collector.collect(sample_request)
        assert 0 <= result.trust_score <= 100

    @pytest.mark.asyncio
    async def test_collect_returns_ad_snippets(self, collector, sample_request):
        """Test ad snippets are generated."""
        result = await collector.collect(sample_request)
        assert len(result.ad_snippets) > 0

    @pytest.mark.asyncio
    async def test_collect_returns_recommendations(self, collector, sample_request):
        """Test recommendations are provided."""
        result = await collector.collect(sample_request)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_collect_returns_best_testimonial(self, collector, sample_request):
        """Test best testimonial is selected."""
        result = await collector.collect(sample_request)
        assert result.best_testimonial is not None

    @pytest.mark.asyncio
    async def test_collect_returns_best_stat(self, collector, sample_request):
        """Test best stat is selected."""
        result = await collector.collect(sample_request)
        assert result.best_stat is not None

    @pytest.mark.asyncio
    async def test_proofs_have_required_fields(self, collector, sample_request):
        """Test proofs have required fields."""
        result = await collector.collect(sample_request)
        for proof in result.proofs:
            assert proof.type in ProofType
            assert proof.content
            assert proof.source
            assert proof.ad_ready

    @pytest.mark.asyncio
    async def test_testimonials_converted_to_proofs(self, collector, sample_request):
        """Test testimonials are converted to proofs."""
        result = await collector.collect(sample_request)
        testimonial_proofs = [p for p in result.proofs if p.type == ProofType.TESTIMONIAL]
        assert len(testimonial_proofs) >= len(sample_request.existing_testimonials)

    @pytest.mark.asyncio
    async def test_user_count_converted_to_proof(self, collector, sample_request):
        """Test user count is converted to proof."""
        result = await collector.collect(sample_request)
        stat_proofs = [p for p in result.proofs if p.type == ProofType.STAT]
        assert len(stat_proofs) > 0

    @pytest.mark.asyncio
    async def test_rating_converted_to_proof(self, collector, sample_request):
        """Test rating is converted to proof."""
        result = await collector.collect(sample_request)
        review_proofs = [p for p in result.proofs if p.type == ProofType.REVIEW]
        assert len(review_proofs) > 0

    @pytest.mark.asyncio
    async def test_notable_customers_converted_to_proofs(self, collector, sample_request):
        """Test notable customers are converted to proofs."""
        result = await collector.collect(sample_request)
        logo_proofs = [p for p in result.proofs if p.type == ProofType.LOGO]
        assert len(logo_proofs) > 0

    @pytest.mark.asyncio
    async def test_high_trust_score_with_full_data(self, collector, sample_request):
        """Test high trust score with complete data."""
        result = await collector.collect(sample_request)
        assert result.trust_score >= 70  # Has user count, rating, customers, testimonials

    @pytest.mark.asyncio
    async def test_low_trust_score_with_minimal_data(self, collector):
        """Test low trust score with minimal data."""
        request = SocialProofRequest(
            brand_name="Test",
            product_description="Test product",
        )
        result = await collector.collect(request)
        assert result.trust_score < 50

    @pytest.mark.asyncio
    async def test_ad_ready_format_truncated(self, collector):
        """Test ad_ready truncates long testimonials."""
        request = SocialProofRequest(
            brand_name="Test",
            product_description="Test",
            existing_testimonials=[
                "This is a very long testimonial that goes on and on about how amazing the product is and how it changed my life and helped me achieve all my goals and dreams in ways I never thought possible."
            ],
        )
        result = await collector.collect(request)
        testimonial_proofs = [p for p in result.proofs if p.type == ProofType.TESTIMONIAL]
        if testimonial_proofs:
            assert len(testimonial_proofs[0].ad_ready) <= 110  # 100 + quotes + ellipsis

    @pytest.mark.asyncio
    async def test_user_count_formatting(self, collector):
        """Test user count is formatted correctly."""
        request = SocialProofRequest(
            brand_name="Test",
            product_description="Test",
            user_count=1500000,  # 1.5M
        )
        result = await collector.collect(request)
        stat_proofs = [p for p in result.proofs if p.type == ProofType.STAT]
        assert any("M" in p.ad_ready or "million" in p.ad_ready.lower() for p in stat_proofs)

    def test_singleton_pattern(self):
        """Test get_social_proof_collector returns singleton."""
        c1 = get_social_proof_collector()
        c2 = get_social_proof_collector()
        assert c1 is c2


class TestProofType:
    """Test ProofType enum."""

    def test_all_types_defined(self):
        """Test all proof types exist."""
        assert ProofType.TESTIMONIAL.value == "testimonial"
        assert ProofType.REVIEW.value == "review"
        assert ProofType.STAT.value == "stat"
        assert ProofType.LOGO.value == "logo"
        assert ProofType.AWARD.value == "award"
        assert ProofType.MEDIA_MENTION.value == "media_mention"
