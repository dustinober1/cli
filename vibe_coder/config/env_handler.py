"""
Environment variable handler for configuration.

This module provides utilities for loading and saving configuration from/to
environment variables and .env files. Useful for containerized environments,
CI/CD pipelines, and local development with .env files.

Supported environment variables:
- VIBE_CODER_API_KEY: API key for authentication
- VIBE_CODER_ENDPOINT: API endpoint URL
- VIBE_CODER_MODEL: Model name to use
- VIBE_CODER_TEMPERATURE: Response temperature (0.0-2.0)
- VIBE_CODER_MAX_TOKENS: Maximum tokens in response
- VIBE_CODER_PROVIDER_NAME: Custom provider name (defaults to "env")
"""

import os
from typing import Optional

from dotenv import load_dotenv, set_key

from vibe_coder.types.config import AIProvider


def load_env_config() -> Optional[dict[str, Optional[str]]]:
    """
    Load configuration from environment variables.

    Looks for VIBE_CODER_* prefixed environment variables. First loads
    from .env file if it exists in the current directory.

    Environment variables recognized:
    - VIBE_CODER_API_KEY: API authentication key (required if using env config)
    - VIBE_CODER_ENDPOINT: API endpoint URL (required if using env config)
    - VIBE_CODER_MODEL: Model name (optional)
    - VIBE_CODER_TEMPERATURE: Temperature value (optional, must be 0.0-2.0)
    - VIBE_CODER_MAX_TOKENS: Max tokens (optional, must be positive)
    - VIBE_CODER_PROVIDER_NAME: Custom provider name (optional, defaults to "env")

    Returns:
        Dictionary with configuration if VIBE_CODER variables found, None otherwise

    Examples:
        >>> config = load_env_config()
        >>> if config:
        ...     print(f"Found API key: {config['api_key']}")
    """
    # Load from .env file if it exists
    load_dotenv()

    # Check for required variables
    api_key = os.getenv("VIBE_CODER_API_KEY")
    endpoint = os.getenv("VIBE_CODER_ENDPOINT")

    # If neither required var is set, return None
    if not api_key and not endpoint:
        return None

    # Build config dict with found variables
    config = {
        "api_key": api_key or "",
        "endpoint": endpoint or "",
        "model": os.getenv("VIBE_CODER_MODEL"),
        "temperature": os.getenv("VIBE_CODER_TEMPERATURE"),
        "max_tokens": os.getenv("VIBE_CODER_MAX_TOKENS"),
        "provider_name": os.getenv("VIBE_CODER_PROVIDER_NAME", "env"),
    }

    return config


def get_env_provider() -> Optional[AIProvider]:
    """
    Get an AIProvider object from environment variables.

    Loads configuration from environment variables and converts to AIProvider.
    Validates that required fields (api_key, endpoint) are present.

    Returns:
        AIProvider instance if environment variables are configured, None otherwise

    Raises:
        ValueError: If temperature is outside 0.0-2.0 range
        ValueError: If max_tokens is not a positive integer
        ValueError: If api_key or endpoint is missing

    Examples:
        >>> provider = get_env_provider()
        >>> if provider:
        ...     print(f"Using provider: {provider.name}")
    """
    config = load_env_config()
    if not config:
        return None

    # Validate required fields
    if not config.get("api_key"):
        raise ValueError("VIBE_CODER_API_KEY environment variable is required")
    if not config.get("endpoint"):
        raise ValueError("VIBE_CODER_ENDPOINT environment variable is required")

    # Parse temperature if provided
    temperature = 0.7  # Default
    temp_str = config.get("temperature")
    if temp_str:
        try:
            temperature = float(temp_str)
            if not (0.0 <= temperature <= 2.0):
                raise ValueError(f"Temperature must be 0.0-2.0, got {temperature}")
        except ValueError as e:
            raise ValueError(f"Invalid temperature value: {temp_str}") from e

    # Parse max_tokens if provided
    max_tokens = None
    tokens_str = config.get("max_tokens")
    if tokens_str:
        try:
            max_tokens = int(tokens_str)
            if max_tokens < 1:
                raise ValueError("max_tokens must be positive")
        except ValueError as e:
            raise ValueError(f"Invalid max_tokens value: {tokens_str}") from e

    # Create and return provider
    api_key: str = config.get("api_key") or ""
    endpoint: str = config.get("endpoint") or ""
    provider = AIProvider(
        name=config.get("provider_name") or "env",
        api_key=api_key,
        endpoint=endpoint,
        model=config.get("model"),
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return provider


def save_to_env(
    api_key: str,
    endpoint: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    provider_name: Optional[str] = None,
    env_file: str = ".env",
) -> None:
    """
    Save configuration to a .env file.

    Creates or updates a .env file with VIBE_CODER_* variables.
    Displays a warning about not committing .env files to version control.

    Args:
        api_key: API authentication key
        endpoint: API endpoint URL
        model: Optional model name
        temperature: Optional temperature (0.0-2.0)
        max_tokens: Optional max tokens
        provider_name: Optional custom provider name (defaults to "env")
        env_file: Path to .env file (defaults to ".env" in current directory)

    Raises:
        ValueError: If temperature or max_tokens are invalid

    Side effects:
        - Creates or updates .env file
        - Prints warning message about not committing .env

    Examples:
        >>> save_to_env(
        ...     api_key="sk-test",
        ...     endpoint="https://api.openai.com/v1",
        ...     model="gpt-4"
        ... )
    """
    # Validate inputs
    if temperature is not None and not (0.0 <= temperature <= 2.0):
        raise ValueError(f"Temperature must be 0.0-2.0, got {temperature}")
    if max_tokens is not None and max_tokens < 1:
        raise ValueError(f"max_tokens must be positive, got {max_tokens}")

    # Set variables
    set_key(env_file, "VIBE_CODER_API_KEY", api_key)
    set_key(env_file, "VIBE_CODER_ENDPOINT", endpoint)

    if model:
        set_key(env_file, "VIBE_CODER_MODEL", model)

    if temperature is not None:
        set_key(env_file, "VIBE_CODER_TEMPERATURE", str(temperature))

    if max_tokens is not None:
        set_key(env_file, "VIBE_CODER_MAX_TOKENS", str(max_tokens))

    if provider_name:
        set_key(env_file, "VIBE_CODER_PROVIDER_NAME", provider_name)

    # Print warning
    print(f"\n⚠️  Configuration saved to {env_file}")
    print("⚠️  Important: Do NOT commit .env files to version control!")
    print("⚠️  Add .env to your .gitignore file")
    print()


def has_env_config() -> bool:
    """
    Check if environment variable configuration is available.

    Returns:
        True if VIBE_CODER_API_KEY or VIBE_CODER_ENDPOINT is set

    Examples:
        >>> if has_env_config():
        ...     print("Environment configuration found")
    """
    return bool(os.getenv("VIBE_CODER_API_KEY") or os.getenv("VIBE_CODER_ENDPOINT"))
