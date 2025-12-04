"""
Pricing database for AI models.

This module provides pricing information for various AI models
from different providers.
"""

from typing import Dict, Optional

from vibe_coder.analytics.types import ModelTier, TokenPricing

# Pricing database - updated as of December 2024
PRICING_DB: Dict[str, TokenPricing] = {
    # OpenAI Models
    "gpt-4o": TokenPricing(
        model_name="gpt-4o",
        input_price_per_1k=0.0025,
        output_price_per_1k=0.01,
        tier=ModelTier.STANDARD,
        context_window=128000,
        max_output=16384,
    ),
    "gpt-4o-mini": TokenPricing(
        model_name="gpt-4o-mini",
        input_price_per_1k=0.00015,
        output_price_per_1k=0.0006,
        tier=ModelTier.CHEAP,
        context_window=128000,
        max_output=16384,
    ),
    "gpt-4-turbo": TokenPricing(
        model_name="gpt-4-turbo",
        input_price_per_1k=0.01,
        output_price_per_1k=0.03,
        tier=ModelTier.EXPENSIVE,
        context_window=128000,
        max_output=4096,
    ),
    "gpt-4": TokenPricing(
        model_name="gpt-4",
        input_price_per_1k=0.03,
        output_price_per_1k=0.06,
        tier=ModelTier.EXPENSIVE,
        context_window=8192,
        max_output=4096,
    ),
    "gpt-3.5-turbo": TokenPricing(
        model_name="gpt-3.5-turbo",
        input_price_per_1k=0.0005,
        output_price_per_1k=0.0015,
        tier=ModelTier.CHEAP,
        context_window=16385,
        max_output=4096,
    ),
    "o1": TokenPricing(
        model_name="o1",
        input_price_per_1k=0.015,
        output_price_per_1k=0.06,
        tier=ModelTier.EXPENSIVE,
        context_window=200000,
        max_output=100000,
    ),
    "o1-mini": TokenPricing(
        model_name="o1-mini",
        input_price_per_1k=0.003,
        output_price_per_1k=0.012,
        tier=ModelTier.STANDARD,
        context_window=128000,
        max_output=65536,
    ),
    # Anthropic Models
    "claude-3-opus-20240229": TokenPricing(
        model_name="claude-3-opus-20240229",
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        tier=ModelTier.EXPENSIVE,
        context_window=200000,
        max_output=4096,
    ),
    "claude-3-5-sonnet-20241022": TokenPricing(
        model_name="claude-3-5-sonnet-20241022",
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=8192,
    ),
    "claude-3-sonnet-20240229": TokenPricing(
        model_name="claude-3-sonnet-20240229",
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=4096,
    ),
    "claude-3-5-haiku-20241022": TokenPricing(
        model_name="claude-3-5-haiku-20241022",
        input_price_per_1k=0.001,
        output_price_per_1k=0.005,
        tier=ModelTier.CHEAP,
        context_window=200000,
        max_output=8192,
    ),
    "claude-3-haiku-20240307": TokenPricing(
        model_name="claude-3-haiku-20240307",
        input_price_per_1k=0.00025,
        output_price_per_1k=0.00125,
        tier=ModelTier.CHEAP,
        context_window=200000,
        max_output=4096,
    ),
    # Aliases for common model names
    "claude-3-opus": TokenPricing(
        model_name="claude-3-opus",
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        tier=ModelTier.EXPENSIVE,
        context_window=200000,
        max_output=4096,
    ),
    "claude-3-5-sonnet": TokenPricing(
        model_name="claude-3-5-sonnet",
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=8192,
    ),
    "claude-3-sonnet": TokenPricing(
        model_name="claude-3-sonnet",
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=4096,
    ),
    "claude-3-haiku": TokenPricing(
        model_name="claude-3-haiku",
        input_price_per_1k=0.00025,
        output_price_per_1k=0.00125,
        tier=ModelTier.CHEAP,
        context_window=200000,
        max_output=4096,
    ),
    # Local/Free Models
    "ollama-local": TokenPricing(
        model_name="ollama-local",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.FREE,
        context_window=8192,
        max_output=4096,
    ),
    "llama-3": TokenPricing(
        model_name="llama-3",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.FREE,
        context_window=8192,
        max_output=4096,
    ),
    "llama-3.1": TokenPricing(
        model_name="llama-3.1",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.FREE,
        context_window=128000,
        max_output=4096,
    ),
    "mistral": TokenPricing(
        model_name="mistral",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.FREE,
        context_window=8192,
        max_output=4096,
    ),
    "codellama": TokenPricing(
        model_name="codellama",
        input_price_per_1k=0.0,
        output_price_per_1k=0.0,
        tier=ModelTier.FREE,
        context_window=16384,
        max_output=4096,
    ),
}


def get_pricing(model: str) -> Optional[TokenPricing]:
    """
    Get pricing for a model.

    Args:
        model: Model name or identifier

    Returns:
        TokenPricing if found, None otherwise
    """
    # Direct lookup
    if model in PRICING_DB:
        return PRICING_DB[model]

    # Try normalized name
    model_lower = model.lower()
    for name, pricing in PRICING_DB.items():
        if name.lower() == model_lower:
            return pricing

    # Try partial match
    for name, pricing in PRICING_DB.items():
        if name.lower() in model_lower or model_lower in name.lower():
            return pricing

    return None


def get_default_pricing(provider: str = "openai") -> TokenPricing:
    """
    Get default pricing for a provider.

    Args:
        provider: Provider name

    Returns:
        Default TokenPricing for the provider
    """
    defaults = {
        "openai": PRICING_DB["gpt-4o-mini"],
        "anthropic": PRICING_DB["claude-3-haiku"],
        "ollama": PRICING_DB["ollama-local"],
    }

    return defaults.get(
        provider.lower(),
        TokenPricing(
            model_name="unknown",
            input_price_per_1k=0.001,
            output_price_per_1k=0.002,
            tier=ModelTier.STANDARD,
        ),
    )


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Estimate cost for a request.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    pricing = get_pricing(model)
    if not pricing:
        pricing = get_default_pricing()

    return pricing.calculate_cost(input_tokens, output_tokens)


def list_models_by_tier(tier: ModelTier) -> list:
    """
    List all models in a pricing tier.

    Args:
        tier: Pricing tier

    Returns:
        List of model names
    """
    return [name for name, pricing in PRICING_DB.items() if pricing.tier == tier]


def get_cheapest_model(provider: Optional[str] = None) -> Optional[str]:
    """
    Get the cheapest model, optionally filtered by provider.

    Args:
        provider: Optional provider name to filter by

    Returns:
        Model name or None if no models found
    """
    models = []
    for name, pricing in PRICING_DB.items():
        if provider:
            # Simple provider detection from model name
            if provider.lower() == "openai" and "gpt" in name.lower():
                models.append((name, pricing))
            elif provider.lower() == "anthropic" and "claude" in name.lower():
                models.append((name, pricing))
            elif provider.lower() == "ollama" and pricing.tier == ModelTier.FREE:
                models.append((name, pricing))
        else:
            models.append((name, pricing))

    if not models:
        return None

    # Sort by total cost (input + output at 1k tokens each)
    models.sort(key=lambda x: x[1].input_price_per_1k + x[1].output_price_per_1k)
    return models[0][0]
