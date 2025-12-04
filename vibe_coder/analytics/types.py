"""
Type definitions for the analytics system.

This module defines data structures for token pricing,
request metrics, and usage statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ModelTier(Enum):
    """Pricing tier for models."""

    FREE = "free"
    CHEAP = "cheap"
    STANDARD = "standard"
    EXPENSIVE = "expensive"


@dataclass
class TokenPricing:
    """Token pricing for a model."""

    model_name: str
    input_price_per_1k: float
    output_price_per_1k: float
    tier: ModelTier
    context_window: int = 4096
    max_output: int = 4096

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token counts."""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "input_price_per_1k": self.input_price_per_1k,
            "output_price_per_1k": self.output_price_per_1k,
            "tier": self.tier.value,
            "context_window": self.context_window,
            "max_output": self.max_output,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TokenPricing":
        """Create from dictionary."""
        return cls(
            model_name=data["model_name"],
            input_price_per_1k=data["input_price_per_1k"],
            output_price_per_1k=data["output_price_per_1k"],
            tier=ModelTier(data.get("tier", "standard")),
            context_window=data.get("context_window", 4096),
            max_output=data.get("max_output", 4096),
        )


@dataclass
class RequestMetrics:
    """Metrics for a single API request."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    operation: str = "chat"
    completion_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        """Calculate total tokens if not set."""
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens
        if self.total_cost == 0:
            self.total_cost = self.input_cost + self.output_cost

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "operation": self.operation,
            "completion_time": self.completion_time,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RequestMetrics":
        """Create from dictionary."""
        return cls(
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            input_cost=data.get("input_cost", 0.0),
            output_cost=data.get("output_cost", 0.0),
            total_cost=data.get("total_cost", 0.0),
            operation=data.get("operation", "chat"),
            completion_time=data.get("completion_time", 0.0),
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )


@dataclass
class UsageStatistics:
    """Aggregated usage statistics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    total_time: float = 0.0
    by_model: Dict[str, Dict] = field(default_factory=dict)
    by_provider: Dict[str, Dict] = field(default_factory=dict)
    by_operation: Dict[str, Dict] = field(default_factory=dict)
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_tokens_per_request(self) -> float:
        """Calculate average tokens per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_tokens / self.total_requests

    @property
    def avg_cost_per_request(self) -> float:
        """Calculate average cost per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_cost / self.total_requests

    @property
    def avg_time_per_request(self) -> float:
        """Calculate average time per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "total_time": self.total_time,
            "by_model": self.by_model,
            "by_provider": self.by_provider,
            "by_operation": self.by_operation,
            "period_start": self.period_start,
            "period_end": self.period_end,
            # Computed properties
            "success_rate": self.success_rate,
            "avg_tokens_per_request": self.avg_tokens_per_request,
            "avg_cost_per_request": self.avg_cost_per_request,
            "avg_time_per_request": self.avg_time_per_request,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UsageStatistics":
        """Create from dictionary."""
        return cls(
            total_requests=data.get("total_requests", 0),
            successful_requests=data.get("successful_requests", 0),
            failed_requests=data.get("failed_requests", 0),
            total_tokens=data.get("total_tokens", 0),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
            total_cost=data.get("total_cost", 0.0),
            total_time=data.get("total_time", 0.0),
            by_model=data.get("by_model", {}),
            by_provider=data.get("by_provider", {}),
            by_operation=data.get("by_operation", {}),
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
        )
