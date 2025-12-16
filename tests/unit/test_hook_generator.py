# tests/unit/test_hook_generator.py
"""Unit tests for Hook Generator (Slice 16)."""

import pytest
from src.generators.hook_generator import (
    HookGenerator, HookGeneratorRequest, HookPattern, POWER_WORDS,
    get_hook_generator,
)


class TestHookGenerator:
    """Test HookGenerator class."""

    @pytest.fixture
    def generator(self):
        return HookGenerator()

    @pytest.fixture
    def sample_request(self):
        return HookGeneratorRequest(
            product_name="Careerfied",
            product_description="AI-powered resume builder",
            target_audience="job seekers",
            pain_points=["getting rejected", "ATS systems"],
            benefits=["land more interviews", "stand out"],
            tone="professional",
            include_emojis=False,
            num_hooks=10,
        )

    @pytest.mark.asyncio
    async def test_generate_returns_correct_count(self, generator, sample_request):
        """Test that generate returns requested number of hooks."""
        result = await generator.generate(sample_request)
        assert len(result.hooks) == sample_request.num_hooks

    @pytest.mark.asyncio
    async def test_generate_returns_best_hook(self, generator, sample_request):
        """Test that best_hook is set correctly."""
        result = await generator.generate(sample_request)
        assert result.best_hook is not None
        assert result.best_hook.score >= max(h.score for h in result.hooks) - 1

    @pytest.mark.asyncio
    async def test_generate_returns_pattern_distribution(self, generator, sample_request):
        """Test pattern distribution is calculated."""
        result = await generator.generate(sample_request)
        assert len(result.pattern_distribution) > 0
        assert sum(result.pattern_distribution.values()) == len(result.hooks)

    @pytest.mark.asyncio
    async def test_generate_with_emojis(self, generator):
        """Test emoji inclusion."""
        request = HookGeneratorRequest(
            product_name="Test",
            product_description="Test product",
            target_audience="users",
            include_emojis=True,
            num_hooks=5,
        )
        result = await generator.generate(request)
        emoji_hooks = [h for h in result.hooks if any(ord(c) > 127 for c in h.text)]
        assert len(emoji_hooks) > 0

    @pytest.mark.asyncio
    async def test_hook_scores_in_valid_range(self, generator, sample_request):
        """Test all hook scores are 0-100."""
        result = await generator.generate(sample_request)
        for hook in result.hooks:
            assert 0 <= hook.score <= 100

    @pytest.mark.asyncio
    async def test_hook_character_count_accurate(self, generator, sample_request):
        """Test character count matches actual length."""
        result = await generator.generate(sample_request)
        for hook in result.hooks:
            assert hook.character_count == len(hook.text)

    @pytest.mark.asyncio
    async def test_all_patterns_covered(self, generator):
        """Test all hook patterns are used when enough hooks requested."""
        request = HookGeneratorRequest(
            product_name="Test",
            product_description="Test",
            target_audience="users",
            num_hooks=10,
        )
        result = await generator.generate(request)
        patterns_used = set(h.pattern for h in result.hooks)
        assert len(patterns_used) == 10  # All 10 patterns

    def test_get_patterns_returns_all(self, generator):
        """Test get_patterns returns all pattern types."""
        patterns = generator.get_patterns()
        assert len(patterns) == 10
        assert all("id" in p and "name" in p for p in patterns)

    def test_get_power_words_returns_categories(self, generator):
        """Test power words are returned by category."""
        words = generator.get_power_words()
        assert "urgency" in words
        assert "emotion" in words
        assert "results" in words
        assert len(words) >= 7

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, generator, sample_request):
        """Test recommendations are provided."""
        result = await generator.generate(sample_request)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_avg_score_calculated(self, generator, sample_request):
        """Test average score is calculated correctly."""
        result = await generator.generate(sample_request)
        expected_avg = sum(h.score for h in result.hooks) / len(result.hooks)
        assert abs(result.avg_score - expected_avg) < 0.1

    def test_singleton_pattern(self):
        """Test get_hook_generator returns singleton."""
        g1 = get_hook_generator()
        g2 = get_hook_generator()
        assert g1 is g2


class TestHookPatterns:
    """Test hook pattern enum."""

    def test_all_patterns_defined(self):
        """Test all 10 patterns are defined."""
        assert len(HookPattern) == 10

    def test_pattern_values(self):
        """Test pattern string values."""
        assert HookPattern.QUESTION.value == "question"
        assert HookPattern.PAIN_POINT.value == "pain_point"
        assert HookPattern.SOCIAL_PROOF.value == "social_proof"


class TestPowerWords:
    """Test power words database."""

    def test_power_words_categories(self):
        """Test all categories exist."""
        expected = ["urgency", "exclusivity", "curiosity", "value", "emotion", "fear", "results"]
        for cat in expected:
            assert cat in POWER_WORDS

    def test_power_words_not_empty(self):
        """Test each category has words."""
        for category, words in POWER_WORDS.items():
            assert len(words) > 0, f"{category} has no words"
