"""
Token counter for estimating token usage.

This module provides token counting capabilities using
tiktoken for OpenAI models and estimation for other models.
"""

from typing import Dict, List, Optional, Tuple

from vibe_coder.analytics.pricing import get_pricing


class TokenCounter:
    """Estimate token usage before API calls."""

    # Default estimation factors for different model families
    TOKEN_ESTIMATION_FACTORS: Dict[str, Dict[str, float]] = {
        "gpt-4": {"chars_per_token": 4.0, "overhead": 1.1},
        "gpt-3.5": {"chars_per_token": 4.0, "overhead": 1.1},
        "gpt-4o": {"chars_per_token": 4.0, "overhead": 1.1},
        "claude": {"chars_per_token": 3.5, "overhead": 1.15},
        "llama": {"chars_per_token": 3.8, "overhead": 1.1},
        "mistral": {"chars_per_token": 3.8, "overhead": 1.1},
        "default": {"chars_per_token": 4.0, "overhead": 1.15},
    }

    def __init__(self):
        self._tiktoken_available = self._check_tiktoken()
        self._anthropic_available = self._check_anthropic()
        self._cache: Dict[str, int] = {}

    def _check_tiktoken(self) -> bool:
        """Check if tiktoken is available."""
        try:
            import tiktoken  # noqa: F401

            return True
        except ImportError:
            return False

    def _check_anthropic(self) -> bool:
        """Check if anthropic SDK is available for token counting."""
        try:
            import anthropic  # noqa: F401

            return True
        except ImportError:
            return False

    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count or estimate tokens for text.

        Uses:
        1. tiktoken for OpenAI models (exact)
        2. Estimation formula for other models

        Args:
            text: Text to count tokens for
            model: Model name for token counting

        Returns:
            Token count
        """
        # Check cache
        cache_key = f"{model}:{hash(text)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        model_lower = model.lower()

        # Use tiktoken for OpenAI models
        if self._tiktoken_available and self._is_openai_model(model_lower):
            count = self._count_tiktoken(text, model)
        else:
            count = self._estimate_tokens(text, model)

        # Cache result
        self._cache[cache_key] = count
        return count

    def count_tokens_sync(self, text: str, model: str) -> int:
        """Synchronous version of count_tokens."""
        model_lower = model.lower()

        if self._tiktoken_available and self._is_openai_model(model_lower):
            return self._count_tiktoken(text, model)
        return self._estimate_tokens(text, model)

    def _is_openai_model(self, model: str) -> bool:
        """Check if model is an OpenAI model."""
        openai_prefixes = ("gpt-", "o1", "text-", "davinci", "curie", "babbage", "ada")
        return any(model.startswith(prefix) for prefix in openai_prefixes)

    def _count_tiktoken(self, text: str, model: str) -> int:
        """Use tiktoken for exact OpenAI token count."""
        try:
            import tiktoken

            # Map model names to encoding
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for newer models
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))
        except Exception:
            return self._estimate_tokens(text, model)

    def _estimate_tokens(self, text: str, model: str) -> int:
        """Estimate tokens using formula."""
        model_lower = model.lower()

        # Find matching estimation factors
        factors = self.TOKEN_ESTIMATION_FACTORS["default"]
        for prefix, model_factors in self.TOKEN_ESTIMATION_FACTORS.items():
            if prefix in model_lower:
                factors = model_factors
                break

        # Calculate token estimate
        base_tokens = len(text) / factors["chars_per_token"]
        return int(base_tokens * factors["overhead"])

    async def count_messages(self, messages: List[Dict[str, str]], model: str) -> int:
        """
        Count tokens for a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name

        Returns:
            Total token count
        """
        total = 0

        # Add per-message overhead
        per_message_overhead = 4 if self._is_openai_model(model.lower()) else 3

        for message in messages:
            content = message.get("content", "")
            role = message.get("role", "")

            # Count content tokens
            total += await self.count_tokens(content, model)

            # Add role tokens (approximation)
            total += await self.count_tokens(role, model)

            # Add message separator overhead
            total += per_message_overhead

        # Add conversation overhead
        total += 3  # Reply priming

        return total

    async def estimate_request_cost(
        self,
        prompt: str,
        model: str,
        estimated_output_tokens: int = 500,
    ) -> Tuple[int, int, float]:
        """
        Estimate cost before making request.

        Args:
            prompt: The prompt text
            model: Model name
            estimated_output_tokens: Expected output tokens

        Returns:
            Tuple of (input_tokens, output_tokens, cost_usd)
        """
        input_tokens = await self.count_tokens(prompt, model)

        pricing = get_pricing(model)
        if not pricing:
            return input_tokens, estimated_output_tokens, 0.0

        cost = pricing.calculate_cost(input_tokens, estimated_output_tokens)
        return input_tokens, estimated_output_tokens, cost

    async def estimate_messages_cost(
        self,
        messages: List[Dict[str, str]],
        model: str,
        estimated_output_tokens: int = 500,
    ) -> Tuple[int, int, float]:
        """
        Estimate cost for a message-based request.

        Args:
            messages: List of message dicts
            model: Model name
            estimated_output_tokens: Expected output tokens

        Returns:
            Tuple of (input_tokens, output_tokens, cost_usd)
        """
        input_tokens = await self.count_messages(messages, model)

        pricing = get_pricing(model)
        if not pricing:
            return input_tokens, estimated_output_tokens, 0.0

        cost = pricing.calculate_cost(input_tokens, estimated_output_tokens)
        return input_tokens, estimated_output_tokens, cost

    def get_token_limit(self, model: str) -> int:
        """
        Get token limit for a model.

        Args:
            model: Model name

        Returns:
            Context window size
        """
        pricing = get_pricing(model)
        if pricing:
            return pricing.context_window
        return 4096  # Default

    def get_output_limit(self, model: str) -> int:
        """
        Get output token limit for a model.

        Args:
            model: Model name

        Returns:
            Maximum output tokens
        """
        pricing = get_pricing(model)
        if pricing:
            return pricing.max_output
        return 4096  # Default

    def will_exceed_limit(self, text: str, model: str, buffer: int = 500) -> bool:
        """
        Check if text will exceed model's context limit.

        Args:
            text: Text to check
            model: Model name
            buffer: Token buffer for response

        Returns:
            True if text exceeds limit
        """
        tokens = self.count_tokens_sync(text, model)
        limit = self.get_token_limit(model)
        return tokens + buffer > limit

    def truncate_to_limit(
        self,
        text: str,
        model: str,
        max_tokens: Optional[int] = None,
        keep_end: bool = False,
    ) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            model: Model name
            max_tokens: Optional specific limit
            keep_end: Keep end instead of beginning

        Returns:
            Truncated text
        """
        limit = max_tokens or (self.get_token_limit(model) - 500)
        current_tokens = self.count_tokens_sync(text, model)

        if current_tokens <= limit:
            return text

        # Estimate character ratio
        char_ratio = len(text) / current_tokens
        target_chars = int(limit * char_ratio * 0.95)  # 5% buffer

        if keep_end:
            return "..." + text[-target_chars:]
        return text[:target_chars] + "..."

    def clear_cache(self) -> None:
        """Clear token count cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "cached_counts": len(self._cache),
            "tiktoken_available": self._tiktoken_available,
            "anthropic_available": self._anthropic_available,
        }


# Module-level instance for convenience
token_counter = TokenCounter()
