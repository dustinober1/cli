"""
Configuration validation utilities.

This module provides functions to validate configuration values before they're
stored. All validators return either True/False or a list of error messages.
"""

from typing import Optional
from urllib.parse import urlparse

from vibe_coder.types.config import AIProvider


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.

    An API key should:
    - Not be empty or None
    - Be a string
    - Be at least 10 characters long
    - Not contain spaces

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_api_key("sk-1234567890")
        True
        >>> validate_api_key("short")
        False
    """
    if not api_key or not isinstance(api_key, str):
        return False
    if len(api_key) < 10:
        return False
    if " " in api_key:
        return False
    return True


def validate_endpoint(endpoint: str) -> bool:
    """
    Validate API endpoint URL.

    An endpoint should:
    - Be a valid URL
    - Have http or https scheme
    - Have a domain/netloc
    - Can be localhost or custom domain

    Args:
        endpoint: URL to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_endpoint("https://api.openai.com/v1")
        True
        >>> validate_endpoint("http://localhost:8000")
        True
        >>> validate_endpoint("not-a-url")
        False
    """
    if not endpoint or not isinstance(endpoint, str):
        return False

    try:
        parsed = urlparse(endpoint)

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return False

        # Check netloc (domain/host)
        if not parsed.netloc:
            return False

        return True
    except Exception:
        return False


def validate_temperature(temperature: float) -> bool:
    """
    Validate temperature value.

    Temperature should be between 0.0 and 2.0 inclusive.

    Args:
        temperature: Temperature value to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_temperature(0.7)
        True
        >>> validate_temperature(0.0)
        True
        >>> validate_temperature(2.0)
        True
        >>> validate_temperature(3.0)
        False
    """
    if not isinstance(temperature, (int, float)):
        return False
    return 0.0 <= temperature <= 2.0


def validate_max_tokens(max_tokens: int) -> bool:
    """
    Validate max_tokens value.

    Max tokens should be a positive integer.

    Args:
        max_tokens: Max tokens value to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_max_tokens(100)
        True
        >>> validate_max_tokens(1)
        True
        >>> validate_max_tokens(0)
        False
        >>> validate_max_tokens(-100)
        False
    """
    if not isinstance(max_tokens, int):
        return False
    return max_tokens > 0


def validate_provider(provider: AIProvider) -> list[str]:
    """
    Validate all fields of an AIProvider.

    Returns a list of error messages. Empty list means valid.

    Validates:
    - name is not empty
    - api_key is valid format
    - endpoint is valid URL
    - temperature is in range 0.0-2.0
    - max_tokens is positive (if provided)

    Args:
        provider: AIProvider instance to validate

    Returns:
        List of error messages (empty if valid)

    Examples:
        >>> provider = AIProvider("test", "sk-test", "https://api.com")
        >>> errors = validate_provider(provider)
        >>> len(errors) == 0
        True
    """
    errors = []

    # Validate name
    if not provider.name or not isinstance(provider.name, str):
        errors.append("Provider name is required and must be a string")

    # Validate api_key
    if not validate_api_key(provider.api_key):
        errors.append("API key must be at least 10 characters, without spaces")

    # Validate endpoint
    if not validate_endpoint(provider.endpoint):
        errors.append("Endpoint must be a valid URL (http:// or https://)")

    # Validate temperature
    if not validate_temperature(provider.temperature):
        errors.append(f"Temperature must be 0.0-2.0, got {provider.temperature}")

    # Validate max_tokens if provided
    if provider.max_tokens is not None:
        if not validate_max_tokens(provider.max_tokens):
            errors.append(f"max_tokens must be positive, got {provider.max_tokens}")

    return errors


def is_localhost(url: str) -> bool:
    """
    Check if URL points to localhost.

    Returns True for localhost, 127.0.0.1, ::1, or local addresses.

    Args:
        url: URL to check

    Returns:
        True if localhost, False otherwise

    Examples:
        >>> is_localhost("http://localhost:8000")
        True
        >>> is_localhost("http://127.0.0.1:8000")
        True
        >>> is_localhost("https://api.openai.com")
        False
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc

        # Handle IPv6 with brackets
        if netloc.startswith("["):
            # IPv6 format: [::1]:port or [::1]
            netloc = netloc.split("]")[0] + "]"
        else:
            # IPv4 or hostname: remove port
            netloc = netloc.split(":")[0]

        return netloc in ("localhost", "127.0.0.1", "::1", "[::1]")
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.

    A valid URL should have http or https scheme and a domain.

    Args:
        url: String to check

    Returns:
        True if valid URL, False otherwise

    Examples:
        >>> is_valid_url("https://api.openai.com/v1")
        True
        >>> is_valid_url("http://localhost:8000")
        True
        >>> is_valid_url("not-a-url")
        False
    """
    return validate_endpoint(url)


def validate_provider_config(
    name: str,
    api_key: str,
    endpoint: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> list[str]:
    """
    Validate provider configuration from raw values.

    Useful for validating user input before creating an AIProvider.

    Args:
        name: Provider name
        api_key: API key
        endpoint: API endpoint URL
        temperature: Temperature (default: 0.7)
        max_tokens: Max tokens (optional)

    Returns:
        List of validation errors (empty if valid)

    Examples:
        >>> errors = validate_provider_config(
        ...     "test", "sk-test", "https://api.com", 0.7, 1000
        ... )
        >>> len(errors) == 0
        True
    """
    errors = []

    # Validate name
    if not name or not isinstance(name, str):
        errors.append("Name is required")

    # Validate api_key
    if not validate_api_key(api_key):
        errors.append("API key must be at least 10 characters, without spaces")

    # Validate endpoint
    if not validate_endpoint(endpoint):
        errors.append("Endpoint must be a valid URL")

    # Validate temperature
    if not validate_temperature(temperature):
        errors.append(f"Temperature must be 0.0-2.0, got {temperature}")

    # Validate max_tokens if provided
    if max_tokens is not None and not validate_max_tokens(max_tokens):
        errors.append(f"max_tokens must be positive, got {max_tokens}")

    return errors
