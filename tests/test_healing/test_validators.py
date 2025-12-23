"""Tests for the CodeValidator class."""

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_coder.healing.types import ValidationResult, ValidationStrategy
from vibe_coder.healing.validators import CodeValidator


class TestCodeValidatorInitialization:
    """Test CodeValidator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        validator = CodeValidator()

        assert validator.project_root == Path.cwd()
        assert validator.python_executable == sys.executable

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        custom_root = "/tmp/project"
        custom_python = "/usr/bin/python3"

        validator = CodeValidator(project_root=custom_root, python_executable=custom_python)

        assert validator.project_root == Path(custom_root)
        assert validator.python_executable == custom_python


class TestValidateMethod:
    """Test the main validate method."""

    @pytest.mark.asyncio
    async def test_validate_single_strategy(self):
        """Test validation with a single strategy."""
        validator = CodeValidator()

        with patch.object(validator, "validate_syntax") as mock_syntax:
            mock_syntax.return_value = ValidationResult(is_valid=True)

            result = await validator.validate(
                code="def test(): pass", language="python", strategies=[ValidationStrategy.SYNTAX]
            )

            assert len(result) == 1
            mock_syntax.assert_called_once_with("def test(): pass", "python")

    @pytest.mark.asyncio
    async def test_validate_multiple_strategies(self):
        """Test validation with multiple strategies."""
        validator = CodeValidator()

        with (
            patch.object(validator, "validate_syntax") as mock_syntax,
            patch.object(validator, "validate_types") as mock_types,
            patch.object(validator, "validate_linting") as mock_lint,
        ):

            mock_syntax.return_value = ValidationResult(is_valid=True)
            mock_types.return_value = ValidationResult(is_valid=False, errors=["Type error"])
            mock_lint.return_value = ValidationResult(is_valid=True)

            result = await validator.validate(
                code="def test(): pass",
                language="python",
                strategies=[
                    ValidationStrategy.SYNTAX,
                    ValidationStrategy.TYPE_CHECK,
                    ValidationStrategy.LINT,
                ],
                file_path="test.py",
            )

            assert len(result) == 3
            mock_syntax.assert_called_once_with("def test(): pass", "python")
            mock_types.assert_called_once_with("def test(): pass", "python", "test.py")
            mock_lint.assert_called_once_with("def test(): pass", "python", "test.py")

    @pytest.mark.asyncio
    async def test_validate_with_tests_strategy(self):
        """Test validation with tests strategy."""
        validator = CodeValidator()

        with patch.object(validator, "validate_tests") as mock_tests:
            mock_tests.return_value = ValidationResult(is_valid=True)

            result = await validator.validate(
                code="def test(): pass",
                language="python",
                strategies=[ValidationStrategy.TESTS],
                file_path="src/test.py",
            )

            assert len(result) == 1
            mock_tests.assert_called_once_with("src/test.py")

    @pytest.mark.asyncio
    async def test_validate_with_build_strategy(self):
        """Test validation with build strategy."""
        validator = CodeValidator()

        with patch.object(validator, "validate_build") as mock_build:
            mock_build.return_value = ValidationResult(is_valid=True)

            result = await validator.validate(
                code="def test(): pass", language="python", strategies=[ValidationStrategy.BUILD]
            )

            assert len(result) == 1
            mock_build.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_with_custom_strategy(self):
        """Test validation with custom strategy."""
        validator = CodeValidator()

        result = await validator.validate(
            code="def test(): pass", language="python", strategies=[ValidationStrategy.CUSTOM]
        )

        assert len(result) == 1
        assert result[0].is_valid is True
        assert result[0].warnings == ["Custom validation not implemented"]


class TestValidateSyntax:
    """Test syntax validation."""

    @pytest.mark.asyncio
    async def test_validate_syntax_valid_python(self):
        """Test syntax validation with valid Python code."""
        validator = CodeValidator()

        result = await validator.validate_syntax(
            code="def hello_world():\n    return 'Hello, World!'", language="python"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.strategy == ValidationStrategy.SYNTAX
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_validate_syntax_invalid_python(self):
        """Test syntax validation with invalid Python code."""
        validator = CodeValidator()

        result = await validator.validate_syntax(
            code="def hello_world(\n    return 'Hello, World!'",  # Missing closing parenthesis
            language="python",
        )

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("unexpected EOF" in error for error in result.errors)
        assert result.strategy == ValidationStrategy.SYNTAX

    @pytest.mark.asyncio
    async def test_validate_syntax_with_text_in_error(self):
        """Test syntax validation when error includes text."""
        validator = CodeValidator()

        # Create a syntax error that includes the problematic line
        code = "print('unclosed string"
        result = await validator.validate_syntax(code, "python")

        assert result.is_valid is False
        assert len(result.errors) > 0
        # Error should mention the line number
        assert any("Line " in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_syntax_non_python(self):
        """Test syntax validation for non-Python languages."""
        validator = CodeValidator()

        result = await validator.validate_syntax(
            code="function test() { return true; }", language="javascript"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "not supported for javascript" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_syntax_empty_code(self):
        """Test syntax validation with empty code."""
        validator = CodeValidator()

        result = await validator.validate_syntax("", "python")

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_syntax_only_whitespace(self):
        """Test syntax validation with only whitespace."""
        validator = CodeValidator()

        result = await validator.validate_syntax("   \n  \t  \n", "python")

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidateTypes:
    """Test type validation."""

    @pytest.mark.asyncio
    async def test_validate_types_valid_code(self):
        """Test type validation with valid code."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

            result = await validator.validate_types(
                code="def greet(name: str) -> str:\n    return f'Hello, {name}!'",
                language="python",
                file_path="test.py",
            )

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.strategy == ValidationStrategy.TYPE_CHECK

    @pytest.mark.asyncio
    async def test_validate_types_with_errors(self):
        """Test type validation with type errors."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": (
                    'test.py:2: error: Incompatible return value type '
                    '(got "int", expected "str")\n'
                ),
                "stderr": "",
            }

            result = await validator.validate_types(
                code="def greet(name: str) -> str:\n    return 42",  # Type mismatch
                language="python",
                file_path="test.py",
            )

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any("Incompatible return value" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_types_with_warnings(self):
        """Test type validation with warnings."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 0,  # mypy returns 0 even with warnings
                "stdout": "test.py:1: warning: Call to untyped function\n",
                "stderr": "",
            }

            result = await validator.validate_types(
                code="def test():\n    return untyped_function()",
                language="python",
                file_path="test.py",
            )

            assert result.is_valid is True
            assert len(result.warnings) > 0
            assert any("warning:" in warning for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_types_mypy_not_installed(self):
        """Test type validation when mypy is not installed."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = await validator.validate_types(code="def test(): pass", language="python")

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert len(result.warnings) == 1
            assert "mypy not installed" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_types_non_python(self):
        """Test type validation for non-Python languages."""
        validator = CodeValidator()

        result = await validator.validate_types(
            code="function test() { return true; }", language="javascript"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "not supported for javascript" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_types_temp_file_cleanup(self):
        """Test that temporary files are cleaned up."""
        validator = CodeValidator()

        with (
            patch.object(validator, "_run_subprocess") as mock_run,
            patch("pathlib.Path.unlink") as mock_unlink,
        ):

            mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

            await validator.validate_types("def test(): pass", "python")

            # Ensure unlink was called to clean up temp file
            mock_unlink.assert_called_once_with(missing_ok=True)


class TestValidateLinting:
    """Test linting validation."""

    @pytest.mark.asyncio
    async def test_validate_linting_valid_code(self):
        """Test linting validation with valid code."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

            result = await validator.validate_linting(
                code="def greet(name: str) -> str:\n    return f'Hello, {name}!'",
                language="python",
                file_path="test.py",
            )

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.strategy == ValidationStrategy.LINT

    @pytest.mark.asyncio
    async def test_validate_linting_with_errors(self):
        """Test linting validation with lint errors."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "test.py:1:1: E302 expected 2 blank lines\n",
                "stderr": "",
            }

            result = await validator.validate_linting(
                code="def test(): pass",  # Missing blank lines
                language="python",
                file_path="test.py",
            )

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any("E302" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_linting_with_warnings(self):
        """Test linting validation with warnings."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "test.py:1:80: W503 line break before binary operator\n",
                "stderr": "",
            }

            result = await validator.validate_linting(
                code="x = 1 + \\\n    2", language="python", file_path="test.py"
            )

            assert result.is_valid is True  # Warnings don't make it invalid
            assert len(result.warnings) > 0
            assert any("W503" in warning for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_linting_flake8_not_installed(self):
        """Test linting validation when flake8 is not installed."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = await validator.validate_linting(code="def test(): pass", language="python")

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert len(result.warnings) == 1
            assert "flake8 not installed" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_linting_non_python(self):
        """Test linting validation for non-Python languages."""
        validator = CodeValidator()

        result = await validator.validate_linting(
            code="function test() { return true; }", language="javascript"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "not supported for javascript" in result.warnings[0]


class TestValidateTests:
    """Test test validation."""

    @pytest.mark.asyncio
    async def test_validate_tests_no_file_path(self):
        """Test test validation without file path."""
        validator = CodeValidator()

        result = await validator.validate_tests()

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "No file path provided" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_tests_no_test_file_found(self):
        """Test test validation when no test file is found."""
        validator = CodeValidator()

        with patch.object(validator, "_find_test_file") as mock_find:
            mock_find.return_value = None

            result = await validator.validate_tests("src/nonexistent.py")

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert len(result.warnings) == 1
            assert "No test file found" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_tests_success(self):
        """Test test validation with passing tests."""
        validator = CodeValidator()

        with (
            patch.object(validator, "_find_test_file") as mock_find,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            mock_find.return_value = Path("tests/test_src.py")
            mock_run.return_value = {
                "returncode": 0,
                "stdout": "tests/test_src.py::test_func PASSED\n",
                "stderr": "",
            }

            result = await validator.validate_tests("src/test.py")

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert "test_output" in result.details
            assert "PASSED" in result.details["test_output"]

    @pytest.mark.asyncio
    async def test_validate_tests_failure(self):
        """Test test validation with failing tests."""
        validator = CodeValidator()

        with (
            patch.object(validator, "_find_test_file") as mock_find,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            mock_find.return_value = Path("tests/test_src.py")
            mock_run.return_value = {
                "returncode": 1,
                "stdout": (
                    "tests/test_src.py::test_func FAILED\n"
                    "AssertionError: Expected True but got False\n"
                ),
                "stderr": "",
            }

            result = await validator.validate_tests("src/test.py")

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any("FAILED" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_tests_pytest_not_installed(self):
        """Test test validation when pytest is not installed."""
        validator = CodeValidator()

        with (
            patch.object(validator, "_find_test_file") as mock_find,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            mock_find.return_value = Path("tests/test_src.py")
            mock_run.side_effect = FileNotFoundError()

            result = await validator.validate_tests("src/test.py")

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert len(result.warnings) == 1
            assert "pytest not installed" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_tests_with_timeout(self):
        """Test test validation with timeout."""
        validator = CodeValidator()

        with (
            patch.object(validator, "_find_test_file") as mock_find,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            mock_find.return_value = Path("tests/test_src.py")
            mock_run.return_value = {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 60s",
            }

            result = await validator.validate_tests("src/test.py")

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert "timed out" in result.errors[0]


class TestValidateBuild:
    """Test build validation."""

    @pytest.mark.asyncio
    async def test_validate_build_with_poetry(self):
        """Test build validation with poetry configuration."""
        validator = CodeValidator()

        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            mock_exists.return_value = True
            mock_run.return_value = {"returncode": 0, "stdout": "All set!\n", "stderr": ""}

            result = await validator.validate_build()

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.strategy == ValidationStrategy.BUILD

    @pytest.mark.asyncio
    async def test_validate_build_poetry_failure(self):
        """Test build validation with poetry check failure."""
        validator = CodeValidator()

        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            # pyproject.toml exists
            mock_exists.side_effect = lambda: True
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "Error: pyproject.toml is invalid\n",
                "stderr": "",
            }

            result = await validator.validate_build()

            assert result.is_valid is False
            assert len(result.errors) > 0
            assert "Poetry check failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_build_with_makefile(self):
        """Test build validation with Makefile."""
        validator = CodeValidator()

        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(validator, "_run_subprocess") as mock_run,
        ):

            # pyproject.toml doesn't exist, but Makefile does
            def exists_side_effect():
                return str(mock_exists.call_args[0][0]).endswith("Makefile")

            mock_exists.side_effect = exists_side_effect
            mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

            result = await validator.validate_build()

            assert result.is_valid is True
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_build_no_config(self):
        """Test build validation with no build configuration."""
        validator = CodeValidator()

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = await validator.validate_build()

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert len(result.warnings) == 1
            assert "No build configuration found" in result.warnings[0]


class TestValidateCustom:
    """Test custom validation."""

    @pytest.mark.asyncio
    async def test_validate_custom_success(self):
        """Test custom validation with success."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {"returncode": 0, "stdout": "Validation passed\n", "stderr": ""}

            result = await validator.validate_custom(
                script="echo 'Checking code...'", code="def test(): pass"
            )

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.strategy == ValidationStrategy.CUSTOM

    @pytest.mark.asyncio
    async def test_validate_custom_failure(self):
        """Test custom validation with failure."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "Validation failed:\n- Missing docstring\n- Type hints required\n",
                "stderr": "",
            }

            result = await validator.validate_custom(
                script="check_code.sh", code="def test(): pass"
            )

            assert result.is_valid is False
            assert len(result.errors) == 2
            assert any("Missing docstring" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_custom_with_stderr(self):
        """Test custom validation with stderr output."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "",
                "stderr": "Error: Cannot validate code\nInvalid syntax at line 5\n",
            }

            result = await validator.validate_custom(script="validate.sh", code="invalid code")

            assert result.is_valid is False
            assert len(result.errors) == 2
            assert any("Cannot validate code" in error for error in result.errors)


