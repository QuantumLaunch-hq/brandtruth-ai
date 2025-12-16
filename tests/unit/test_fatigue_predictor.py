# tests/unit/test_fatigue_predictor.py
"""Unit tests for Fatigue Predictor (Slice 14)."""

import pytest
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analyzers.fatigue_predictor import (
    FatiguePredictor,
    AdPerformanceData,
    FatiguePrediction,
    FatigueLevel,
    RefreshUrgency,
    DecayPattern,
    FatigueConfig,
    get_fatigue_predictor,
)


class TestAdPerformanceData:
    """Tests for AdPerformanceData model."""
    
    def test_create_minimal(self):
        """Test creating with minimal fields."""
        data = AdPerformanceData(
            ad_id="test_ad",
            start_date=datetime.utcnow() - timedelta(days=14),
            days_running=14,
        )
        assert data.ad_id == "test_ad"
        assert data.days_running == 14
    
    def test_create_full(self):
        """Test creating with all fields."""
        data = AdPerformanceData(
            ad_id="test_ad",
            start_date=datetime.utcnow() - timedelta(days=14),
            impressions=50000,
            clicks=1000,
            frequency=2.5,
            reach=20000,
            audience_size=100000,
            ctr_history=[2.0, 1.9, 1.8],
            cpm_history=[10.0, 10.5, 11.0],
            days_running=14,
            industry="saas",
            platform="meta",
        )
        assert data.impressions == 50000
        assert data.frequency == 2.5
        assert data.industry == "saas"


class TestFatigueLevel:
    """Tests for FatigueLevel enum."""
    
    def test_all_levels_exist(self):
        """Test all fatigue levels exist."""
        assert FatigueLevel.FRESH.value == "fresh"
        assert FatigueLevel.HEALTHY.value == "healthy"
        assert FatigueLevel.MODERATE.value == "moderate"
        assert FatigueLevel.HIGH.value == "high"
        assert FatigueLevel.CRITICAL.value == "critical"


class TestRefreshUrgency:
    """Tests for RefreshUrgency enum."""
    
    def test_all_urgencies_exist(self):
        """Test all urgency levels exist."""
        assert RefreshUrgency.NONE.value == "none"
        assert RefreshUrgency.PLAN.value == "plan"
        assert RefreshUrgency.PREPARE.value == "prepare"
        assert RefreshUrgency.URGENT.value == "urgent"
        assert RefreshUrgency.IMMEDIATE.value == "immediate"


class TestDecayPattern:
    """Tests for DecayPattern enum."""
    
    def test_all_patterns_exist(self):
        """Test all decay patterns exist."""
        assert DecayPattern.NONE.value == "none"
        assert DecayPattern.GRADUAL.value == "gradual"
        assert DecayPattern.SUDDEN.value == "sudden"
        assert DecayPattern.CYCLICAL.value == "cyclical"
        assert DecayPattern.PLATEAU.value == "plateau"


