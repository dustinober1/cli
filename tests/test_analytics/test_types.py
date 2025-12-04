"""Tests for analytics types."""

from vibe_coder.analytics.types import ModelTier, RequestMetrics, TokenPricing, UsageStatistics


class TestModelTier:
    """Tests for ModelTier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert ModelTier.FREE.value == "free"
        assert ModelTier.CHEAP.value == "cheap"
        assert ModelTier.STANDARD.value == "standard"
        assert ModelTier.EXPENSIVE.value == "expensive"


class TestTokenPricing:
    """Tests for TokenPricing dataclass."""

    def test_create_token_pricing(self):
        """Test creating token pricing."""
        pricing = TokenPricing(
            model_name="gpt-4",
            input_price_per_1k=0.03,
            output_price_per_1k=0.06,
            tier=ModelTier.EXPENSIVE,
            context_window=8192,
            max_output=4096,
        )

        assert pricing.model_name == "gpt-4"
        assert pricing.input_price_per_1k == 0.03
        assert pricing.tier == ModelTier.EXPENSIVE

    def test_calculate_cost(self):
        """Test cost calculation."""
        pricing = TokenPricing(
            model_name="test",
            input_price_per_1k=0.001,
            output_price_per_1k=0.002,
            tier=ModelTier.CHEAP,
        )

        cost = pricing.calculate_cost(1000, 500)
        expected = 0.001 + 0.001  # 1K input + 0.5K output
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_large(self):
        """Test cost calculation for large token counts."""
        pricing = TokenPricing(
            model_name="test",
            input_price_per_1k=0.01,
            output_price_per_1k=0.03,
            tier=ModelTier.STANDARD,
        )

        cost = pricing.calculate_cost(100000, 50000)
        expected = 1.0 + 1.5  # 100K input + 50K output
        assert abs(cost - expected) < 0.0001

    def test_token_pricing_to_dict(self):
        """Test serialization."""
        pricing = TokenPricing(
            model_name="model",
            input_price_per_1k=0.005,
            output_price_per_1k=0.015,
            tier=ModelTier.STANDARD,
        )

        data = pricing.to_dict()
        assert data["model_name"] == "model"
        assert data["tier"] == "standard"

    def test_token_pricing_from_dict(self):
        """Test deserialization."""
        data = {
            "model_name": "loaded",
            "input_price_per_1k": 0.002,
            "output_price_per_1k": 0.008,
            "tier": "cheap",
            "context_window": 16000,
        }

        pricing = TokenPricing.from_dict(data)
        assert pricing.model_name == "loaded"
        assert pricing.tier == ModelTier.CHEAP


class TestRequestMetrics:
    """Tests for RequestMetrics dataclass."""

    def test_create_request_metrics(self):
        """Test creating request metrics."""
        metrics = RequestMetrics(
            model="gpt-4",
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
            input_cost=0.03,
            output_cost=0.03,
            completion_time=2.5,
            operation="chat",
        )

        assert metrics.model == "gpt-4"
        assert metrics.total_tokens == 1500
        assert metrics.total_cost == 0.06

    def test_auto_calculate_totals(self):
        """Test automatic calculation of totals."""
        metrics = RequestMetrics(
            model="test",
            provider="test",
            input_tokens=100,
            output_tokens=200,
            input_cost=0.01,
            output_cost=0.02,
        )

        assert metrics.total_tokens == 300
        assert metrics.total_cost == 0.03

    def test_request_metrics_defaults(self):
        """Test default values."""
        metrics = RequestMetrics()

        assert metrics.model == ""
        assert metrics.success is True
        assert metrics.error_message is None
        assert metrics.operation == "chat"

    def test_request_metrics_to_dict(self):
        """Test serialization."""
        metrics = RequestMetrics(
            model="claude",
            provider="anthropic",
            input_tokens=500,
            output_tokens=300,
        )

        data = metrics.to_dict()
        assert data["model"] == "claude"
        assert "timestamp" in data

    def test_request_metrics_from_dict(self):
        """Test deserialization."""
        data = {
            "timestamp": "2024-01-01T00:00:00",
            "model": "gpt-3.5",
            "provider": "openai",
            "input_tokens": 200,
            "output_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.001,
            "success": True,
        }

        metrics = RequestMetrics.from_dict(data)
        assert metrics.model == "gpt-3.5"
        assert metrics.total_tokens == 300


class TestUsageStatistics:
    """Tests for UsageStatistics dataclass."""

    def test_create_usage_statistics(self):
        """Test creating usage statistics."""
        stats = UsageStatistics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            total_tokens=50000,
            total_cost=5.0,
            total_time=250.0,
        )

        assert stats.total_requests == 100
        assert stats.success_rate == 95.0

    def test_computed_properties(self):
        """Test computed property calculations."""
        stats = UsageStatistics(
            total_requests=10,
            successful_requests=8,
            failed_requests=2,
            total_tokens=10000,
            total_cost=1.0,
            total_time=50.0,
        )

        assert stats.success_rate == 80.0
        assert stats.avg_tokens_per_request == 1000.0
        assert stats.avg_cost_per_request == 0.1
        assert stats.avg_time_per_request == 5.0

    def test_zero_requests_properties(self):
        """Test properties with zero requests."""
        stats = UsageStatistics()

        assert stats.success_rate == 100.0
        assert stats.avg_tokens_per_request == 0.0
        assert stats.avg_cost_per_request == 0.0

    def test_usage_statistics_to_dict(self):
        """Test serialization includes computed properties."""
        stats = UsageStatistics(
            total_requests=5,
            successful_requests=5,
            total_tokens=2500,
            total_cost=0.5,
        )

        data = stats.to_dict()
        assert data["total_requests"] == 5
        assert data["success_rate"] == 100.0
        assert data["avg_tokens_per_request"] == 500.0

    def test_usage_statistics_from_dict(self):
        """Test deserialization."""
        data = {
            "total_requests": 50,
            "successful_requests": 45,
            "failed_requests": 5,
            "total_tokens": 25000,
            "total_cost": 2.5,
            "by_model": {"gpt-4": {"requests": 30}},
        }

        stats = UsageStatistics.from_dict(data)
        assert stats.total_requests == 50
        assert "gpt-4" in stats.by_model