class TestRunSubprocess:
    """Test subprocess execution."""

    @pytest.mark.asyncio
    async def test_run_subprocess_success(self):
        """Test successful subprocess execution."""
        validator = CodeValidator()

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_create.return_value.__aenter__ = AsyncMock(return_value=mock_process)
            mock_create.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await validator._run_subprocess(["echo", "hello"])

            assert result["returncode"] == 0
            assert result["stdout"] == "output"
            assert result["stderr"] == ""

    @pytest.mark.asyncio
    async def test_run_subprocess_with_input(self):
        """Test subprocess execution with input data."""
        validator = CodeValidator()

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"processed", b"")
            mock_create.return_value.__aenter__ = AsyncMock(return_value=mock_process)
            mock_create.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await validator._run_subprocess(["cat"], input_data="test input")

            assert result["returncode"] == 0
            assert result["stdout"] == "processed"

    @pytest.mark.asyncio
    async def test_run_subprocess_timeout(self):
        """Test subprocess execution with timeout."""
        validator = CodeValidator()

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = MagicMock()
            mock_process.kill = MagicMock()

            # Simulate timeout
            async def mock_commulate(*args, **kwargs):
                raise asyncio.TimeoutError()

            mock_process.communicate = mock_commulate
            mock_create.return_value.__aenter__ = AsyncMock(return_value=mock_process)
            mock_create.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await validator._run_subprocess(["sleep", "10"], timeout=1)

            assert result["returncode"] == -1
            assert "timed out" in result["stderr"]
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_subprocess_exception(self):
        """Test subprocess execution with exception."""
        validator = CodeValidator()

        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_create.side_effect = Exception("Process creation failed")

            result = await validator._run_subprocess(["invalid_command"])

            assert result["returncode"] == -1
            assert "Process creation failed" in result["stderr"]


