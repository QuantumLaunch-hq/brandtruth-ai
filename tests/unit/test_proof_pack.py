# tests/unit/test_proof_pack.py
"""Unit tests for Proof Pack Generator (Slice 15)."""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.proof_pack import (
    ProofPackGenerator,
    ProofPack,
    ClaimVerification,
    RegulatoryCheck,
    BrandSafetyCheck,
    ApprovalRecord,
    ComplianceStatus,
    ClaimRisk,
    RegulationType,
    ProofPackConfig,
    get_proof_pack_generator,
)


class TestComplianceStatus:
    """Tests for ComplianceStatus enum."""
    
    def test_all_statuses_exist(self):
        """Test all statuses exist."""
        assert ComplianceStatus.PASS.value == "pass"
        assert ComplianceStatus.WARNING.value == "warning"
        assert ComplianceStatus.FAIL.value == "fail"
        assert ComplianceStatus.REVIEW.value == "review"


class TestClaimRisk:
    """Tests for ClaimRisk enum."""
    
    def test_all_risks_exist(self):
        """Test all risk levels exist."""
        assert ClaimRisk.LOW.value == "low"
        assert ClaimRisk.MEDIUM.value == "medium"
        assert ClaimRisk.HIGH.value == "high"
        assert ClaimRisk.CRITICAL.value == "critical"


class TestClaimVerification:
    """Tests for ClaimVerification model."""
    
    def test_create_verification(self):
        """Test creating claim verification."""
        verification = ClaimVerification(
            claim_text="Join 10,000+ users",
            source_text="Based on user surveys",
            verification_status=ComplianceStatus.PASS,
            risk_level=ClaimRisk.LOW,
            notes="Claim verified",
        )
        
        assert verification.claim_text == "Join 10,000+ users"
        assert verification.verification_status == ComplianceStatus.PASS
        assert verification.requires_disclaimer is False
    
    def test_verification_with_disclaimer(self):
        """Test verification requiring disclaimer."""
        verification = ClaimVerification(
            claim_text="Guaranteed results",
            source_text="",
            verification_status=ComplianceStatus.WARNING,
            risk_level=ClaimRisk.HIGH,
            requires_disclaimer=True,
            suggested_disclaimer="Results may vary",
        )
        
        assert verification.requires_disclaimer is True
        assert verification.suggested_disclaimer == "Results may vary"


class TestRegulatoryCheck:
    """Tests for RegulatoryCheck model."""
    
    def test_create_check(self):
        """Test creating regulatory check."""
        check = RegulatoryCheck(
            regulation=RegulationType.FTC,
            regulation_name="FTC Advertising Guidelines",
            status=ComplianceStatus.PASS,
            requirements_met=["No deceptive patterns"],
            requirements_failed=[],
            recommendations=[],
        )
        
        assert check.regulation == RegulationType.FTC
        assert check.status == ComplianceStatus.PASS
        assert len(check.requirements_met) == 1


class TestBrandSafetyCheck:
    """Tests for BrandSafetyCheck model."""
    
    def test_create_check(self):
        """Test creating brand safety check."""
        check = BrandSafetyCheck(
            category="Content Appropriateness",
            status=ComplianceStatus.PASS,
            details="No inappropriate content detected",
            risk_factors=[],
        )
        
        assert check.category == "Content Appropriateness"
        assert check.status == ComplianceStatus.PASS


