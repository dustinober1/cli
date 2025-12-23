"""
Tests for token budgeting functionality.

This module tests the TokenBudgeter class which provides dynamic
token allocation based on context, operation type, and conversation history.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.intelligence.token_budgeter import ContextRequest, TokenBudgeter
from vibe_coder.intelligence.types import ContextItem, TokenBudget


class TestContextRequest:
    """Test ContextRequest dataclass."""

    def test_context_request_creation(self):
        """Test creating a context request."""
        request = ContextRequest(
            operation_type="generate",
            target_file="main.py",
            conversation_history_length=500,
            recent_changes=["utils.py", "main.py"],
            model_name="gpt-4",
            custom_budget=4000,
        )

        assert request.operation_type == "generate"
        assert request.target_file == "main.py"
        assert request.conversation_history_length == 500
        assert request.recent_changes == ["utils.py", "main.py"]
        assert request.model_name == "gpt-4"
        assert request.custom_budget == 4000

    def test_context_request_defaults(self):
        """Test context request with default values."""
        request = ContextRequest(operation_type="fix")

        assert request.operation_type == "fix"
        assert request.target_file is None
        assert request.conversation_history_length == 0
        assert request.recent_changes == []
        assert request.model_name == "gpt-4"
        assert request.custom_budget is None

    def test_context_request_post_init(self):
        """Test post_init initializes recent_changes."""
        request = ContextRequest(operation_type="test", recent_changes=None)
        assert request.recent_changes == []


class TestTokenBudgeterInitialization:
    """Test TokenBudgeter initialization."""

    def test_init_with_known_model(self):
        """Test initialization with known model."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        assert budgeter.token_counter == mock_counter
        assert budgeter.model_name == "gpt-4"
        assert budgeter.context_limit == 8192  # gpt-4 limit
        assert budgeter.base_reserve_percentage == 0.3

    def test_init_with_unknown_model(self):
        """Test initialization with unknown model."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="unknown-model")

        assert budgeter.model_name == "unknown-model"
        assert budgeter.context_limit == 8192  # Default limit

    def test_model_limits(self):
        """Test model token limits are properly defined."""
        assert TokenBudgeter.MODEL_LIMITS["gpt-3.5-turbo"] == 16385
        assert TokenBudgeter.MODEL_LIMITS["gpt-4"] == 8192
        assert TokenBudgeter.MODEL_LIMITS["gpt-4-32k"] == 32768
        assert TokenBudgeter.MODEL_LIMITS["gpt-4-turbo"] == 128000
        assert TokenBudgeter.MODEL_LIMITS["claude-3-haiku"] == 200000
        assert TokenBudgeter.MODEL_LIMITS["claude-3-sonnet"] == 200000
        assert TokenBudgeter.MODEL_LIMITS["claude-3-opus"] == 200000

    def test_operation_allocations(self):
        """Test operation-specific allocations sum to reasonable values."""
        for operation, allocations in TokenBudgeter.OPERATION_ALLOCATIONS.items():
            total = sum(allocations.values())
            # Should sum to 1.0 (100%)
            assert abs(total - 1.0) < 0.001
            assert "reserve_response" in allocations


@pytest.mark.asyncio
class TestCalculateBudget:
    """Test budget calculation functionality."""

    async def test_calculate_budget_with_custom_budget(self):
        """Test calculating budget with custom token limit."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        request = ContextRequest(
            operation_type="generate",
            custom_budget=4000,
        )

        budget = await budgeter.calculate_budget(request)

        assert budget.total == 4000  # Custom budget used
        assert budget.available >= 0
        assert budget.reserved_response > 0
        assert "repository_overview" in budget.allocations
        assert "target_file" in budget.allocations
        assert "dependencies" in budget.allocations

    async def test_calculate_budget_with_history(self):
        """Test calculating budget considering conversation history."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")  # 8192 limit

        request = ContextRequest(
            operation_type="fix",
            conversation_history_length=2000,  # Takes up space
        )

        budget = await budgeter.calculate_budget(request)

        # Total should be less than full limit due to history
        expected_available = 8192 - 2000 - int(8192 * 0.3)  # History + reserve
        assert budget.total == expected_available
        assert budget.reserved_response > 0

    async def test_calculate_budget_different_operations(self):
        """Test calculating budget for different operation types."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        operations = ["generate", "fix", "refactor", "explain", "test", "document"]

        for op in operations:
            request = ContextRequest(operation_type=op)
            budget = await budgeter.calculate_budget(request)

            # Check operation-specific allocations
            if op == "fix":
                assert budget.allocations.get("target_file", 0) > budget.allocations.get(
                    "repository_overview", 0
                )
            elif op == "explain":
                assert "metadata" in budget.allocations

    async def test_calculate_budget_unknown_operation(self):
        """Test calculating budget for unknown operation type."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        request = ContextRequest(operation_type="unknown")
        budget = await budgeter.calculate_budget(request)

        # Should use default (generate) allocations
        assert "repository_overview" in budget.allocations
        assert "target_file" in budget.allocations

    async def test_calculate_budget_with_recent_changes(self):
        """Test budget adjustment for recently modified files."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        request = ContextRequest(
            operation_type="generate",
            target_file="main.py",
            recent_changes=["main.py", "utils.py"],
            custom_budget=4000,
        )

        budget = await budgeter.calculate_budget(request)

        # Target file allocation should be increased
        original_target_allocation = int(4000 * 0.4)  # 40% for generate
        assert budget.allocations["target_file"] > original_target_allocation