class TestFindTestFile:
    """Test test file finding."""

    def test_find_test_file_in_project_root(self):
        """Test finding test file in project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            validator = CodeValidator(str(project_root))

            # Create test file
            test_file = project_root / "test_example.py"
            test_file.touch()

            found = validator._find_test_file("src/example.py")
            assert found == test_file

    def test_find_test_file_in_tests_dir(self):
        """Test finding test file in tests directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            validator = CodeValidator(str(project_root))

            # Create test file in tests directory
            tests_dir = project_root / "tests"
            tests_dir.mkdir()
            test_file = tests_dir / "test_example.py"
            test_file.touch()

            found = validator._find_test_file("src/example.py")
            assert found == test_file

    def test_find_test_file_parallel_structure(self):
        """Test finding test file in parallel structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            validator = CodeValidator(str(project_root))

            # Create vibe_coder structure
            vibe_dir = project_root / "vibe_coder" / "commands"
            vibe_dir.mkdir(parents=True)

            # Create parallel test structure
            tests_dir = project_root / "tests" / "commands"
            tests_dir.mkdir(parents=True)
            test_file = tests_dir / "test_file.py"
            test_file.touch()

            source_path = str(vibe_dir / "file.py")
            found = validator._find_test_file(source_path)
            assert found == test_file

    def test_find_test_file_not_found(self):
        """Test when test file is not found."""
        validator = CodeValidator()

        found = validator._find_test_file("src/nonexistent.py")
        assert found is None

    def test_find_test_file_multiple_patterns(self):
        """Test finding test file with multiple naming patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            validator = CodeValidator(str(project_root))

            # Create test file with different pattern
            test_file = project_root / "example_test.py"
            test_file.touch()

            found = validator._find_test_file("src/example.py")
            assert found == test_file