class TestFatiguePredictor:
    """Tests for FatiguePredictor."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance."""
        return FatiguePredictor()
    
    @pytest.mark.asyncio
    async def test_predict_fresh_ad(self, predictor):
        """Test prediction for fresh ad."""
        data = AdPerformanceData(
            ad_id="fresh_ad",
            start_date=datetime.utcnow() - timedelta(days=3),
            days_running=3,
            frequency=1.2,
            reach=9000,
            audience_size=100000,
            ctr_history=[2.0, 2.0, 1.98],
            cpm_history=[10.0, 10.0, 10.1],
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        assert isinstance(prediction, FatiguePrediction)
        assert prediction.fatigue_score < 30  # Fresh should be low
        assert prediction.fatigue_level in [FatigueLevel.FRESH, FatigueLevel.HEALTHY]
        assert prediction.refresh_urgency in [RefreshUrgency.NONE, RefreshUrgency.PLAN]
    
    @pytest.mark.asyncio
    async def test_predict_fatigued_ad(self, predictor):
        """Test prediction for fatigued ad."""
        days = 35
        data = AdPerformanceData(
            ad_id="fatigued_ad",
            start_date=datetime.utcnow() - timedelta(days=days),
            days_running=days,
            frequency=5.5,
            reach=105000,
            audience_size=100000,  # Over-saturated
            ctr_history=[max(0.5, 2.0 * (0.95 ** i)) for i in range(days)],
            cpm_history=[10.0 * (1.03 ** i) for i in range(days)],
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        assert prediction.fatigue_score > 70  # Fatigued should be high
        assert prediction.fatigue_level in [FatigueLevel.HIGH, FatigueLevel.CRITICAL]
        assert prediction.refresh_urgency in [RefreshUrgency.URGENT, RefreshUrgency.IMMEDIATE]
    
    @pytest.mark.asyncio
    async def test_predict_has_recommendations(self, predictor):
        """Test that prediction includes recommendations."""
        data = AdPerformanceData(
            ad_id="test_ad",
            start_date=datetime.utcnow() - timedelta(days=18),
            days_running=18,
            frequency=3.0,
            reach=54000,
            audience_size=100000,
            ctr_history=[max(0.5, 2.0 * (0.97 ** i)) for i in range(18)],
            cpm_history=[10.0 * (1.02 ** i) for i in range(18)],
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        assert len(prediction.recommendations) > 0
        assert len(prediction.refresh_strategies) > 0
    
    @pytest.mark.asyncio
    async def test_predict_has_projections(self, predictor):
        """Test that prediction includes 7-day projections."""
        data = AdPerformanceData(
            ad_id="test_ad",
            start_date=datetime.utcnow() - timedelta(days=14),
            days_running=14,
            frequency=2.5,
            reach=35000,
            audience_size=100000,
            ctr_history=[max(0.5, 2.0 * (0.97 ** i)) for i in range(14)],
            cpm_history=[10.0 * (1.02 ** i) for i in range(14)],
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        assert prediction.projected_ctr_7d > 0
        assert prediction.projected_cpm_7d > 0
        assert prediction.projected_frequency_7d > 0
    
    @pytest.mark.asyncio
    async def test_predict_calculates_decay_rate(self, predictor):
        """Test that decay rate is calculated."""
        data = AdPerformanceData(
            ad_id="test_ad",
            start_date=datetime.utcnow() - timedelta(days=14),
            days_running=14,
            frequency=2.5,
            reach=35000,
            audience_size=100000,
            ctr_history=[2.0 - (i * 0.05) for i in range(14)],  # Linear decline
            cpm_history=[10.0 + (i * 0.2) for i in range(14)],
            industry="saas",
        )
        
        prediction = await predictor.predict(data)
        
        assert prediction.decay_pattern != DecayPattern.NONE
        assert prediction.decay_rate >= 0
    
    @pytest.mark.asyncio
    async def test_industry_affects_prediction(self, predictor):
        """Test that industry benchmarks affect prediction."""
        base_data = {
            "ad_id": "test_ad",
            "start_date": datetime.utcnow() - timedelta(days=20),
            "days_running": 20,
            "frequency": 3.0,
            "reach": 60000,
            "audience_size": 100000,
            "ctr_history": [max(0.5, 2.0 * (0.97 ** i)) for i in range(20)],
            "cpm_history": [10.0 * (1.02 ** i) for i in range(20)],
        }
        
        # Entertainment has shorter fatigue window (10 days)
        entertainment_data = AdPerformanceData(**base_data, industry="entertainment")
        
        # Finance has longer fatigue window (30 days)
        finance_data = AdPerformanceData(**base_data, industry="finance")
        
        entertainment_pred = await predictor.predict(entertainment_data)
        finance_pred = await predictor.predict(finance_data)
        
        # Entertainment should show higher fatigue for same metrics
        assert entertainment_pred.fatigue_score >= finance_pred.fatigue_score


class TestFatiguePrediction:
    """Tests for FatiguePrediction model."""
    
    def test_get_summary(self):
        """Test summary generation."""
        prediction = FatiguePrediction(
            ad_id="test_ad",
            fatigue_score=55,
            fatigue_level=FatigueLevel.MODERATE,
            days_until_fatigue=7,
            refresh_urgency=RefreshUrgency.PREPARE,
            ctr_decline_percent=18.5,
            cpm_increase_percent=22.3,
            frequency_risk=0.64,
            audience_saturation=0.33,
            decay_pattern=DecayPattern.GRADUAL,
            decay_rate=1.2,
            projected_ctr_7d=1.65,
            projected_cpm_7d=12.8,
            projected_frequency_7d=3.7,
            recommendations=["Test recommendation"],
            refresh_strategies=["Test strategy"],
            optimal_refresh_date=datetime.utcnow() + timedelta(days=7),
        )
        
        summary = prediction.get_summary()
        assert "55" in summary
        assert "moderate" in summary.lower()


class TestFatigueConfig:
    """Tests for FatigueConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = FatigueConfig()
        
        # Check actual attribute names
        assert config.ctr_decline_threshold == 0.2
        assert config.cpm_increase_threshold == 0.3
        assert config.frequency_warning == 2.5
        assert config.frequency_critical == 4.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = FatigueConfig(
            ctr_decline_threshold=0.15,
            frequency_warning=2.0,
        )
        
        assert config.ctr_decline_threshold == 0.15
        assert config.frequency_warning == 2.0


class TestGetFatiguePredictor:
    """Tests for factory function."""
    
    def test_returns_predictor(self):
        """Test factory returns predictor."""
        predictor = get_fatigue_predictor()
        assert predictor is not None
        assert hasattr(predictor, "predict")
