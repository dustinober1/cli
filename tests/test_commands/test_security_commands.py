"""Tests for security commands."""

import pytest
from unittest.mock import patch, AsyncMock

from vibe_coder.commands.slash.commands.security import SecurityScanCommand, SecretsCommand
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
async def test_security_scan_command_no_bandit(context):
    with patch("shutil.which", return_value=None):
        cmd = SecurityScanCommand()
        response = await cmd.execute([], context)
        assert "requires `bandit`" in response

@pytest.mark.asyncio
async def test_security_scan_command_success(context):
    with patch("shutil.which", return_value="/usr/bin/bandit"):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Scan results", b"")
            mock_exec.return_value = mock_process

            cmd = SecurityScanCommand()
            response = await cmd.execute([], context)

            assert "Security Scan Results" in response
            assert "Scan results" in response

@pytest.mark.asyncio
async def test_secrets_command(context):
    cmd = SecretsCommand()
    with patch("os.walk") as mock_walk:
        mock_walk.return_value = [(".", [], ["secret.py"])]

        with patch("builtins.open") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "api_key = '12345678901234567890'"

            response = await cmd.execute([], context)
            assert "Potential Secrets Found" in response
            assert "API Key" in response

@pytest.mark.asyncio
async def test_secrets_command_clean(context):
    cmd = SecretsCommand()
    with patch("os.walk") as mock_walk:
        mock_walk.return_value = []

        response = await cmd.execute([], context)
        assert "No obvious secrets found" in response
