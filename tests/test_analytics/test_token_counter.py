"""Tests for the token counter."""

import pytest

from vibe_coder.analytics.token_counter import TokenCounter, token_counter


class TestTokenCounter:
    """Tests for TokenCounter class."""

    @pytest.fixture
    def counter(self):
        """Create token counter instance."""
        return TokenCounter()

    @pytest.mark.asyncio
    async def test_count_tokens_basic(self, counter):
        """Test basic token counting."""
        text = "Hello, world! This is a test."
        count = await counter.count_tokens(text, "gpt-4")

        # Should be reasonable estimate
        assert count > 0
        assert count < len(text)  # Tokens < characters

    @pytest.mark.asyncio
    async def test_count_tokens_empty(self, counter):
        """Test counting empty text."""
        count = await counter.count_tokens("", "gpt-4")
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_tokens_different_models(self, counter):
        """Test counting for different models."""
        text = "A sample text for testing token counts."

        gpt_count = await counter.count_tokens(text, "gpt-4")
        claude_count = await counter.count_tokens(text, "claude-3-sonnet")

        # Both should be positive
        assert gpt_count > 0
        assert claude_count > 0

    def test_count_tokens_sync(self, counter):
        """Test synchronous token counting."""
        text = "Synchronous test text."
        count = counter.count_tokens_sync(text, "gpt-4")

        assert count > 0

    @pytest.mark.asyncio
    async def test_count_messages(self, counter):
        """Test counting messages."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        count = await counter.count_messages(messages, "gpt-4")

        # Should include all message content plus overhead
        assert count > 0

    @pytest.mark.asyncio
    async def test_estimate_request_cost(self, counter):
        """Test cost estimation."""
        prompt = "This is a test prompt for cost estimation."

        input_tokens, output_tokens, cost = await counter.estimate_request_cost(
            prompt, "gpt-4", estimated_output_tokens=100
        )

        assert input_tokens > 0
        assert output_tokens == 100
        assert cost >= 0

    @pytest.mark.asyncio
    async def test_estimate_messages_cost(self, counter):
        """Test cost estimation for messages."""
        messages = [
            {"role": "user", "content": "What is Python?"},
        ]

        input_tokens, output_tokens, cost = await counter.estimate_messages_cost(
            messages, "gpt-4o-mini", estimated_output_tokens=200
        )

        assert input_tokens > 0
        assert cost >= 0

    def test_get_token_limit(self, counter):
        """Test getting token limits."""
        limit = counter.get_token_limit("gpt-4o")
        assert limit == 128000

        limit = counter.get_token_limit("claude-3-sonnet")
        assert limit == 200000

        # Unknown model should return default
        limit = counter.get_token_limit("unknown-model")
        assert limit == 4096

    def test_get_output_limit(self, counter):
        """Test getting output limits."""
        limit = counter.get_output_limit("gpt-4o")
        assert limit == 16384

        limit = counter.get_output_limit("claude-3-haiku")
        assert limit == 4096

    def test_will_exceed_limit(self, counter):
        """Test limit checking."""
        short_text = "Short text"
        long_text = "x" * 1000000  # Very long text

        assert counter.will_exceed_limit(short_text, "gpt-4") is False
        assert counter.will_exceed_limit(long_text, "gpt-4") is True

    def test_truncate_to_limit(self, counter):
        """Test text truncation."""
        long_text = "word " * 10000  # Long text

        truncated = counter.truncate_to_limit(long_text, "gpt-4", max_tokens=100)

        assert len(truncated) < len(long_text)
        assert truncated.endswith("...")

    def test_truncate_keep_end(self, counter):
        """Test truncation keeping end."""
        long_text = "start " * 5000 + "important end"

        truncated = counter.truncate_to_limit(long_text, "gpt-4", max_tokens=50, keep_end=True)

        assert truncated.startswith("...")
        assert "end" in truncated

    def test_cache_operations(self, counter):
        """Test cache operations."""
        counter.clear_cache()
        stats = counter.get_cache_stats()
        assert stats["cached_counts"] == 0

        # Count something to populate cache
        counter.count_tokens_sync("test", "gpt-4")
        stats = counter.get_cache_stats()
        assert stats["cached_counts"] > 0

        # Clear and verify
        counter.clear_cache()
        stats = counter.get_cache_stats()
        assert stats["cached_counts"] == 0

    def test_module_level_instance(self):
        """Test module-level token_counter instance."""
        assert token_counter is not None
        count = token_counter.count_tokens_sync("test", "gpt-4")
        assert count > 0


class TestTokenEstimation:
    """Tests for token estimation accuracy."""

    @pytest.fixture
    def counter(self):
        """Create token counter instance."""
        return TokenCounter()

    def test_estimation_factors_exist(self, counter):
        """Test that estimation factors exist for common models."""
        factors = counter.TOKEN_ESTIMATION_FACTORS

        assert "gpt-4" in factors
        assert "claude" in factors
        assert "default" in factors

    def test_estimation_reasonable(self, counter):
        """Test that estimation is reasonable."""
        # Average English word is ~5 characters, ~1.3 tokens
        text = "The quick brown fox jumps over the lazy dog."  # 9 words

        count = counter.count_tokens_sync(text, "unknown-model")

        # Should be roughly 10-15 tokens
        assert 5 < count < 30

    def test_estimation_consistent(self, counter):
        """Test that repeated estimation is consistent."""
        text = "Consistent test text for verification."

        count1 = counter.count_tokens_sync(text, "gpt-4")
        count2 = counter.count_tokens_sync(text, "gpt-4")

        assert count1 == count2