@pytest.mark.asyncio
class TestCompressContext:
    """Test context compression functionality."""

    async def test_compress_context_within_budget(self):
        """Test compressing context that fits within budget."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        # Create budget with allocations
        budget = TokenBudget(
            total=1000,
            available=1000,
            reserved_response=50,
        )
        budget.allocate("target_file", 500)
        budget.allocate("dependencies", 300)

        # Create context items
        items = [
            ContextItem(
                path="target.py",
                content="def target(): pass",
                importance=0.9,
                token_count=100,
                type="file",
            ),
            ContextItem(
                path="utils.py",
                content="def helper(): pass",
                importance=0.6,
                token_count=80,
                type="file",
            ),
        ]

        compressed = await budgeter.compress_context(items, budget)

        assert len(compressed) == 2  # Both items fit
        assert compressed[0].path == "target.py"  # Higher importance first

    async def test_compress_context_exceeds_budget(self):
        """Test compressing context that exceeds budget."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        # Create small budget
        budget = TokenBudget(
            total=100,
            available=100,
            reserved_response=10,
        )
        budget.allocate("target_file", 50)

        # Create large items
        items = [
            ContextItem(
                path="large.py",
                content="#" * 400,  # Large content
                importance=0.8,
                token_count=100,
                type="file",
            ),
            ContextItem(
                path="small.py",
                content="# Small",
                importance=0.9,
                token_count=10,
                type="file",
            ),
        ]

        with patch.object(budgeter, "_summarize_item") as mock_summarize:
            # Mock summarization to reduce tokens
            summarized = ContextItem(
                path="large.py",
                content="# Summarized",
                importance=0.8,
                token_count=20,
                type="summary",
            )
            mock_summarize.return_value = summarized

            compressed = await budgeter.compress_context(items, budget)

            # Should include small item and summarized large item
            assert len(compressed) <= 2
            # Check that summarization was attempted
            mock_summarize.assert_called()

    async def test_compress_context_by_importance(self):
        """Test that compression respects item importance."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        budget = TokenBudget(total=100, available=100, reserved_response=10)
        budget.allocate("target_file", 50)

        # Create items with different importance
        items = [
            ContextItem(
                path="low.py",
                content="# Low importance",
                importance=0.2,
                token_count=30,
                type="file",
            ),
            ContextItem(
                path="high.py",
                content="# High importance",
                importance=0.9,
                token_count=30,
                type="file",
            ),
            ContextItem(
                path="medium.py",
                content="# Medium importance",
                importance=0.6,
                token_count=30,
                type="file",
            ),
        ]

        compressed = await budgeter.compress_context(items, budget)

        # Should prioritize by importance (descending)
        if len(compressed) >= 2:
            assert compressed[0].importance >= compressed[1].importance

    async def test_compress_context_allocation_limits(self):
        """Test that compression respects allocation limits per section."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        budget = TokenBudget(total=200, available=200, reserved_response=20)
        budget.allocate("target_file", 50)
        budget.allocate("dependencies", 50)

        # Create items that would exceed allocation
        items = [
            ContextItem(
                path="target1.py",
                content="# Target file 1",
                importance=0.9,
                token_count=30,
                type="file",
            ),
            ContextItem(
                path="target2.py",
                content="# Target file 2",
                importance=0.8,
                token_count=30,
                type="file",
            ),
            ContextItem(
                path="target3.py",
                content="# Target file 3",
                importance=0.7,
                token_count=30,
                type="file",
            ),
        ]

        compressed = await budgeter.compress_context(items, budget)

        # Should not exceed target_file allocation (50 tokens)
        target_tokens = sum(
            item.token_count for item in compressed if item.path.startswith("target")
        )
        assert target_tokens <= 50

    def test_get_allocation_key(self):
        """Test mapping item types to allocation keys."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        # Test different item types
        assert budgeter._get_allocation_key("file", "target.py") == "target_file"
        assert budgeter._get_allocation_key("function", "target.py") == "target_file"
        assert budgeter._get_allocation_key("class", "target.py") == "target_file"
        assert budgeter._get_allocation_key("import", "utils.py") == "dependencies"
        assert budgeter._get_allocation_key("summary", "overview.md") == "repository_overview"

        # Test path-based detection
        assert budgeter._get_allocation_key("file", "dependency/helper.py") == "dependencies"
        assert budgeter._get_allocation_key("file", "imports/utils.py") == "dependencies"


@pytest.mark.asyncio
class TestSummarizeItem:
    """Test item summarization functionality."""

    async def test_summarize_file_item(self):
        """Test summarizing a file context item."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        # Create file with various content
        content = '''
"""Module docstring."""

import os
import sys
from typing import Optional

def simple_function(param):
    """Function docstring."""
    return param

class TestClass:
    """Class docstring."""

    def method(self):
        # Implementation comment
        pass

# More code here
x = 1
y = 2
z = x + y
'''

        item = ContextItem(
            path="test.py",
            content=content,
            importance=0.7,
            token_count=len(content) // 4,
            type="file",
        )

        summarized = await budgeter._summarize_item(item)

        assert summarized is not None
        assert summarized.type == "summary"
        assert summarized.token_count < item.token_count
        assert "def simple_function" in summarized.content
        assert "class TestClass" in summarized.content
        assert "import" in summarized.content
        assert summarized.metadata["summarized"] is True

    async def test_summarize_non_file_item(self):
        """Test summarizing non-file context item."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        item = ContextItem(
            path="metadata",
            content="Some metadata",
            importance=0.5,
            token_count=10,
            type="metadata",
        )

        summarized = await budgeter._summarize_item(item)

        # Non-file items might not be summarized
        assert summarized is None

    async def test_summarize_empty_file(self):
        """Test summarizing an empty file."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        item = ContextItem(
            path="empty.py",
            content="",
            importance=0.5,
            token_count=0,
            type="file",
        )

        summarized = await budgeter._summarize_item(item)

        # Empty file cannot be summarized
        assert summarized is None


