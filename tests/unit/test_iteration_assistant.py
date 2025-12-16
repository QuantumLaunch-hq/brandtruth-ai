# tests/unit/test_iteration_assistant.py
"""Unit tests for Iteration Assistant (Slice 22)."""

import pytest
from src.analyzers.iteration_assistant import (
    IterationAssistant, IterationRequest, PerformanceIssue, IssueSeverity,
    BENCHMARKS, get_iteration_assistant,
)


class TestIterationAssistant:
    """Test IterationAssistant class."""

    @pytest.fixture
    def assistant(self):
        return IterationAssistant()

    @pytest.fixture
    def sample_request(self):
        return IterationRequest(
            headline="Check out our product",
            primary_text="We have a great product that you should try.",
            cta="Learn More",
            current_ctr=0.5,
            current_cvr=1.0,
            current_cpa=120,
            target_cpa=50,
            impressions=10000,
            frequency=2.0,
            days_running=7,
        )

    @pytest.fixture
    def good_performance_request(self):
        return IterationRequest(
            headline="Stop Getting Rejected",
            primary_text="Build ATS-optimized resumes",
            cta="Get Started Free",
            current_ctr=2.0,
            current_cvr=4.0,
            current_cpa=40,
            target_cpa=50,
            impressions=10000,
            frequency=1.5,
            days_running=7,
        )

    @pytest.mark.asyncio
    async def test_analyze_returns_diagnoses(self, assistant, sample_request):
        """Test diagnoses are returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.diagnoses) > 0

    @pytest.mark.asyncio
    async def test_analyze_returns_improved_variants(self, assistant, sample_request):
        """Test improved variants are returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.improved_variants) > 0

    @pytest.mark.asyncio
    async def test_analyze_returns_priority_fixes(self, assistant, sample_request):
        """Test priority fixes are returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.priority_fixes) > 0

    @pytest.mark.asyncio
    async def test_analyze_returns_testing_roadmap(self, assistant, sample_request):
        """Test testing roadmap is returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.testing_roadmap) > 0

    @pytest.mark.asyncio
    async def test_analyze_returns_quick_wins(self, assistant, sample_request):
        """Test quick wins are returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.quick_wins) > 0

    @pytest.mark.asyncio
    async def test_analyze_returns_estimated_improvement(self, assistant, sample_request):
        """Test estimated improvement is returned."""
        result = await assistant.analyze(sample_request)
        assert len(result.estimated_improvement) > 0

    @pytest.mark.asyncio
    async def test_diagnoses_have_required_fields(self, assistant, sample_request):
        """Test diagnoses have required fields."""
        result = await assistant.analyze(sample_request)
        for diag in result.diagnoses:
            assert diag.issue in PerformanceIssue
            assert diag.severity in IssueSeverity
            assert diag.description
            assert diag.likely_cause
            assert diag.impact

    @pytest.mark.asyncio
    async def test_improved_variants_have_required_fields(self, assistant, sample_request):
        """Test improved variants have required fields."""
        result = await assistant.analyze(sample_request)
        for imp in result.improved_variants:
            assert imp.element
            assert imp.original
            assert imp.improved
            assert imp.rationale
            assert imp.expected_improvement

    @pytest.mark.asyncio
    async def test_low_ctr_detected(self, assistant):
        """Test low CTR is diagnosed."""
        request = IterationRequest(
            headline="Test",
            primary_text="Test",
            cta="Test",
            current_ctr=0.3,  # Very low
            current_cvr=2.0,
            current_cpa=80,
            target_cpa=50,
        )
        result = await assistant.analyze(request)
        ctr_issues = [d for d in result.diagnoses if d.issue == PerformanceIssue.LOW_CTR]
        assert len(ctr_issues) > 0
        assert ctr_issues[0].severity == IssueSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_low_cvr_detected(self, assistant):
        """Test low CVR is diagnosed."""
        request = IterationRequest(
            headline="Test",
            primary_text="Test",
            cta="Test",
            current_ctr=1.5,
            current_cvr=0.5,  # Very low
            current_cpa=200,
            target_cpa=50,
        )
        result = await assistant.analyze(request)
        cvr_issues = [d for d in result.diagnoses if d.issue == PerformanceIssue.LOW_CVR]
        assert len(cvr_issues) > 0

    @pytest.mark.asyncio
    async def test_high_cpa_detected(self, assistant):
        """Test high CPA is diagnosed."""
        request = IterationRequest(
            headline="Test",
            primary_text="Test",
            cta="Test",
            current_ctr=1.0,
            current_cvr=2.0,
            current_cpa=150,  # 3x target
            target_cpa=50,
        )
        result = await assistant.analyze(request)
        cpa_issues = [d for d in result.diagnoses if d.issue == PerformanceIssue.HIGH_CPA]
        assert len(cpa_issues) > 0

    @pytest.mark.asyncio
    async def test_high_frequency_detected(self, assistant):
        """Test high frequency is diagnosed."""
        request = IterationRequest(
            headline="Test",
            primary_text="Test",
            cta="Test",
            current_ctr=1.0,
            current_cvr=2.0,
            current_cpa=80,
            target_cpa=50,
            frequency=4.0,  # High frequency
        )
        result = await assistant.analyze(request)
        freq_issues = [d for d in result.diagnoses if d.issue == PerformanceIssue.HIGH_FREQUENCY]
        assert len(freq_issues) > 0

    @pytest.mark.asyncio
    async def test_good_performance_fewer_issues(self, assistant, good_performance_request):
        """Test good performance has fewer critical issues."""
        result = await assistant.analyze(good_performance_request)
        critical_issues = [d for d in result.diagnoses if d.severity == IssueSeverity.CRITICAL]
        assert len(critical_issues) == 0

    def test_singleton_pattern(self):
        """Test get_iteration_assistant returns singleton."""
        a1 = get_iteration_assistant()
        a2 = get_iteration_assistant()
        assert a1 is a2


class TestPerformanceIssue:
    """Test PerformanceIssue enum."""

    def test_all_issues_defined(self):
        """Test all performance issues exist."""
        assert PerformanceIssue.LOW_CTR.value == "low_ctr"
        assert PerformanceIssue.LOW_CVR.value == "low_cvr"
        assert PerformanceIssue.HIGH_CPA.value == "high_cpa"
        assert PerformanceIssue.HIGH_FREQUENCY.value == "high_frequency"


class TestBenchmarks:
    """Test benchmark data."""

    def test_ctr_benchmarks(self):
        """Test CTR benchmarks exist."""
        assert "ctr" in BENCHMARKS
        assert "poor" in BENCHMARKS["ctr"]
        assert "average" in BENCHMARKS["ctr"]
        assert "good" in BENCHMARKS["ctr"]

    def test_cvr_benchmarks(self):
        """Test CVR benchmarks exist."""
        assert "cvr" in BENCHMARKS
        assert "poor" in BENCHMARKS["cvr"]
        assert "average" in BENCHMARKS["cvr"]
        assert "good" in BENCHMARKS["cvr"]
