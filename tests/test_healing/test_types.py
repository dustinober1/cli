"""Tests for healing types."""

from vibe_coder.healing.types import (
    HealingAttempt,
    HealingConfig,
    HealingResult,
    ValidationResult,
    ValidationStrategy,
)


class TestValidationStrategy:
    """Tests for ValidationStrategy enum."""

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert ValidationStrategy.SYNTAX.value == "syntax"
        assert ValidationStrategy.TYPE_CHECK.value == "typecheck"
        assert ValidationStrategy.LINT.value == "lint"
        assert ValidationStrategy.TESTS.value == "tests"
        assert ValidationStrategy.BUILD.value == "build"
        assert ValidationStrategy.CUSTOM.value == "custom"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["minor warning"],
            strategy=ValidationStrategy.SYNTAX,
            execution_time=0.5,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.strategy == ValidationStrategy.SYNTAX

    def test_create_invalid_result(self):
        """Test creating an invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Syntax error at line 5"],
            warnings=[],
            strategy=ValidationStrategy.SYNTAX,
            execution_time=0.1,
        )

        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validation_result_to_dict(self):
        """Test serialization."""
        result = ValidationResult(
            is_valid=True,
            strategy=ValidationStrategy.LINT,
        )

        data = result.to_dict()
        assert data["is_valid"] is True
        assert data["strategy"] == "lint"

    def test_validation_result_from_dict(self):
        """Test deserialization."""
        data = {
            "is_valid": False,
            "errors": ["Error 1"],
            "warnings": [],
            "strategy": "typecheck",
            "execution_time": 1.5,
        }

        result = ValidationResult.from_dict(data)
        assert result.is_valid is False
        assert result.strategy == ValidationStrategy.TYPE_CHECK

    def test_validation_result_str(self):
        """Test string representation."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["warning"],
            strategy=ValidationStrategy.SYNTAX,
        )

        string = str(result)
        assert "Valid" in string
        assert "0 errors" in string


class TestHealingAttempt:
    """Tests for HealingAttempt dataclass."""

    def test_create_healing_attempt(self):
        """Test creating a healing attempt."""
        result = ValidationResult(is_valid=False, errors=["error"])

        attempt = HealingAttempt(
            attempt_number=1,
            original_code="broken code",
            fixed_code="fixed code",
            validation_results=[result],
            ai_prompt="Fix this",
            ai_response="Here's the fix",
            success=False,
        )

        assert attempt.attempt_number == 1
        assert attempt.original_code == "broken code"
        assert attempt.fixed_code == "fixed code"
        assert len(attempt.validation_results) == 1
        assert attempt.success is False

    def test_healing_attempt_to_dict(self):
        """Test serialization."""
        attempt = HealingAttempt(
            attempt_number=2,
            original_code="code1",
            fixed_code="code2",
        )

        data = attempt.to_dict()
        assert data["attempt_number"] == 2
        assert "timestamp" in data

    def test_healing_attempt_from_dict(self):
        """Test deserialization."""
        data = {
            "attempt_number": 3,
            "original_code": "orig",
            "fixed_code": "fixed",
            "validation_results": [],
            "ai_prompt": "",
            "ai_response": "",
            "timestamp": "2024-01-01T00:00:00",
            "success": True,
        }

        attempt = HealingAttempt.from_dict(data)
        assert attempt.attempt_number == 3
        assert attempt.success is True


class TestHealingResult:
    """Tests for HealingResult dataclass."""

    def test_create_successful_result(self):
        """Test creating a successful result."""
        result = HealingResult(
            success=True,
            original_code="broken",
            final_code="fixed",
            attempts=[],
            total_time=5.0,
            errors_fixed=["error1", "error2"],
            errors_remaining=[],
        )

        assert result.success is True
        assert len(result.errors_fixed) == 2
        assert len(result.errors_remaining) == 0

    def test_create_failed_result(self):
        """Test creating a failed result."""
        result = HealingResult(
            success=False,
            original_code="broken",
            final_code="still broken",
            attempts=[],
            total_time=10.0,
            errors_fixed=[],
            errors_remaining=["unfixable error"],
        )

        assert result.success is False
        assert len(result.errors_remaining) == 1

    def test_healing_result_to_dict(self):
        """Test serialization."""
        result = HealingResult(
            success=True,
            original_code="a",
            final_code="b",
        )

        data = result.to_dict()
        assert data["success"] is True
        assert data["original_code"] == "a"

    def test_healing_result_str(self):
        """Test string representation."""
        result = HealingResult(
            success=True,
            original_code="a",
            final_code="b",
            attempts=[],
            total_time=2.5,
            errors_fixed=["e1", "e2"],
            errors_remaining=[],
        )

        string = str(result)
        assert "Success" in string
        assert "2 fixed" in string


class TestHealingConfig:
    """Tests for HealingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = HealingConfig()

        assert config.max_attempts == 3
        assert ValidationStrategy.SYNTAX in config.strategies
        assert config.require_user_confirmation is True
        assert config.save_before_healing is True
        assert config.timeout_seconds == 60

    def test_custom_config(self):
        """Test custom configuration."""
        config = HealingConfig(
            max_attempts=5,
            strategies=[
                ValidationStrategy.SYNTAX,
                ValidationStrategy.TYPE_CHECK,
                ValidationStrategy.LINT,
            ],
            require_user_confirmation=False,
            temperature=0.5,
        )

        assert config.max_attempts == 5
        assert len(config.strategies) == 3
        assert config.require_user_confirmation is False

    def test_strict_config(self):
        """Test strict configuration preset."""
        config = HealingConfig.strict()

        assert config.max_attempts == 5
        assert len(config.strategies) >= 3
        assert ValidationStrategy.LINT in config.strategies

    def test_quick_config(self):
        """Test quick configuration preset."""
        config = HealingConfig.quick()

        assert config.max_attempts == 2
        assert len(config.strategies) == 1
        assert config.require_user_confirmation is False

    def test_config_to_dict(self):
        """Test serialization."""
        config = HealingConfig()
        data = config.to_dict()

        assert data["max_attempts"] == 3
        assert "syntax" in data["strategies"]

    def test_config_from_dict(self):
        """Test deserialization."""
        data = {
            "max_attempts": 4,
            "strategies": ["syntax", "lint"],
            "require_user_confirmation": False,
            "temperature": 0.2,
        }

        config = HealingConfig.from_dict(data)
        assert config.max_attempts == 4
        assert len(config.strategies) == 2
