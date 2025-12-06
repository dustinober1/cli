"""Tests for workflow commands."""

import pytest
from vibe_coder.commands.slash.commands.workflow import AliasCommand, WorkflowCommand, BatchCommand
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
async def test_alias_command(context):
    cmd = AliasCommand()
    response = await cmd.execute(["test", "echo"], context)
    assert "Alias 'test' created" in response

@pytest.mark.asyncio
async def test_workflow_command(context):
    cmd = WorkflowCommand()
    response = await cmd.execute(["ship"], context)
    assert "logic defined but execution requires parser access" in response

@pytest.mark.asyncio
async def test_workflow_command_not_found(context):
    cmd = WorkflowCommand()
    response = await cmd.execute(["unknown"], context)
    assert "not found" in response

@pytest.mark.asyncio
async def test_batch_command(context):
    cmd = BatchCommand()
    response = await cmd.execute(["file.txt"], context)
    assert "requires parser access" in response
