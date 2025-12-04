"""
Auto-healing engine for automatic code fixing.

This module provides AI-powered automatic code fixing capabilities
with multi-strategy validation and rollback support.
"""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from vibe_coder.healing.types import HealingAttempt, HealingConfig, HealingResult, ValidationResult
from vibe_coder.healing.validators import CodeValidator


class AutoHealer:
    """Automatically fix code issues using AI."""

    def __init__(
        self,
        api_client,
        validator: Optional[CodeValidator] = None,
        config: Optional[HealingConfig] = None,
        backup_dir: Optional[str] = None,
    ):
        """
        Initialize the auto-healer.

        Args:
            api_client: API client for AI requests
            validator: Code validator instance
            config: Healing configuration
            backup_dir: Directory for backup files
        """
        self.api_client = api_client
        self.validator = validator or CodeValidator()
        self.config = config or HealingConfig()
        self.backup_dir = Path(backup_dir) if backup_dir else Path.home() / ".vibe" / "backups"
        self.healing_history: List[HealingResult] = []

    async def heal_code(
        self,
        code: str,
        language: str = "python",
        context: str = "",
        file_path: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> HealingResult:
        """
        Attempt to fix broken code.

        Args:
            code: The code to fix
            language: Programming language
            context: Additional context for the AI
            file_path: Original file path (for backups and context)
            custom_prompt: Optional custom prompt for AI

        Returns:
            HealingResult with final code and attempt history
        """
        start_time = time.time()
        attempts: List[HealingAttempt] = []
        current_code = code
        original_errors: List[str] = []
        fixed_errors: List[str] = []

        # Save backup if configured
        if self.config.save_before_healing and file_path:
            self._create_backup(file_path, code)

        # Initial validation
        initial_results = await self.validator.validate(
            code, language, self.config.strategies, file_path
        )
        original_errors = self._collect_errors(initial_results)

        # Check if already valid
        if all(r.is_valid for r in initial_results):
            return HealingResult(
                success=True,
                original_code=code,
                final_code=code,
                attempts=[],
                total_time=time.time() - start_time,
                errors_fixed=[],
                errors_remaining=[],
            )

        # Healing loop
        for attempt_num in range(1, self.config.max_attempts + 1):
            # Validate current code
            validation_results = await self.validator.validate(
                current_code, language, self.config.strategies, file_path
            )

            # Check if all validations passed
            if all(r.is_valid for r in validation_results):
                # Calculate fixed errors
                remaining = self._collect_errors(validation_results)
                fixed_errors = [e for e in original_errors if e not in remaining]

                result = HealingResult(
                    success=True,
                    original_code=code,
                    final_code=current_code,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                    errors_fixed=fixed_errors,
                    errors_remaining=remaining,
                )
                self.healing_history.append(result)
                return result

            # Collect all errors
            all_errors = self._collect_errors(validation_results)
            all_warnings = self._collect_warnings(validation_results)

            # Ask AI to fix
            fixed_code, ai_prompt, ai_response = await self._ask_ai_to_fix(
                current_code,
                language,
                all_errors,
                all_warnings,
                context,
                attempt_num,
                custom_prompt,
            )

            # Record attempt
            attempt = HealingAttempt(
                attempt_number=attempt_num,
                original_code=current_code,
                fixed_code=fixed_code,
                validation_results=validation_results,
                ai_prompt=ai_prompt,
                ai_response=ai_response,
                timestamp=datetime.now().isoformat(),
                success=False,
            )
            attempts.append(attempt)

            # Check if fix made any changes
            if fixed_code == current_code:
                # AI couldn't find a fix, try with more context
                if attempt_num < self.config.max_attempts:
                    context += "\n\nPREVIOUS ATTEMPT RETURNED SAME CODE. Try a different approach."

            current_code = fixed_code

        # Max attempts exceeded - final validation
        final_results = await self.validator.validate(
            current_code, language, self.config.strategies, file_path
        )

        remaining_errors = self._collect_errors(final_results)
        fixed_errors = [e for e in original_errors if e not in remaining_errors]

        # Mark last attempt as success if we fixed some errors
        success = len(remaining_errors) < len(original_errors) or all(
            r.is_valid for r in final_results
        )

        if attempts:
            attempts[-1].success = success

        result = HealingResult(
            success=success,
            original_code=code,
            final_code=current_code,
            attempts=attempts,
            total_time=time.time() - start_time,
            errors_fixed=fixed_errors,
            errors_remaining=remaining_errors,
        )
        self.healing_history.append(result)
        return result

    async def heal_file(
        self,
        file_path: str,
        context: str = "",
        save_result: bool = False,
    ) -> HealingResult:
        """
        Heal a file directly.

        Args:
            file_path: Path to the file to heal
            context: Additional context for the AI
            save_result: Whether to save the fixed code back to file

        Returns:
            HealingResult with healing details
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file
        code = path.read_text(encoding="utf-8")

        # Determine language
        language = self._detect_language(file_path)

        # Heal the code
        result = await self.heal_code(
            code=code,
            language=language,
            context=context,
            file_path=file_path,
        )

        # Save result if requested and successful
        if save_result and result.success:
            path.write_text(result.final_code, encoding="utf-8")

        return result

    async def _ask_ai_to_fix(
        self,
        code: str,
        language: str,
        errors: List[str],
        warnings: List[str],
        context: str,
        attempt_num: int,
        custom_prompt: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Use AI to fix code.

        Returns:
            Tuple of (fixed_code, prompt, response)
        """
        error_description = "\n".join(f"- {e}" for e in errors[:20])  # Limit errors
        warning_description = "\n".join(f"- {w}" for w in warnings[:10])

        if custom_prompt:
            prompt = custom_prompt.format(
                code=code,
                language=language,
                errors=error_description,
                warnings=warning_description,
                context=context,
                attempt_num=attempt_num,
            )
        else:
            prompt = self._build_fix_prompt(
                code,
                language,
                error_description,
                warning_description,
                context,
                attempt_num,
            )

        system_prompt = (
            f"You are an expert {language} developer specializing in code fixes. "
            "Your task is to fix code errors while preserving functionality. "
            "Return ONLY the complete fixed code, no explanations or markdown."
        )

        try:
            # Import here to avoid circular imports
            from vibe_coder.types.api import ApiMessage, MessageRole

            messages = [
                ApiMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ApiMessage(role=MessageRole.USER, content=prompt),
            ]

            response = await self.api_client.send_request(messages)
            fixed_code = self._extract_code_from_response(response.content, language)

            return fixed_code, prompt, response.content
        except Exception as e:
            # Return original code if AI request fails
            return code, prompt, f"Error: {str(e)}"

    def _build_fix_prompt(
        self,
        code: str,
        language: str,
        errors: str,
        warnings: str,
        context: str,
        attempt_num: int,
    ) -> str:
        """Build the prompt for fixing code."""
        parts = [
            f"Fix the following {language} code.",
            "",
            "ERRORS TO FIX:",
            errors,
        ]

        if warnings:
            parts.extend(
                [
                    "",
                    "WARNINGS (fix if possible):",
                    warnings,
                ]
            )

        parts.extend(
            [
                "",
                "ORIGINAL CODE:",
                f"```{language}",
                code,
                "```",
            ]
        )

        if context:
            parts.extend(
                [
                    "",
                    "CONTEXT:",
                    context,
                ]
            )

        if attempt_num > 1:
            parts.extend(
                [
                    "",
                    f"NOTE: This is attempt #{attempt_num}. Previous fixes failed.",
                    "Try a different approach or be more thorough with the fix.",
                ]
            )

        parts.extend(
            [
                "",
                f"Return ONLY the fixed {language} code, no explanations or markdown blocks.",
            ]
        )

        return "\n".join(parts)

    def _extract_code_from_response(self, response: str, language: str) -> str:
        """Extract code from AI response."""
        # Try to extract from markdown code block
        patterns = [
            rf"```{language}\n(.*?)```",
            r"```python\n(.*?)```",
            r"```\n(.*?)```",
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # If no code block, check if response is just code
        lines = response.strip().split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            # Skip explanatory text
            if line.startswith("#") and not line.startswith("# "):
                continue
            if "fix" in line.lower() and not line.strip().startswith(("def", "class", "import")):
                continue
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code or self._looks_like_code(line, language):
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)

        # Return the whole response as fallback
        return response.strip()

    def _looks_like_code(self, line: str, language: str) -> bool:
        """Check if a line looks like code."""
        if language.lower() == "python":
            code_indicators = [
                "import ",
                "from ",
                "def ",
                "class ",
                "if ",
                "for ",
                "while ",
                "return ",
                "    ",  # Indentation
                "self.",
                "=",
                "(",
                ")",
            ]
            return any(indicator in line for indicator in code_indicators)
        return True  # For other languages, assume it's code

    def _collect_errors(self, results: List[ValidationResult]) -> List[str]:
        """Collect all errors from validation results."""
        errors = []
        for result in results:
            errors.extend(result.errors)
        return errors

    def _collect_warnings(self, results: List[ValidationResult]) -> List[str]:
        """Collect all warnings from validation results."""
        warnings = []
        for result in results:
            warnings.extend(result.warnings)
        return warnings

    def _create_backup(self, file_path: str, content: str) -> Path:
        """Create a backup of the file before healing."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = Path(file_path).name
        backup_name = f"{file_name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        return language_map.get(ext, "text")

    def restore_backup(self, file_path: str) -> bool:
        """
        Restore the most recent backup of a file.

        Args:
            file_path: Path to the file to restore

        Returns:
            True if backup was restored, False otherwise
        """
        file_name = Path(file_path).name
        backups = sorted(
            self.backup_dir.glob(f"{file_name}.*.bak"),
            reverse=True,
        )

        if not backups:
            return False

        latest_backup = backups[0]
        content = latest_backup.read_text(encoding="utf-8")
        Path(file_path).write_text(content, encoding="utf-8")
        return True

    def list_backups(self, file_path: Optional[str] = None) -> List[Path]:
        """
        List available backups.

        Args:
            file_path: Optional file path to filter backups

        Returns:
            List of backup file paths
        """
        if not self.backup_dir.exists():
            return []

        if file_path:
            file_name = Path(file_path).name
            pattern = f"{file_name}.*.bak"
        else:
            pattern = "*.bak"

        return sorted(self.backup_dir.glob(pattern), reverse=True)

    def get_healing_stats(self) -> dict:
        """Get statistics about healing attempts."""
        if not self.healing_history:
            return {
                "total_healings": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_attempts": 0.0,
                "avg_time": 0.0,
                "total_errors_fixed": 0,
            }

        successful = sum(1 for r in self.healing_history if r.success)
        total_attempts = sum(len(r.attempts) for r in self.healing_history)
        total_time = sum(r.total_time for r in self.healing_history)
        total_fixed = sum(len(r.errors_fixed) for r in self.healing_history)

        return {
            "total_healings": len(self.healing_history),
            "successful": successful,
            "failed": len(self.healing_history) - successful,
            "success_rate": (successful / len(self.healing_history)) * 100,
            "avg_attempts": total_attempts / len(self.healing_history),
            "avg_time": total_time / len(self.healing_history),
            "total_errors_fixed": total_fixed,
        }
