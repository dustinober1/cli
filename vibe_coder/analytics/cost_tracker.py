"""
Cost tracker for API usage and budget management.

This module provides comprehensive cost tracking, budget management,
and usage analytics persistence.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

from vibe_coder.analytics.pricing import get_pricing
from vibe_coder.analytics.types import RequestMetrics, UsageStatistics

logger = logging.getLogger(__name__)


class CostTracker:
    """Track API usage and costs."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_save: bool = True,
    ):
        """
        Initialize the cost tracker.

        Args:
            storage_path: Path to store analytics data
            auto_save: Whether to auto-save after each request
        """
        if storage_path:
            self.storage_path = Path(storage_path).expanduser()
        else:
            self.storage_path = Path.home() / ".vibe" / "analytics.json"

        self.auto_save = auto_save
        self.metrics: List[RequestMetrics] = []
        self.budget_limit: Optional[float] = None
        self.budget_period: str = "monthly"
        self.alert_threshold: float = 0.8  # Alert at 80% of budget
        self.alert_callbacks: List[Callable[[float, float], None]] = []

        self._load_history()

    def set_budget(
        self,
        amount_usd: float,
        period: str = "monthly",
        alert_threshold: float = 0.8,
    ) -> None:
        """
        Set spending budget.

        Args:
            amount_usd: Budget amount in USD
            period: Budget period ("daily", "weekly", "monthly")
            alert_threshold: Percentage at which to trigger alerts
        """
        self.budget_limit = amount_usd
        self.budget_period = period
        self.alert_threshold = alert_threshold

        if self.auto_save:
            self._save_history()

    def record_request(self, metrics: RequestMetrics) -> None:
        """
        Record API request metrics.

        Args:
            metrics: Request metrics to record
        """
        self.metrics.append(metrics)

        if self.auto_save:
            self._save_history()

        # Check budget
        if self.budget_limit:
            current_spent = self.get_current_period_cost()
            threshold_amount = self.budget_limit * self.alert_threshold

            if current_spent >= threshold_amount:
                self._trigger_alerts(current_spent, self.budget_limit)

    def record_usage(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        completion_time: float = 0.0,
        operation: str = "chat",
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> RequestMetrics:
        """
        Record usage with automatic cost calculation.

        Args:
            model: Model name
            provider: Provider name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            completion_time: Time taken for request
            operation: Type of operation
            success: Whether request succeeded
            error_message: Error message if failed

        Returns:
            Created RequestMetrics
        """
        pricing = get_pricing(model)
        if pricing:
            input_cost = (input_tokens / 1000) * pricing.input_price_per_1k
            output_cost = (output_tokens / 1000) * pricing.output_price_per_1k
        else:
            input_cost = 0.0
            output_cost = 0.0

        metrics = RequestMetrics(
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            completion_time=completion_time,
            operation=operation,
            success=success,
            error_message=error_message,
        )

        self.record_request(metrics)
        return metrics

    def get_current_period_cost(self) -> float:
        """Get spending for current period."""
        period_start = self._get_period_start(datetime.now())

        return sum(
            m.total_cost
            for m in self.metrics
            if datetime.fromisoformat(m.timestamp) >= period_start
        )

    def get_remaining_budget(self) -> Optional[float]:
        """Get remaining budget for current period."""
        if not self.budget_limit:
            return None
        return max(0, self.budget_limit - self.get_current_period_cost())

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> UsageStatistics:
        """
        Get comprehensive usage statistics.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            UsageStatistics with aggregated data
        """
        # Filter metrics by date range
        filtered = self.metrics
        if start_date or end_date:
            filtered = [
                m for m in self.metrics if self._in_date_range(m.timestamp, start_date, end_date)
            ]

        if not filtered:
            return UsageStatistics()

        stats = UsageStatistics(
            total_requests=len(filtered),
            successful_requests=sum(1 for m in filtered if m.success),
            failed_requests=sum(1 for m in filtered if not m.success),
            total_tokens=sum(m.total_tokens for m in filtered),
            total_input_tokens=sum(m.input_tokens for m in filtered),
            total_output_tokens=sum(m.output_tokens for m in filtered),
            total_cost=sum(m.total_cost for m in filtered),
            total_time=sum(m.completion_time for m in filtered),
            by_model=self._stats_by_field(filtered, "model"),
            by_provider=self._stats_by_field(filtered, "provider"),
            by_operation=self._stats_by_field(filtered, "operation"),
            period_start=start_date.isoformat() if start_date else None,
            period_end=end_date.isoformat() if end_date else None,
        )

        return stats

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """
        Get daily statistics for the last N days.

        Args:
            days: Number of days to include

        Returns:
            List of daily statistics
        """
        result = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(days):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            day_metrics = [
                m
                for m in self.metrics
                if day_start <= datetime.fromisoformat(m.timestamp) < day_end
            ]

            result.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "requests": len(day_metrics),
                    "tokens": sum(m.total_tokens for m in day_metrics),
                    "cost": sum(m.total_cost for m in day_metrics),
                }
            )

        return list(reversed(result))

    def get_most_expensive_requests(self, limit: int = 10) -> List[RequestMetrics]:
        """
        Get the most expensive requests.

        Args:
            limit: Number of requests to return

        Returns:
            List of most expensive RequestMetrics
        """
        sorted_metrics = sorted(
            self.metrics,
            key=lambda m: m.total_cost,
            reverse=True,
        )
        return sorted_metrics[:limit]

    def project_monthly_cost(self) -> float:
        """
        Project monthly cost based on current usage.

        Returns:
            Projected monthly cost
        """
        # Get this month's metrics
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days_elapsed = (now - month_start).days + 1
        days_in_month = 30  # Approximation

        month_metrics = [
            m for m in self.metrics if datetime.fromisoformat(m.timestamp) >= month_start
        ]

        if days_elapsed == 0:
            return 0.0

        current_cost = sum(m.total_cost for m in month_metrics)
        daily_rate = current_cost / days_elapsed

        return daily_rate * days_in_month

    def add_alert_callback(self, callback: Callable[[float, float], None]) -> None:
        """
        Add a callback for budget alerts.

        Args:
            callback: Function called with (current_spent, limit) when threshold exceeded
        """
        self.alert_callbacks.append(callback)

    def export_csv(self, file_path: str) -> None:
        """
        Export metrics to CSV file.

        Args:
            file_path: Path to save CSV
        """
        import csv

        with open(file_path, "w", newline="") as f:
            if not self.metrics:
                return

            fieldnames = list(self.metrics[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for metric in self.metrics:
                writer.writerow(metric.to_dict())

    def export_json(self, file_path: str) -> None:
        """
        Export metrics to JSON file.

        Args:
            file_path: Path to save JSON
        """
        data = {
            "metrics": [m.to_dict() for m in self.metrics],
            "statistics": self.get_statistics().to_dict(),
            "exported_at": datetime.now().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def clear_history(self, before_date: Optional[datetime] = None) -> int:
        """
        Clear history, optionally before a specific date.

        Args:
            before_date: Optional date before which to clear

        Returns:
            Number of records cleared
        """
        if before_date:
            original_count = len(self.metrics)
            self.metrics = [
                m for m in self.metrics if datetime.fromisoformat(m.timestamp) >= before_date
            ]
            cleared = original_count - len(self.metrics)
        else:
            cleared = len(self.metrics)
            self.metrics = []

        if self.auto_save:
            self._save_history()

        return cleared

    def _load_history(self) -> None:
        """Load metrics from disk."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            self.metrics = [RequestMetrics.from_dict(m) for m in data.get("metrics", [])]
            self.budget_limit = data.get("budget_limit")
            self.budget_period = data.get("budget_period", "monthly")
            self.alert_threshold = data.get("alert_threshold", 0.8)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load analytics history: {e}")
            self.metrics = []

    def _save_history(self) -> None:
        """Persist metrics to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metrics": [m.to_dict() for m in self.metrics],
            "budget_limit": self.budget_limit,
            "budget_period": self.budget_period,
            "alert_threshold": self.alert_threshold,
            "saved_at": datetime.now().isoformat(),
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _get_period_start(self, now: datetime) -> datetime:
        """Get start of current budget period."""
        if self.budget_period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.budget_period == "weekly":
            days_since_monday = now.weekday()
            return (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:  # monthly
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _in_date_range(
        self,
        timestamp: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> bool:
        """Check if timestamp is within date range."""
        dt = datetime.fromisoformat(timestamp)
        if start_date and dt < start_date:
            return False
        if end_date and dt > end_date:
            return False
        return True

    def _stats_by_field(self, metrics: List[RequestMetrics], field: str) -> Dict[str, Dict]:
        """Calculate statistics grouped by a field."""
        groups: Dict[str, List[RequestMetrics]] = {}

        for m in metrics:
            key = getattr(m, field, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(m)

        result = {}
        for key, group in groups.items():
            result[key] = {
                "requests": len(group),
                "tokens": sum(m.total_tokens for m in group),
                "cost": sum(m.total_cost for m in group),
                "avg_tokens": sum(m.total_tokens for m in group) / len(group),
                "avg_cost": sum(m.total_cost for m in group) / len(group),
            }

        return result

    def _trigger_alerts(self, current_spent: float, limit: float) -> None:
        """Trigger budget alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(current_spent, limit)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        # Log warning
        percent = (current_spent / limit) * 100
        if current_spent >= limit:
            logger.warning(
                f"Budget EXCEEDED: ${current_spent:.2f} of ${limit:.2f} ({percent:.0f}%)"
            )
        else:
            logger.warning(f"Budget alert: ${current_spent:.2f} of ${limit:.2f} ({percent:.0f}%)")


class CostDisplay:
    """Format cost information for display."""

    @staticmethod
    def format_cost(amount_usd: float, precision: int = 4) -> str:
        """Format cost as string."""
        if amount_usd == 0:
            return "$0.00"
        if amount_usd < 0.0001:
            return f"${amount_usd:.6f}"
        if amount_usd < 0.01:
            return f"${amount_usd:.4f}"
        return f"${amount_usd:.{precision}f}"

    @staticmethod
    def format_tokens(count: int) -> str:
        """Format token count with K/M suffix."""
        if count < 1000:
            return str(count)
        if count < 1000000:
            return f"{count / 1000:.1f}K"
        return f"{count / 1000000:.2f}M"

    @staticmethod
    def get_cost_emoji(cost: float) -> str:
        """Return emoji based on cost level."""
        if cost == 0:
            return "🆓"
        if cost < 0.01:
            return "🟢"
        if cost < 0.10:
            return "🟡"
        if cost < 1.00:
            return "🟠"
        return "🔴"

    @staticmethod
    def get_tier_emoji(tier: str) -> str:
        """Return emoji for pricing tier."""
        emojis = {
            "free": "🆓",
            "cheap": "💚",
            "standard": "💛",
            "expensive": "❤️",
        }
        return emojis.get(tier.lower(), "💎")

    @staticmethod
    def render_budget_gauge(spent: float, limit: float, width: int = 20) -> str:
        """
        Render visual budget gauge.

        Args:
            spent: Amount spent
            limit: Budget limit
            width: Gauge width in characters

        Returns:
            Formatted gauge string
        """
        if limit <= 0:
            return "[No budget set]"

        percent = min(100, (spent / limit) * 100)
        filled = int((percent / 100) * width)
        empty = width - filled

        if percent < 60:
            color = "green"
            bar_char = "█"
        elif percent < 80:
            color = "yellow"
            bar_char = "█"
        elif percent < 100:
            color = "red"
            bar_char = "█"
        else:
            color = "red"
            bar_char = "▓"

        # For Rich console
        gauge = f"[{color}]{bar_char * filled}[/{color}]{'░' * empty}"
        return f"{gauge} {percent:.0f}% (${spent:.2f}/${limit:.2f})"

    @staticmethod
    def format_stats_summary(stats: UsageStatistics) -> str:
        """Format statistics summary."""
        lines = [
            f"Total Requests: {stats.total_requests}",
            f"Success Rate: {stats.success_rate:.1f}%",
            f"Total Tokens: {CostDisplay.format_tokens(stats.total_tokens)}",
            f"Total Cost: {CostDisplay.format_cost(stats.total_cost)}",
            f"Avg Cost/Request: {CostDisplay.format_cost(stats.avg_cost_per_request)}",
        ]
        return "\n".join(lines)


# Module-level instance for convenience
cost_tracker = CostTracker()