class TestProofPackConfig:
    """Tests for ProofPackConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ProofPackConfig()
        
        assert config.include_claims is True
        assert config.include_regulatory is True
        assert config.include_brand_safety is True
        assert RegulationType.FTC in config.regulations_to_check
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ProofPackConfig(
            include_claims=False,
            output_format="pdf",
        )
        
        assert config.include_claims is False
        assert config.output_format == "pdf"


class TestProofPackGenerator:
    """Tests for ProofPackGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return ProofPackGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_basic_pack(self, generator):
        """Test generating basic proof pack."""
        pack = await generator.generate(
            ad_id="test_001",
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            headline="Test Headline",
            primary_text="Test body text",
            cta="Learn More",
        )
        
        assert isinstance(pack, ProofPack)
        assert pack.ad_id == "test_001"
        assert pack.brand_name == "Test Brand"
        assert pack.overall_compliance in ComplianceStatus
    
    @pytest.mark.asyncio
    async def test_generate_with_claims(self, generator):
        """Test generating pack with claims."""
        claims = [
            {"claim": "Join 10,000+ users", "source_text": "User surveys", "risk_level": "low"},
            {"claim": "AI-powered", "source_text": "Uses GPT-4", "risk_level": "low"},
            {"claim": "Guaranteed results", "source_text": "", "risk_level": "high"},
        ]
        
        pack = await generator.generate(
            ad_id="test_002",
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            headline="Test Headline",
            primary_text="Test body",
            cta="Get Started",
            claims=claims,
        )
        
        assert pack.total_claims == 3
        assert pack.verified_claims >= 0
        assert pack.high_risk_claims >= 1  # "Guaranteed results" is high risk
    
    @pytest.mark.asyncio
    async def test_claim_verification(self, generator):
        """Test claim verification logic."""
        claims = [
            {"claim": "Verified claim", "source_text": "Official source with sufficient detail", "risk_level": "low"},
            {"claim": "Unverified claim", "source_text": "", "risk_level": "medium"},
        ]
        
        pack = await generator.generate(
            ad_id="test_003",
            campaign_name="Test",
            brand_name="Test",
            headline="Test",
            primary_text="Test",
            cta="Test",
            claims=claims,
        )
        
        # First claim should pass (has source)
        verified_claim = next(c for c in pack.claims if "Verified" in c.claim_text)
        assert verified_claim.verification_status == ComplianceStatus.PASS
    
    @pytest.mark.asyncio
    async def test_regulatory_checks_included(self, generator):
        """Test that regulatory checks are included."""
        pack = await generator.generate(
            ad_id="test_004",
            campaign_name="Test",
            brand_name="Test",
            headline="Test Headline",
            primary_text="Test body",
            cta="Learn More",
        )
        
        assert len(pack.regulatory_checks) > 0
        
        # Should include FTC check
        ftc_check = next((c for c in pack.regulatory_checks if c.regulation == RegulationType.FTC), None)
        assert ftc_check is not None
        
        # Should include Meta Policy check
        meta_check = next((c for c in pack.regulatory_checks if c.regulation == RegulationType.META_POLICY), None)
        assert meta_check is not None
    
    @pytest.mark.asyncio
    async def test_brand_safety_checks_included(self, generator):
        """Test that brand safety checks are included."""
        pack = await generator.generate(
            ad_id="test_005",
            campaign_name="Test",
            brand_name="TestBrand",
            headline="Test Headline",
            primary_text="Test body with TestBrand mentioned",
            cta="Learn More",
        )
        
        assert len(pack.brand_safety_checks) > 0
        assert pack.brand_safety_score >= 0
        assert pack.brand_safety_score <= 100
    
    @pytest.mark.asyncio
    async def test_headline_length_check(self, generator):
        """Test Meta headline length check."""
        # Long headline
        pack = await generator.generate(
            ad_id="test_006",
            campaign_name="Test",
            brand_name="Test",
            headline="This is a very long headline that exceeds the recommended forty character limit for Meta ads",
            primary_text="Test",
            cta="Test",
        )
        
        meta_check = next((c for c in pack.regulatory_checks if c.regulation == RegulationType.META_POLICY), None)
        assert meta_check is not None
        
        # Should have failed requirement about headline length
        assert any("headline" in req.lower() for req in meta_check.requirements_failed)
    
    @pytest.mark.asyncio
    async def test_risky_claim_detection(self, generator):
        """Test detection of risky claim patterns."""
        claims = [
            {"claim": "100% guaranteed to work", "source_text": "", "risk_level": "high"},
        ]
        
        pack = await generator.generate(
            ad_id="test_007",
            campaign_name="Test",
            brand_name="Test",
            headline="Test",
            primary_text="Test",
            cta="Test",
            claims=claims,
        )
        
        # Should detect "guaranteed" as requiring disclaimer
        risky_claim = pack.claims[0]
        assert risky_claim.requires_disclaimer is True
        assert risky_claim.suggested_disclaimer is not None
    
    @pytest.mark.asyncio
    async def test_action_items_generated(self, generator):
        """Test that action items are generated."""
        claims = [
            {"claim": "Unverified high risk claim", "source_text": "", "risk_level": "high"},
        ]
        
        pack = await generator.generate(
            ad_id="test_008",
            campaign_name="Test",
            brand_name="Test",
            headline="A" * 50,  # Too long
            primary_text="Test",
            cta="Test",
            claims=claims,
        )
        
        # Should have action items
        assert len(pack.action_items) > 0
    
    @pytest.mark.asyncio
    async def test_approval_trail(self, generator):
        """Test that approval trail is created."""
        pack = await generator.generate(
            ad_id="test_009",
            campaign_name="Test",
            brand_name="Test",
            headline="Test",
            primary_text="Test",
            cta="Test",
        )
        
        # Should have at least generation record
        assert len(pack.approval_history) > 0
        assert any("proof_pack_generated" in a.action for a in pack.approval_history)
    
    def test_export_to_json(self, generator):
        """Test JSON export."""
        import asyncio
        
        async def run():
            pack = await generator.generate(
                ad_id="test_010",
                campaign_name="Test",
                brand_name="Test",
                headline="Test",
                primary_text="Test",
                cta="Test",
            )
            return generator.export_to_json(pack)
        
        json_str = asyncio.run(run())
        
        assert isinstance(json_str, str)
        assert "test_010" in json_str
    
    def test_export_to_html(self, generator):
        """Test HTML export."""
        import asyncio
        
        async def run():
            pack = await generator.generate(
                ad_id="test_011",
                campaign_name="Test",
                brand_name="Test",
                headline="Test",
                primary_text="Test",
                cta="Test",
            )
            return generator.export_to_html(pack)
        
        html = asyncio.run(run())
        
        assert isinstance(html, str)
        assert "<html>" in html
        assert "test_011" in html


class TestProofPack:
    """Tests for ProofPack model."""
    
    def test_get_summary(self):
        """Test summary generation."""
        pack = ProofPack(
            pack_id="pack_test",
            ad_id="ad_test",
            campaign_name="Test Campaign",
            brand_name="Test Brand",
            headline="Test",
            primary_text="Test",
            cta="Test",
            total_claims=3,
            verified_claims=2,
            high_risk_claims=1,
            brand_safety_score=85,
            overall_compliance=ComplianceStatus.WARNING,
        )
        
        summary = pack.get_summary()
        
        assert "warning" in summary.lower() or "⚠️" in summary
        assert "2/3" in summary or "2" in summary


class TestGetProofPackGenerator:
    """Tests for factory function."""
    
    def test_returns_generator(self):
        """Test factory returns generator."""
        generator = get_proof_pack_generator()
        assert generator is not None
        assert hasattr(generator, "generate")
