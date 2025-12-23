"""
Dynamic token budgeting for AI context management.

This module provides intelligent token allocation based on context,
operation type, and conversation history.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from vibe_coder.analytics.token_counter import TokenCounter

from vibe_coder.intelligence.types import ContextItem, TokenBudget


@dataclass
class ContextRequest:
    """Request for context with token budgeting."""

    operation_type: str  # "generate", "fix", "refactor", "explain", "test", "document"
    target_file: Optional[str] = None
    conversation_history_length: int = 0
    recent_changes: List[str] = None  # List of recently modified files
    model_name: str = "gpt-4"
    custom_budget: Optional[int] = None

    def __post_init__(self):
        if self.recent_changes is None:
            self.recent_changes = []


class TokenBudgeter:
    """Manages dynamic token allocation based on context."""

    # Model-specific token limits
    MODEL_LIMITS = {
        "gpt-3.5-turbo": 16385,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "claude-3-haiku": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-opus": 200000,
    }

    # Operation-specific token allocations (percentage of total)
    OPERATION_ALLOCATIONS = {
        "generate": {
            "repository_overview": 0.1,
            "target_file": 0.4,
            "dependencies": 0.3,
            "related_patterns": 0.15,
            "reserve_response": 0.05,
        },
        "fix": {
            "repository_overview": 0.05,
            "target_file": 0.6,
            "dependencies": 0.2,
            "error_context": 0.1,
            "reserve_response": 0.05,
        },
        "refactor": {
            "repository_overview": 0.1,
            "target_file": 0.5,
            "dependents": 0.25,
            "patterns": 0.1,
            "reserve_response": 0.05,
        },
        "explain": {
            "repository_overview": 0.15,
            "target_file": 0.5,
            "metadata": 0.2,
            "reserve_response": 0.15,
        },
        "test": {
            "repository_overview": 0.1,
            "target_file": 0.4,
            "existing_tests": 0.3,
            "patterns": 0.1,
            "reserve_response": 0.1,
        },
        "document": {
            "repository_overview": 0.1,
            "target_file": 0.5,
            "documentation": 0.25,
            "reserve_response": 0.1,
        },
    }

    def __init__(self, token_counter: "TokenCounter", model_name: str = "gpt-4"):
        self.token_counter = token_counter
        self.model_name = model_name
        self.context_limit = self.MODEL_LIMITS.get(model_name, 8192)
        self.base_reserve_percentage = 0.3  # Default 30% for response

    async def calculate_budget(self, request: ContextRequest) -> TokenBudget:
        """
        Calculate optimal token allocation for a context request.

        Args:
            request: The context request with operation details.

        Returns:
            TokenBudget with allocations for different sections.
        """
        # Determine total available tokens
        if request.custom_budget:
            total_tokens = min(request.custom_budget, self.context_limit)
        else:
            # Reserve space for conversation history and response
            history_tokens = request.conversation_history_length
            reserve_for_response = int(self.context_limit * self.base_reserve_percentage)
            available_for_context = self.context_limit - history_tokens - reserve_for_response
            total_tokens = available_for_context

        # Get operation-specific allocations
        op_allocations = self.OPERATION_ALLOCATIONS.get(
            request.operation_type, self.OPERATION_ALLOCATIONS["generate"]
        )

        # Calculate initial allocations
        budget = TokenBudget(
            total=total_tokens,
            available=total_tokens,
            reserved_response=int(total_tokens * op_allocations.get("reserve_response", 0.05)),
        )

        # Allocate tokens for each section
        for section, percentage in op_allocations.items():
            if section == "reserve_response":
                continue

            tokens = int(total_tokens * percentage)
            if budget.allocate(section, tokens):
                pass  # Successfully allocated
            else:
                # Not enough tokens, allocate what's available
                available = budget.available
                budget.allocate(section, available)

        # Adjust for recently modified files
        if request.recent_changes:
            await self._adjust_for_recent_changes(budget, request.recent_changes, request)

        return budget

    async def _adjust_for_recent_changes(
        self, budget: TokenBudget, recent_files: List[str], request: ContextRequest
    ) -> None:
        """Adjust budget allocations based on recently modified files."""
        # Prioritize recently modified files in allocations
        if "target_file" in budget.allocations and request.target_file in recent_files:
            # Increase allocation for target file if recently modified
            increase = min(budget.available, int(budget.total * 0.1))
            budget.allocations["target_file"] += increase
            budget.available -= increase

    async def compress_context(
        self, items: List[ContextItem], budget: TokenBudget
    ) -> List[ContextItem]:
        """
        Compress context items to fit within token budget.

        Args:
            items: List of context items to include.
            budget: Token budget with allocations.

        Returns:
            Compressed list of context items.
        """
        # Sort items by importance and relevance
        sorted_items = sorted(items, key=lambda x: (-x.importance, x.token_count))

        result = []
        used_tokens = 0

        # Group items by type for allocation tracking
        allocations_used = {section: 0 for section in budget.allocations.keys()}

        for item in sorted_items:
            # Check if we have budget for this type of item
            item_type = item.type.lower()
            allocation_key = self._get_allocation_key(item_type, item.path)

            if allocation_key in allocations_used:
                allocation_limit = budget.allocations.get(allocation_key, 0)
                allocated = allocations_used[allocation_key]

                if allocated >= allocation_limit:
                    # Skip this item - allocation exceeded
                    continue

                # Check if adding this item would exceed budget
                if used_tokens + item.token_count > budget.available:
                    # Try to summarize the item
                    summarized_item = await self._summarize_item(item)
                    if (
                        summarized_item
                        and used_tokens + summarized_item.token_count <= budget.available
                    ):
                        result.append(summarized_item)
                        used_tokens += summarized_item.token_count
                        allocations_used[allocation_key] += summarized_item.token_count
                else:
                    # Include full item
                    result.append(item)
                    used_tokens += item.token_count
                    allocations_used[allocation_key] += item.token_count
            else:
                # No specific allocation, use available budget
                if used_tokens + item.token_count <= budget.available:
                    result.append(item)
                    used_tokens += item.token_count

        return result

    def _get_allocation_key(self, item_type: str, path: str) -> str:
        """Map item type to budget allocation key."""
        type_mapping = {
            "file": "target_file",
            "function": "target_file",
            "class": "target_file",
            "import": "dependencies",
            "summary": "repository_overview",
            "metadata": "metadata",
        }

        # Check if it's a dependency
        if "dependency" in path.lower() or "import" in path.lower():
            return "dependencies"

        # Check if it's the target file
        if "target" in path.lower() or path.endswith("/"):
            return "target_file"

        return type_mapping.get(item_type, "related_patterns")

    async def _summarize_item(self, item: ContextItem) -> Optional[ContextItem]:
        """
        Summarize a context item to reduce token count.

        Args:
            item: The context item to summarize.

        Returns:
            Summarized context item or None if cannot be summarized.
        """
        # For files, create a summary with key information
        if item.type == "file":
            # Extract just function/class signatures
            lines = item.content.split("\n")
            summary_lines = []

            for line in lines:
                line = line.strip()
                # Keep function and class definitions
                if line.startswith(("def ", "class ", "async def ")):
                    summary_lines.append(line)
                # Keep imports
                elif line.startswith(("import ", "from ")):
                    summary_lines.append(line)
                # Keep docstrings
                elif line.startswith('"""') or line.startswith("'''"):
                    summary_lines.append(line)

            if summary_lines:
                summary_content = "\n".join(summary_lines)
                estimated_tokens = len(summary_content) // 4  # Rough estimate

                return ContextItem(
                    path=item.path,
                    content=summary_content,
                    importance=item.importance,
                    token_count=estimated_tokens,
                    type="summary",
                    metadata={"summarized": True, "original_tokens": item.token_count},
                )

        # For other types, might return None or create a shorter version
        return None

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate tokens for.

        Returns:
            Estimated token count.
        """
        return await self.token_counter.count_tokens(text, self.model_name)

    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            "name": self.model_name,
            "context_limit": self.context_limit,
            "is_chat_model": True,  # Assume all models are chat models
            "supports_functions": "gpt-4" in self.model_name or "claude-3" in self.model_name,
        }

    def update_model(self, model_name: str) -> None:
        """Update the model being used."""
        self.model_name = model_name
        self.context_limit = self.MODEL_LIMITS.get(model_name, 8192)
