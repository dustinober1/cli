#!/usr/bin/env python3
"""Test dynamic token budgeting functionality."""

import asyncio
import tempfile
from pathlib import Path

from vibe_coder.analytics.token_counter import TokenCounter
from vibe_coder.intelligence.repo_mapper import RepositoryMapper
from vibe_coder.intelligence.token_budgeter import TokenBudgeter, ContextRequest
from vibe_coder.intelligence.types import ContextItem


async def test_token_budgeting():
    """Test dynamic token budget allocation."""
    print("Starting token budgeting test...")

    # Create token counter and budgeter
    token_counter = TokenCounter()
    budgeter = TokenBudgeter(token_counter, model_name="gpt-4")

    # Test 1: Model information
    print("\nTest 1: Model information...")
    model_info = budgeter.get_model_info()
    print(f"Model: {model_info['name']}")
    print(f"Context limit: {model_info['context_limit']}")
    print(f"Supports functions: {model_info['supports_functions']}")

    # Test 2: Basic budget calculation
    print("\nTest 2: Basic budget calculation...")
    request = ContextRequest(
        operation_type="generate",
        target_file="main.py",
        conversation_history_length=1000,
        model_name="gpt-4"
    )

    budget = await budgeter.calculate_budget(request)
    print(f"Total tokens allocated: {budget.total}")
    print(f"Available tokens: {budget.available}")
    print(f"Reserved for response: {budget.reserved_response}")
    print(f"Allocations:")
    for section, tokens in budget.allocations.items():
        print(f"  - {section}: {tokens} tokens")

    # Test 3: Different operation types
    print("\nTest 3: Budget allocation by operation type...")
    operations = ["generate", "fix", "refactor", "explain", "test", "document"]

    for op in operations:
        request = ContextRequest(
            operation_type=op,
            target_file="main.py",
            conversation_history_length=1000
        )
        budget = await budgeter.calculate_budget(request)
        print(f"\n{op.title()} operation:")
        print(f"  Target file allocation: {budget.allocations.get('target_file', 0)}")
        print(f"  Repository overview: {budget.allocations.get('repository_overview', 0)}")
        print(f"  Dependencies: {budget.allocations.get('dependencies', 0)}")

    # Test 4: Context compression
    print("\nTest 4: Context compression...")

    # Create sample context items
    items = []
    for i in range(10):
        item = ContextItem(
            path=f"file_{i}.py",
            content=f"def function_{i}():\n    return {i}\n" * 20,  # Make it longer
            importance=0.5 + (i % 3) * 0.2,  # Varying importance
            token_count=100 + i * 10,
            type="file" if i % 2 == 0 else "function"
        )
        items.append(item)

    # Compress with budget
    budget = await budgeter.calculate_budget(
        ContextRequest(operation_type="explain", target_file="file_0.py")
    )
    compressed = await budgeter.compress_context(items, budget)

    print(f"Original items: {len(items)}")
    print(f"Compressed items: {len(compressed)}")
    print(f"Total original tokens: {sum(item.token_count for item in items)}")
    print(f"Total compressed tokens: {sum(item.token_count for item in compressed)}")

    # Test 5: Custom budget
    print("\nTest 5: Custom budget...")
    request = ContextRequest(
        operation_type="generate",
        custom_budget=2000  # Small budget
    )
    budget = await budgeter.calculate_budget(request)
    print(f"Custom budget of 2000 tokens allocated:")
    print(f"  Total: {budget.total}")
    print(f"  Available: {budget.available}")

    # Test 6: Recent changes adjustment
    print("\nTest 6: Recent files adjustment...")
    request = ContextRequest(
        operation_type="fix",
        target_file="recently_modified.py",
        recent_changes=["recently_modified.py", "helper.py"]
    )
    budget = await budgeter.calculate_budget(request)

    target_allocation = budget.allocations.get('target_file', 0)
    print(f"Target file allocation with recent changes: {target_allocation}")

    # Compare without recent changes
    request_no_recent = ContextRequest(
        operation_type="fix",
        target_file="recently_modified.py",
        recent_changes=[]
    )
    budget_no_recent = await budgeter.calculate_budget(request_no_recent)
    target_no_recent = budget_no_recent.allocations.get('target_file', 0)
    print(f"Target file allocation without recent changes: {target_no_recent}")

    if target_allocation > target_no_recent:
        print("✓ Recent files get increased allocation")

    # Test 7: Token estimation
    print("\nTest 7: Token estimation...")
    sample_text = """
    def hello_world():
        print("Hello, World!")
        return True

    class TestClass:
        def method(self, arg):
            return arg * 2
    """
    estimated = await budgeter.estimate_tokens(sample_text)
    print(f"Sample text length: {len(sample_text)} characters")
    print(f"Estimated tokens: {estimated}")

    print("\nToken budgeting test completed successfully!")


async def test_context_compression():
    """Test advanced context compression scenarios."""
    print("\n" + "="*50)
    print("Testing context compression scenarios...")

    token_counter = TokenCounter()
    budgeter = TokenBudgeter(token_counter, model_name="gpt-4")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        files = []
        for i in range(5):
            file_path = Path(temp_dir) / f"module_{i}.py"
            content = f"""
# Module {i}
import os
import sys

def function_{i}():
    '''Function {i} documentation.'''
    result = 0
    for j in range(100):
        result += j
    return result

class Class{i}:
    '''Class {i} documentation.'''

    def __init__(self):
        self.value = function_{i}()

    def method(self, arg):
        '''Method documentation.'''
        return self.value * arg
"""
            file_path.write_text(content)
            files.append(str(file_path))

        # Create context items
        items = []
        for i, file_path in enumerate(files):
            # Read actual content
            with open(file_path, 'r') as f:
                content = f.read()

            # Count tokens
            token_count = await token_counter.count_tokens(content, "gpt-4")

            # Create context item with varying importance
            item = ContextItem(
                path=f"module_{i}.py",
                content=content,
                importance=1.0 - (i * 0.1),  # Decreasing importance
                token_count=token_count,
                type="file",
                metadata={"size": len(content)}
            )
            items.append(item)

        # Test compression with different budgets
        budgets = [500, 1000, 2000, 5000]

        for budget_tokens in budgets:
            print(f"\nTesting with {budget_tokens} token budget:")

            request = ContextRequest(
                operation_type="explain",
                target_file="module_0.py",
                custom_budget=budget_tokens
            )
            budget = await budgeter.calculate_budget(request)

            compressed = await budgeter.compress_context(items, budget)

            total_tokens = sum(item.token_count for item in compressed)
            print(f"  Items included: {len(compressed)}/{len(items)}")
            print(f"  Total tokens: {total_tokens}/{budget.available}")
            print(f"  Utilization: {total_tokens/budget.available*100:.1f}%")

            # Show which files were included
            included = [Path(item.path).name for item in compressed]
            print(f"  Included files: {', '.join(included)}")

    print("\nContext compression test completed!")


if __name__ == "__main__":
    asyncio.run(test_token_budgeting())
    asyncio.run(test_context_compression())