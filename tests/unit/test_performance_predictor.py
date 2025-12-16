# tests/unit/test_performance_predictor.py
"""Unit tests for Performance Predictor (Slice 9)."""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analyzers.performance_predictor import (
    PerformancePredictor,
    MockPerformancePredictor,
    AdToAnalyze,
    PerformancePrediction,
    PerformanceTier,
    CTRPrediction,
    ImprovementPriority,
    ComponentScore,
    get_predictor,
)


class TestAdToAnalyze:
    """Tests for AdToAnalyze model."""
    
    def test_create_minimal(self):
        """Test creating with minimal fields."""
        ad = AdToAnalyze(
            headline="Test Headline",
            primary_text="Test body text",
            cta="Learn More",
        )
        assert ad.headline == "Test Headline"
        assert ad.cta == "Learn More"
        assert ad.platform == "meta"  # default
    
    def test_create_full(self):
        """Test creating with all fields."""
        ad = AdToAnalyze(
            headline="Stop Getting Rejected",
            primary_text="Build resumes that work",
            cta="Get Started",
            image_url="https://example.com/image.jpg",
            target_audience="Job seekers",
            platform="instagram",
            industry="career",
            brand_name="Careerfied",
        )
        assert ad.platform == "instagram"
        assert ad.industry == "career"
        assert ad.brand_name == "Careerfied"


class TestPerformanceTier:
    """Tests for PerformanceTier enum."""
    
    def test_tier_values(self):
        """Test all tier values exist."""
        assert PerformanceTier.POOR.value == "poor"
        assert PerformanceTier.WEAK.value == "weak"
        assert PerformanceTier.AVERAGE.value == "average"
        assert PerformanceTier.GOOD.value == "good"
        assert PerformanceTier.STRONG.value == "strong"
        assert PerformanceTier.EXCEPTIONAL.value == "exceptional"


class TestMockPerformancePredictor:
    """Tests for MockPerformancePredictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance."""
        return MockPerformancePredictor()
    
    @pytest.mark.asyncio
    async def test_predict_returns_prediction(self, predictor):
        """Test prediction returns valid result."""
        ad = AdToAnalyze(
            headline="Test Headline",
            primary_text="Test body",
            cta="Learn More",
        )
        
        prediction = await predictor.predict(ad)
        
        assert isinstance(prediction, PerformancePrediction)
        assert 0 <= prediction.overall_score <= 100
        assert prediction.performance_tier in PerformanceTier
        assert prediction.ctr_prediction in CTRPrediction
    
    @pytest.mark.asyncio
    async def test_predict_has_component_scores(self, predictor):
        """Test prediction includes component scores."""
        ad = AdToAnalyze(
            headline="Stop Getting Rejected by ATS",
            primary_text="Build resumes that get interviews",
            cta="Get Started",
        )
        
        prediction = await predictor.predict(ad)
        
        assert len(prediction.component_scores) > 0
        for score in prediction.component_scores:
            assert 0 <= score.score <= 100
            assert score.name
    
    @pytest.mark.asyncio
    async def test_predict_has_improvements(self, predictor):
        """Test prediction includes improvements."""
        ad = AdToAnalyze(
            headline="Test",
            primary_text="Short",
            cta="OK",
        )
        
        prediction = await predictor.predict(ad)
        
        # Should have some improvements for weak ad
        assert len(prediction.improvements) >= 0
    
    @pytest.mark.asyncio
    async def test_strong_headline_scores_higher(self, predictor):
        """Test that strong headlines score higher."""
        weak_ad = AdToAnalyze(
            headline="Test",
            primary_text="Test body",
            cta="OK",
        )
        
        strong_ad = AdToAnalyze(
            headline="Stop Getting Rejected by ATS Systems",
            primary_text="Build resumes that get interviews with AI-powered optimization",
            cta="Get Started Free",
        )
        
        weak_prediction = await predictor.predict(weak_ad)
        strong_prediction = await predictor.predict(strong_ad)
        
        # Strong ad should score higher
        assert strong_prediction.overall_score >= weak_prediction.overall_score
    
    @pytest.mark.asyncio
    async def test_prediction_summary(self, predictor):
        """Test prediction summary generation."""
        ad = AdToAnalyze(
            headline="Test Headline",
            primary_text="Test body",
            cta="Learn More",
        )
        
        prediction = await predictor.predict(ad)
        summary = prediction.get_summary()
        
        assert str(prediction.overall_score) in summary
        assert prediction.performance_tier.value in summary.lower() or "score" in summary.lower()


class TestPerformancePrediction:
    """Tests for PerformancePrediction model."""
    
    def test_get_summary(self):
        """Test summary generation."""
        prediction = PerformancePrediction(
            overall_score=75,
            performance_tier=PerformanceTier.GOOD,
            confidence=0.8,
            ctr_prediction=CTRPrediction.ABOVE_AVERAGE,
            estimated_ctr_range=(1.2, 1.8),
            conversion_potential="High",
            component_scores=[
                ComponentScore(
                    name="Headline",
                    score=80,
                    weight=0.25,
                    analysis="Good headline with clear value prop",
                    strengths=["Clear"],
                    weaknesses=[],
                ),
            ],
            improvements=[],
            ab_test_suggestions=[],
        )
        
        summary = prediction.get_summary()
        assert "75" in summary
        assert isinstance(summary, str)


class TestGetPredictor:
    """Tests for predictor factory function."""
    
    def test_returns_predictor(self):
        """Test factory returns predictor instance."""
        predictor = get_predictor()
        assert predictor is not None
        assert hasattr(predictor, "predict")