class TestGetValidationSummary:
    """Test validation summary generation."""

    def test_get_validation_summary_all_valid(self):
        """Test summary when all validations are valid."""
        validator = CodeValidator()

        results = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX),
            ValidationResult(is_valid=True, strategy=ValidationStrategy.TYPE_CHECK),
            ValidationResult(is_valid=True, strategy=ValidationStrategy.LINT),
        ]

        summary = validator.get_validation_summary(results)

        assert summary["all_valid"] is True
        assert summary["total_errors"] == 0
        assert summary["total_warnings"] == 0
        assert summary["strategies_run"] == ["syntax", "typecheck", "lint"]
        assert len(summary["failed_strategies"]) == 0

    def test_get_validation_summary_with_errors(self):
        """Test summary when there are errors."""
        validator = CodeValidator()

        results = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX),
            ValidationResult(
                is_valid=False,
                errors=["Type error 1", "Type error 2"],
                strategy=ValidationStrategy.TYPE_CHECK,
            ),
            ValidationResult(
                is_valid=False,
                errors=["Lint error"],
                warnings=["Lint warning"],
                strategy=ValidationStrategy.LINT,
            ),
        ]

        summary = validator.get_validation_summary(results)

        assert summary["all_valid"] is False
        assert summary["total_errors"] == 3
        assert summary["total_warnings"] == 1
        assert summary["failed_strategies"] == ["typecheck", "lint"]

    def test_get_validation_summary_with_timing(self):
        """Test summary includes execution times."""
        validator = CodeValidator()

        results = [
            ValidationResult(is_valid=True, strategy=ValidationStrategy.SYNTAX, execution_time=0.1),
            ValidationResult(
                is_valid=True, strategy=ValidationStrategy.TYPE_CHECK, execution_time=0.5
            ),
            ValidationResult(is_valid=True, strategy=ValidationStrategy.LINT, execution_time=0.2),
        ]

        summary = validator.get_validation_summary(results)

        assert summary["total_time"] == 0.8
        assert summary["all_valid"] is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_validate_with_exception_handling(self):
        """Test validation handles exceptions gracefully."""
        validator = CodeValidator()

        with patch.object(validator, "validate_syntax") as mock_syntax:
            mock_syntax.side_effect = Exception("Unexpected error")

            await validator.validate(
                code="def test(): pass", language="python", strategies=[ValidationStrategy.SYNTAX]
            )

            # Should not crash, but the specific exception handling
            # would depend on implementation

    @pytest.mark.asyncio
    async def test_validate_types_with_invalid_mypy_output(self):
        """Test type validation with unparseable mypy output."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "Invalid output format\nNo proper error format\n",
                "stderr": "",
            }

            result = await validator.validate_types(code="def test(): pass", language="python")

            assert result.is_valid is False
            # Should handle the output gracefully

    @pytest.mark.asyncio
    async def test_validate_linting_with_invalid_flake8_output(self):
        """Test linting validation with unparseable flake8 output."""
        validator = CodeValidator()

        with patch.object(validator, "_run_subprocess") as mock_run:
            mock_run.return_value = {
                "returncode": 1,
                "stdout": "Weird output format\nNot standard flake8\n",
                "stderr": "",
            }

            result = await validator.validate_linting(code="def test(): pass", language="python")

            # Should classify as warnings since it doesn't match error pattern
            assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_test_with_nonexistent_project_root(self):
        """Test test validation with nonexistent project root."""
        validator = CodeValidator(project_root="/nonexistent")

        with patch.object(validator, "_find_test_file") as mock_find:
            mock_find.return_value = Path("/nonexistent/test.py")

            with patch.object(validator, "_run_subprocess") as mock_run:
                mock_run.return_value = {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "No such file or directory",
                }

                result = await validator.validate_tests("test.py")
                assert result.is_valid is False
