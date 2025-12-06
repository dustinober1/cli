"""Tests for model and provider commands."""

import pytest
from unittest.mock import patch

from vibe_coder.commands.slash.commands.model import ModelCommand
from vibe_coder.commands.slash.commands.provider import ProviderCommand
from vibe_coder.commands.slash.base import CommandContext
from vibe_coder.types.config import AIProvider

@pytest.fixture
def context():
    return CommandContext(
        chat_history=[],
        current_provider=AIProvider(name="test", api_key="key", endpoint="url"),
        working_directory="."
    )

@pytest.mark.asyncio
async def test_model_command(context):
    cmd = ModelCommand()
    with patch("vibe_coder.commands.slash.commands.model.config_manager") as mock_config:
        response = await cmd.execute(["gpt-4"], context)
        assert "Model switched to: gpt-4" in response[1]
        mock_config.set_provider.assert_called_once()

@pytest.mark.asyncio
async def test_provider_command(context):
    cmd = ProviderCommand()
    with patch("vibe_coder.commands.slash.commands.provider.config_manager") as mock_config:
        mock_config.has_provider.return_value = True

        response = await cmd.execute(["openai"], context)
        assert "Provider switched to: openai" in response[1]
        mock_config.set_current_provider.assert_called_with("openai")

@pytest.mark.asyncio
async def test_provider_command_not_found(context):
    cmd = ProviderCommand()
    with patch("vibe_coder.commands.slash.commands.provider.config_manager") as mock_config:
        mock_config.has_provider.return_value = False

        response = await cmd.execute(["unknown"], context)
        assert "not found" in response[1]
