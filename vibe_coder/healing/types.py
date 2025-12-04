"""
Type definitions for the auto-healing system.

This module defines data structures for validation results,
healing attempts, and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ValidationStrategy(Enum):
    """Types of validation to run."""

    SYNTAX = "syntax"
    TYPE_CHECK = "typecheck"
    LINT = "lint"
    TESTS = "tests"
    BUILD = "build"
    CUSTOM = "custom"


@dataclass
class ValidationResult:
    """Result of code validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    strategy: ValidationStrategy = ValidationStrategy.SYNTAX
    execution_time: float = 0.0
    details: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "strategy": self.strategy.value,
            "execution_time": self.execution_time,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ValidationResult":
        """Create from dictionary."""
        return cls(
            is_valid=data["is_valid"],
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            strategy=ValidationStrategy(data.get("strategy", "syntax")),
            execution_time=data.get("execution_time", 0.0),
            details=data.get("details"),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "✓ Valid" if self.is_valid else "✗ Invalid"
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        return f"{status} ({self.strategy.value}): {error_count} errors, {warning_count} warnings"


@dataclass
class HealingAttempt:
    """Record of a single healing attempt."""

    attempt_number: int
    original_code: str
    fixed_code: str
    validation_results: List[ValidationResult] = field(default_factory=list)
    ai_prompt: str = ""
    ai_response: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "attempt_number": self.attempt_number,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "ai_prompt": self.ai_prompt,
            "ai_response": self.ai_response,
            "timestamp": self.timestamp,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HealingAttempt":
        """Create from dictionary."""
        return cls(
            attempt_number=data["attempt_number"],
            original_code=data["original_code"],
            fixed_code=data["fixed_code"],
            validation_results=[
                ValidationResult.from_dict(r) for r in data.get("validation_results", [])
            ],
            ai_prompt=data.get("ai_prompt", ""),
            ai_response=data.get("ai_response", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            success=data.get("success", False),
        )


@dataclass
class HealingResult:
    """Final result of the healing process."""

    success: bool
    original_code: str
    final_code: str
    attempts: List[HealingAttempt] = field(default_factory=list)
    total_time: float = 0.0
    errors_fixed: List[str] = field(default_factory=list)
    errors_remaining: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "original_code": self.original_code,
            "final_code": self.final_code,
            "attempts": [a.to_dict() for a in self.attempts],
            "total_time": self.total_time,
            "errors_fixed": self.errors_fixed,
            "errors_remaining": self.errors_remaining,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HealingResult":
        """Create from dictionary."""
        return cls(
            success=data["success"],
            original_code=data["original_code"],
            final_code=data["final_code"],
            attempts=[HealingAttempt.from_dict(a) for a in data.get("attempts", [])],
            total_time=data.get("total_time", 0.0),
            errors_fixed=data.get("errors_fixed", []),
            errors_remaining=data.get("errors_remaining", []),
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "✓ Success" if self.success else "✗ Failed"
        return (
            f"{status} after {len(self.attempts)} attempts "
            f"({self.total_time:.2f}s): "
            f"{len(self.errors_fixed)} fixed, "
            f"{len(self.errors_remaining)} remaining"
        )


@dataclass
class HealingConfig:
    """Configuration for auto-healing."""

    max_attempts: int = 3
    strategies: List[ValidationStrategy] = field(
        default_factory=lambda: [ValidationStrategy.SYNTAX]
    )
    require_user_confirmation: bool = True
    save_before_healing: bool = True
    timeout_seconds: int = 60
    retry_on_partial_success: bool = True
    include_context: bool = True
    temperature: float = 0.3  # Lower temperature for more consistent fixes

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "max_attempts": self.max_attempts,
            "strategies": [s.value for s in self.strategies],
            "require_user_confirmation": self.require_user_confirmation,
            "save_before_healing": self.save_before_healing,
            "timeout_seconds": self.timeout_seconds,
            "retry_on_partial_success": self.retry_on_partial_success,
            "include_context": self.include_context,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HealingConfig":
        """Create from dictionary."""
        return cls(
            max_attempts=data.get("max_attempts", 3),
            strategies=[ValidationStrategy(s) for s in data.get("strategies", ["syntax"])],
            require_user_confirmation=data.get("require_user_confirmation", True),
            save_before_healing=data.get("save_before_healing", True),
            timeout_seconds=data.get("timeout_seconds", 60),
            retry_on_partial_success=data.get("retry_on_partial_success", True),
            include_context=data.get("include_context", True),
            temperature=data.get("temperature", 0.3),
        )

    @classmethod
    def strict(cls) -> "HealingConfig":
        """Create strict configuration with all validations."""
        return cls(
            max_attempts=5,
            strategies=[
                ValidationStrategy.SYNTAX,
                ValidationStrategy.TYPE_CHECK,
                ValidationStrategy.LINT,
            ],
            require_user_confirmation=True,
            save_before_healing=True,
            timeout_seconds=120,
        )

    @classmethod
    def quick(cls) -> "HealingConfig":
        """Create quick configuration with minimal validation."""
        return cls(
            max_attempts=2,
            strategies=[ValidationStrategy.SYNTAX],
            require_user_confirmation=False,
            save_before_healing=True,
            timeout_seconds=30,
        )