@pytest.mark.asyncio
class TestEstimateTokens:
    """Test token estimation functionality."""

    async def test_estimate_tokens(self):
        """Test token estimation delegation."""
        mock_counter = MagicMock()
        mock_counter.count_tokens = AsyncMock(return_value=100)

        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        text = "Sample text to estimate tokens"
        count = await budgeter.estimate_tokens(text)

        mock_counter.count_tokens.assert_called_once_with(text, "gpt-4")
        assert count == 100


class TestModelManagement:
    """Test model management functionality."""

    def test_get_model_info(self):
        """Test getting model information."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        info = budgeter.get_model_info()

        assert info["name"] == "gpt-4"
        assert info["context_limit"] == 8192
        assert info["is_chat_model"] is True
        assert info["supports_functions"] is True

    def test_get_model_info_claude(self):
        """Test getting Claude model information."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="claude-3-sonnet")

        info = budgeter.get_model_info()

        assert info["name"] == "claude-3-sonnet"
        assert info["context_limit"] == 200000
        assert info["is_chat_model"] is True
        assert info["supports_functions"] is True

    def test_update_model(self):
        """Test updating the model."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        assert budgeter.model_name == "gpt-4"
        assert budgeter.context_limit == 8192

        budgeter.update_model("gpt-4-turbo")

        assert budgeter.model_name == "gpt-4-turbo"
        assert budgeter.context_limit == 128000

    def test_update_model_to_unknown(self):
        """Test updating to unknown model."""
        mock_counter = MagicMock()
        budgeter = TokenBudgeter(mock_counter, model_name="gpt-4")

        budgeter.update_model("unknown-model")

        assert budgeter.model_name == "unknown-model"
        assert budgeter.context_limit == 8192  # Default limit


class TestTokenBudget:
    """Test TokenBudget class functionality."""

    def test_token_budget_creation(self):
        """Test creating a token budget."""
        budget = TokenBudget(
            total=1000,
            available=1000,
            reserved_response=100,
        )

        assert budget.total == 1000
        assert budget.available == 1000
        assert budget.reserved_response == 100
        assert budget.allocations == {}

    def test_token_budget_allocation(self):
        """Test allocating tokens within budget."""
        budget = TokenBudget(
            total=1000,
            available=1000,
            reserved_response=100,
        )

        # Successful allocation
        assert budget.allocate("section1", 300) is True
        assert budget.available == 700
        assert budget.allocations["section1"] == 300

        # Another successful allocation
        assert budget.allocate("section2", 200) is True
        assert budget.available == 500
        assert budget.allocations["section2"] == 200

    def test_token_budget_insufficient(self):
        """Test allocating more tokens than available."""
        budget = TokenBudget(
            total=1000,
            available=1000,
            reserved_response=100,
        )

        # Allocate most of budget
        budget.allocate("section1", 900)
        assert budget.available == 100

        # Try to allocate more than available
        assert budget.allocate("section2", 200) is False
        assert budget.available == 100  # Unchanged
        assert "section2" not in budget.allocations

    def test_token_budget_to_dict(self):
        """Test converting budget to dictionary."""
        budget = TokenBudget(
            total=1000,
            available=500,
            reserved_response=100,
        )
        budget.allocate("section1", 300)
        budget.allocate("section2", 200)

        budget_dict = budget.to_dict()

        assert budget_dict["total"] == 1000
        assert budget_dict["available"] == 500
        assert budget_dict["reserved_response"] == 100
        assert budget_dict["allocations"]["section1"] == 300
        assert budget_dict["allocations"]["section2"] == 200
