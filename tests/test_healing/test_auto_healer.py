"""Tests for the AutoHealer class."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.healing.auto_healer import AutoHealer
from vibe_coder.healing.types import (
    HealingAttempt,
    HealingConfig,
    HealingResult,
    ValidationResult,
    ValidationStrategy,
)
from vibe_coder.healing.validators import CodeValidator


class TestAutoHealerInitialization:
    """Test AutoHealer initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        mock_api_client = MagicMock()
        healer = AutoHealer(mock_api_client)

        assert healer.api_client == mock_api_client
        assert isinstance(healer.validator, CodeValidator)
        assert isinstance(healer.config, HealingConfig)
        assert healer.backup_dir == Path.home() / ".vibe" / "backups"
        assert healer.healing_history == []

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        mock_api_client = MagicMock()
        mock_validator = MagicMock()
        custom_config = HealingConfig(max_attempts=5)
        custom_backup = "/tmp/backups"

        healer = AutoHealer(
            api_client=mock_api_client,
            validator=mock_validator,
            config=custom_config,
            backup_dir=custom_backup,
        )

        assert healer.api_client == mock_api_client
        assert healer.validator == mock_validator
        assert healer.config == custom_config
        assert healer.backup_dir == Path(custom_backup)

    def test_backup_dir_creation(self):
        """Test that backup directory is created when needed."""
        mock_api_client = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "backups"
            AutoHealer(mock_api_client, backup_dir=str(backup_dir))
            assert backup_dir.exists()


class TestHealCode:
    """Test the heal_code method."""

    @pytest.mark.asyncio
    async def test_heal_valid_code(self):
        """Test healing already valid code."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        # Return valid result
        mock_validator.validate.return_value = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX)
        ]

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        code = "def hello():\n    return 'world'"
        result = await healer.heal_code(code, "python")

        assert result.success is True
        assert result.original_code == code
        assert result.final_code == code
        assert len(result.attempts) == 0
        assert len(result.errors_fixed) == 0
        assert len(result.errors_remaining) == 0

        # API should not be called for valid code
        mock_api_client.send_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_heal_invalid_code_success(self):
        """Test successful healing of invalid code."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        # First call returns invalid, second returns valid
        mock_validator.validate.side_effect = [
            [
                ValidationResult(
                    is_valid=False,
                    errors=["Syntax error: invalid syntax"],
                    strategy=ValidationStrategy.SYNTAX,
                )
            ],
            [ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX)],
        ]

        # Mock AI response
        mock_response = MagicMock()
        mock_response.content = "def hello():\n    return 'world'"
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        code = "def hello(\n    return 'world'"  # Invalid syntax
        result = await healer.heal_code(code, "python")

        assert result.success is True
        assert result.original_code == code
        assert result.final_code == "def hello():\n    return 'world'"
        assert len(result.attempts) == 1
        assert result.attempts[0].success is True
        assert len(result.errors_fixed) == 1
        assert len(result.errors_remaining) == 0

    @pytest.mark.asyncio
    async def test_heal_with_max_attempts(self):
        """Test healing with maximum attempts reached."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        # Always return invalid
        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False,
                errors=["Syntax error: invalid syntax"],
                strategy=ValidationStrategy.SYNTAX,
            )
        ]

        # Mock AI response (same code, no improvement)
        mock_response = MagicMock()
        mock_response.content = "def hello(\n    return 'world'"
        mock_api_client.send_request.return_value = mock_response

        config = HealingConfig(max_attempts=2)
        healer = AutoHealer(mock_api_client, validator=mock_validator, config=config)

        code = "def hello(\n    return 'world'"
        result = await healer.heal_code(code, "python")

        assert result.success is False
        assert len(result.attempts) == 2
        assert mock_api_client.send_request.call_count == 2

    @pytest.mark.asyncio
    async def test_heal_with_custom_prompt(self):
        """Test healing with custom prompt."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False,
                errors=["Type error: unsupported operand type"],
                strategy=ValidationStrategy.TYPE_CHECK,
            )
        ]

        mock_response = MagicMock()
        mock_response.content = "def add(a: int, b: int) -> int:\n    return a + b"
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        custom_prompt = "Fix this code: {code}\nErrors: {errors}"
        code = "def add(a, b):\n    return a + b"
        result = await healer.heal_code(code, "python", custom_prompt=custom_prompt)

        assert len(result.attempts) == 1
        # Check that custom prompt was used
        call_args = mock_api_client.send_request.call_args[0][0]
        prompt = call_args[1].content
        assert "Fix this code:" in prompt

    @pytest.mark.asyncio
    async def test_heal_with_backup(self):
        """Test healing with backup creation."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            )
        ]

        mock_response = MagicMock()
        mock_response.content = "fixed code"
        mock_api_client.send_request.return_value = mock_response

        config = HealingConfig(save_before_healing=True)
        healer = AutoHealer(mock_api_client, validator=mock_validator, config=config)

        with patch("pathlib.Path.write_text") as mock_write:
            await healer.heal_code(code="broken code", language="python", file_path="/tmp/test.py")
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_heal_multiple_strategies(self):
        """Test healing with multiple validation strategies."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        # Multiple strategy failures
        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            ),
            ValidationResult(
                is_valid=False, errors=["Type error"], strategy=ValidationStrategy.TYPE_CHECK
            ),
        ]

        mock_response = MagicMock()
        mock_response.content = "fixed code"
        mock_api_client.send_request.return_value = mock_response

        strategies = [ValidationStrategy.SYNTAX, ValidationStrategy.TYPE_CHECK]
        config = HealingConfig(strategies=strategies)
        healer = AutoHealer(mock_api_client, validator=mock_validator, config=config)

        await healer.heal_code("broken code", "python")

        # Verify all strategies were checked
        assert mock_validator.validate.call_count == 2

    @pytest.mark.asyncio
    async def test_heal_with_ai_failure(self):
        """Test healing when AI request fails."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            )
        ]

        # AI request fails
        mock_api_client.send_request.side_effect = Exception("AI service unavailable")

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        code = "broken code"
        result = await healer.heal_code(code, "python")

        assert result.success is False
        assert len(result.attempts) == 1
        assert "Error: AI service unavailable" in result.attempts[0].ai_response

    @pytest.mark.asyncio
    async def test_heal_with_partial_success(self):
        """Test healing with partial error fixing."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        # Initial errors
        initial_errors = ["Syntax error", "Type error", "Lint error"]
        remaining_errors = ["Type error"]  # Only syntax and lint fixed

        mock_validator.validate.side_effect = [
            [
                ValidationResult(
                    is_valid=False, errors=initial_errors[:1], strategy=ValidationStrategy.SYNTAX
                ),
                ValidationResult(
                    is_valid=False,
                    errors=initial_errors[1:],
                    strategy=ValidationStrategy.TYPE_CHECK,
                ),
                ValidationResult(
                    is_valid=False, errors=initial_errors[2:], strategy=ValidationStrategy.LINT
                ),
            ],
            [
                ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX),
                ValidationResult(
                    is_valid=False, errors=remaining_errors, strategy=ValidationStrategy.TYPE_CHECK
                ),
                ValidationResult(is_valid=True, strategy=ValidationStrategy.LINT),
            ],
        ]

        mock_response = MagicMock()
        mock_response.content = "partially fixed code"
        mock_api_client.send_request.return_value = mock_response

        config = HealingConfig(max_attempts=1)
        healer = AutoHealer(mock_api_client, validator=mock_validator, config=config)

        result = await healer.heal_code("broken code", "python")

        assert result.success is True  # Some errors were fixed
        assert len(result.errors_fixed) == 2
        assert len(result.errors_remaining) == 1

    @pytest.mark.asyncio
    async def test_heal_with_no_code_changes(self):
        """Test healing when AI returns same code."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            )
        ]

        # AI returns same code
        code = "broken code"
        mock_response = MagicMock()
        mock_response.content = code
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(
            mock_api_client, validator=mock_validator, config=HealingConfig(max_attempts=2)
        )

        result = await healer.heal_code(code, "python")

        # Should add context about previous attempt
        assert len(result.attempts) == 2
        assert "PREVIOUS ATTEMPT RETURNED SAME CODE" in result.attempts[0].ai_prompt


class TestHealFile:
    """Test the heal_file method."""

    @pytest.mark.asyncio
    async def test_heal_file_success(self):
        """Test successful file healing."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            ),
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX),
        ]

        mock_response = MagicMock()
        mock_response.content = "fixed code"
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("broken code")
            temp_path = f.name

        try:
            result = await healer.heal_file(temp_path)
            assert result.success is True
            assert result.original_code == "broken code"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_heal_file_not_found(self):
        """Test healing non-existent file."""
        healer = AutoHealer(MagicMock())

        with pytest.raises(FileNotFoundError, match="File not found"):
            await healer.heal_file("/nonexistent/file.py")

    @pytest.mark.asyncio
    async def test_heal_file_with_save(self):
        """Test healing file with save option."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(
                is_valid=False, errors=["Syntax error"], strategy=ValidationStrategy.SYNTAX
            ),
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX),
        ]

        mock_response = MagicMock()
        mock_response.content = "fixed code"
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("broken code")
            temp_path = f.name

        try:
            result = await healer.heal_file(temp_path, save_result=True)
            assert result.success is True

            # Check file was updated
            with open(temp_path, "r") as f:
                assert f.read() == "fixed code"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_heal_file_language_detection(self):
        """Test language detection from file extension."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX)
        ]

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("function test() {}")
            temp_path = f.name

        try:
            result = await healer.heal_file(temp_path)
            assert result.success is True
            # Should detect JavaScript from .js extension
            mock_validator.validate.assert_called_with(
                "function test() {}", "javascript", healer.config.strategies, temp_path
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestHelperMethods:
    """Test helper methods."""

    def test_build_fix_prompt(self):
        """Test prompt building."""
        healer = AutoHealer(MagicMock())

        prompt = healer._build_fix_prompt(
            code="def test():\n    pass",
            language="python",
            errors="IndentationError: expected an indented block",
            warnings="Unused variable 'x'",
            context="This is a test function",
            attempt_num=1,
        )

        assert "Fix the following python code" in prompt
        assert "def test():" in prompt
        assert "IndentationError" in prompt
        assert "Unused variable" in prompt
        assert "This is a test function" in prompt

    def test_extract_code_from_response_markdown(self):
        """Test code extraction from markdown."""
        healer = AutoHealer(MagicMock())

        response = """Here's the fixed code:

```python
def hello():
    return "world"
```"""

        extracted = healer._extract_code_from_response(response, "python")
        assert extracted == 'def hello():\n    return "world"'

    def test_extract_code_from_response_plain(self):
        """Test code extraction from plain text."""
        healer = AutoHealer(MagicMock())

        response = 'def hello():\n    return "world"'

        extracted = healer._extract_code_from_response(response, "python")
        assert extracted == 'def hello():\n    return "world"'

    def test_extract_code_fallback(self):
        """Test code extraction fallback."""
        healer = AutoHealer(MagicMock())

        response = "Some explanatory text\nand more text"

        extracted = healer._extract_code_from_response(response, "python")
        assert extracted == response

    def test_looks_like_code_python(self):
        """Test Python code detection."""
        healer = AutoHealer(MagicMock())

        assert healer._looks_like_code("def test():", "python")
        assert healer._looks_like_code("import os", "python")
        assert healer._looks_like_code("    x = 1", "python")
        assert not healer._looks_like_code("This is a comment", "python")

    def test_collect_errors(self):
        """Test error collection."""
        healer = AutoHealer(MagicMock())

        results = [
            ValidationResult(errors=["Error 1", "Error 2"]),
            ValidationResult(errors=["Error 3"]),
            ValidationResult(errors=[]),
        ]

        errors = healer._collect_errors(results)
        assert errors == ["Error 1", "Error 2", "Error 3"]

    def test_collect_warnings(self):
        """Test warning collection."""
        healer = AutoHealer(MagicMock())

        results = [
            ValidationResult(warnings=["Warning 1"]),
            ValidationResult(warnings=["Warning 2", "Warning 3"]),
            ValidationResult(warnings=[]),
        ]

        warnings = healer._collect_warnings(results)
        assert warnings == ["Warning 1", "Warning 2", "Warning 3"]

    def test_detect_language(self):
        """Test language detection from file path."""
        healer = AutoHealer(MagicMock())

        assert healer._detect_language("test.py") == "python"
        assert healer._detect_language("test.js") == "javascript"
        assert healer._detect_language("test.ts") == "typescript"
        assert healer._detect_language("test.go") == "go"
        assert healer._detect_language("test.rs") == "rust"
        assert healer._detect_language("test.java") == "java"
        assert healer._detect_language("test.unknown") == "text"

    def test_create_backup(self):
        """Test backup creation."""
        healer = AutoHealer(MagicMock())

        with tempfile.TemporaryDirectory() as tmpdir:
            healer.backup_dir = Path(tmpdir) / "backups"
            code = "test code"

            backup_path = healer._create_backup("test.py", code)

            assert backup_path.exists()
            assert backup_path.name.startswith("test.py.")
            assert backup_path.name.endswith(".bak")
            assert backup_path.read_text() == code

    def test_restore_backup(self):
        """Test backup restoration."""
        healer = AutoHealer(MagicMock())

        with tempfile.TemporaryDirectory() as tmpdir:
            healer.backup_dir = Path(tmpdir) / "backups"
            healer.backup_dir.mkdir()

            # Create backup
            backup_path = healer.backup_dir / "test.py.20240101_120000.bak"
            backup_path.write_text("backup content")

            # Create target file
            target_path = Path(tmpdir) / "test.py"
            target_path.write_text("original content")

            result = healer.restore_backup(str(target_path))

            assert result is True
            assert target_path.read_text() == "backup content"

    def test_restore_backup_no_backups(self):
        """Test restore with no backups available."""
        healer = AutoHealer(MagicMock())

        result = healer.restore_backup("nonexistent.py")
        assert result is False

    def test_list_backups(self):
        """Test listing backups."""
        healer = AutoHealer(MagicMock())

        with tempfile.TemporaryDirectory() as tmpdir:
            healer.backup_dir = Path(tmpdir) / "backups"
            healer.backup_dir.mkdir()

            # Create some backups
            for i in range(3):
                backup_path = healer.backup_dir / f"test.py.2024010{i}_120000.bak"
                backup_path.write_text(f"backup {i}")

            backups = healer.list_backups("test.py")
            assert len(backups) == 3
            assert all("test.py" in b.name for b in backups)

    def test_list_backups_no_directory(self):
        """Test listing backups with no directory."""
        healer = AutoHealer(MagicMock())
        healer.backup_dir = Path("/nonexistent")

        backups = healer.list_backups()
        assert backups == []

    def test_get_healing_stats_empty(self):
        """Test getting stats with no history."""
        healer = AutoHealer(MagicMock())

        stats = healer.get_healing_stats()

        assert stats["total_healings"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_attempts"] == 0.0
        assert stats["avg_time"] == 0.0
        assert stats["total_errors_fixed"] == 0

    def test_get_healing_stats_with_history(self):
        """Test getting stats with healing history."""
        healer = AutoHealer(MagicMock())

        # Add some mock history
        healer.healing_history = [
            HealingResult(
                success=True,
                original_code="code1",
                final_code="fixed1",
                attempts=[
                    HealingAttempt(
                        1, "code1", "fixed1", [], "", "", datetime.now().isoformat(), True
                    )
                ],
                total_time=1.5,
                errors_fixed=["error1", "error2"],
                errors_remaining=[],
            ),
            HealingResult(
                success=False,
                original_code="code2",
                final_code="code2",
                attempts=[
                    HealingAttempt(
                        1, "code2", "code2", [], "", "", datetime.now().isoformat(), False
                    )
                ],
                total_time=2.0,
                errors_fixed=[],
                errors_remaining=["error3"],
            ),
        ]

        stats = healer.get_healing_stats()

        assert stats["total_healings"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate"] == 50.0
        assert stats["avg_attempts"] == 1.0
        assert stats["avg_time"] == 1.75
        assert stats["total_errors_fixed"] == 2


class TestCodeExtraction:
    """Test code extraction edge cases."""

    def test_extract_code_with_language_specific_patterns(self):
        """Test code extraction with language-specific patterns."""
        healer = AutoHealer(MagicMock())

        # Test with different language patterns
        js_response = "```javascript\nfunction test() { return true; }\n```"
        extracted = healer._extract_code_from_response(js_response, "javascript")
        assert "function test()" in extracted

        # Test with generic python pattern
        py_response = "```python\nprint('hello')\n```"
        extracted = healer._extract_code_from_response(py_response, "python")
        assert extracted == "print('hello')"

    def test_extract_code_mixed_content(self):
        """Test code extraction from mixed content."""
        healer = AutoHealer(MagicMock())

        response = """Here's what I found wrong:

The issue is with the indentation. Here's the fix:

```python
def hello():
    print("world")
```

This should fix the problem."""

        extracted = healer._extract_code_from_response(response, "python")
        assert extracted == 'def hello():\n    print("world")'

    def test_extract_code_no_code_blocks(self):
        """Test extraction when no code blocks are present."""
        healer = AutoHealer(MagicMock())

        # Response with no code blocks but looks like code
        response = "def test():\n    return 'Hello, World!'"

        extracted = healer._extract_code_from_response(response, "python")
        assert extracted == response

    def test_extract_code_with_explanations(self):
        """Test extraction filtering out explanations."""
        healer = AutoHealer(MagicMock())

        response = """# Here's the fixed function
def test():
    # This is a comment
    return True

# End of function"""

        extracted = healer._extract_code_from_response(response, "python")
        # Should include actual code but filter some explanatory text
        assert "def test():" in extracted
        assert "return True" in extracted


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error conditions."""

    async def test_heal_with_timeout(self):
        """Test healing with timeout configuration."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(is_valid=False, errors=["Error"], strategy=ValidationStrategy.SYNTAX)
        ]

        # Simulate timeout by making AI take too long
        async def slow_send_request(*args, **kwargs):
            await asyncio.sleep(2)
            return MagicMock(content="fixed code")

        mock_api_client.send_request = slow_send_request

        config = HealingConfig(timeout_seconds=1)
        healer = AutoHealer(mock_api_client, validator=mock_validator, config=config)

        # This should not hang indefinitely
        result = await healer.heal_code("broken", "python")
        assert len(result.attempts) == 1

    async def test_heal_empty_code(self):
        """Test healing empty code."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX)
        ]

        healer = AutoHealer(mock_api_client, validator=mock_validator)

        result = await healer.heal_code("", "python")
        assert result.success is True
        assert result.final_code == ""

    async def test_heal_with_context_accumulation(self):
        """Test context accumulation across attempts."""
        mock_api_client = AsyncMock()
        mock_validator = AsyncMock()

        mock_validator.validate.return_value = [
            ValidationResult(is_valid=False, errors=["Error"], strategy=ValidationStrategy.SYNTAX)
        ]

        # AI returns same code each time
        mock_response = MagicMock()
        mock_response.content = "same broken code"
        mock_api_client.send_request.return_value = mock_response

        healer = AutoHealer(
            mock_api_client, validator=mock_validator, config=HealingConfig(max_attempts=3)
        )

        initial_context = "Initial context"
        await healer.heal_code("broken", "python", context=initial_context)

        # Check that context was accumulated
        calls = mock_api_client.send_request.call_args_list
        assert len(calls) == 3

        # Second call should have context about previous attempt
        prompt2 = calls[1][0][0][1].content
        assert "PREVIOUS ATTEMPT RETURNED SAME CODE" in prompt2

        # Third call should have both context messages
        prompt3 = calls[2][0][0][1].content
        assert prompt3.count("PREVIOUS ATTEMPT RETURNED SAME CODE") == 2
