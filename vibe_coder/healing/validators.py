"""
Code validators for the auto-healing system.

This module provides validation strategies for Python code including
syntax checking, type checking, linting, and test execution.
"""

import ast
import asyncio
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from vibe_coder.healing.types import ValidationResult, ValidationStrategy


class CodeValidator:
    """Run various validations on code."""

    def __init__(
        self,
        project_root: Optional[str] = None,
        python_executable: Optional[str] = None,
    ):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.python_executable = python_executable or sys.executable

    async def validate(
        self,
        code: str,
        language: str,
        strategies: List[ValidationStrategy],
        file_path: Optional[str] = None,
    ) -> List[ValidationResult]:
        """
        Run multiple validation strategies on code.

        Args:
            code: The code to validate
            language: Programming language (e.g., "python")
            strategies: List of validation strategies to run
            file_path: Optional path for context-aware validation

        Returns:
            List of ValidationResult for each strategy
        """
        results = []

        for strategy in strategies:
            if strategy == ValidationStrategy.SYNTAX:
                result = await self.validate_syntax(code, language)
            elif strategy == ValidationStrategy.TYPE_CHECK:
                result = await self.validate_types(code, language, file_path)
            elif strategy == ValidationStrategy.LINT:
                result = await self.validate_linting(code, language, file_path)
            elif strategy == ValidationStrategy.TESTS:
                result = await self.validate_tests(file_path)
            elif strategy == ValidationStrategy.BUILD:
                result = await self.validate_build()
            else:
                result = ValidationResult(
                    is_valid=True,
                    strategy=strategy,
                    warnings=["Custom validation not implemented"],
                )

            results.append(result)

        return results

    async def validate_syntax(self, code: str, language: str) -> ValidationResult:
        """
        Check if code has syntax errors.

        Args:
            code: Source code to validate
            language: Programming language

        Returns:
            ValidationResult with syntax check results
        """
        start_time = time.time()
        errors = []
        warnings = []

        if language.lower() == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                error_msg = f"Line {e.lineno}: {e.msg}"
                if e.text:
                    error_msg += f" - {e.text.strip()}"
                errors.append(error_msg)
        else:
            warnings.append(f"Syntax validation not supported for {language}")

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.SYNTAX,
            execution_time=execution_time,
        )

    async def validate_types(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None,
    ) -> ValidationResult:
        """
        Run type checker on code.

        Args:
            code: Source code to validate
            language: Programming language
            file_path: Optional original file path for context

        Returns:
            ValidationResult with type checking results
        """
        start_time = time.time()
        errors = []
        warnings = []

        if language.lower() != "python":
            return ValidationResult(
                is_valid=True,
                warnings=[f"Type checking not supported for {language}"],
                strategy=ValidationStrategy.TYPE_CHECK,
                execution_time=time.time() - start_time,
            )

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run mypy
            result = await self._run_subprocess(
                [self.python_executable, "-m", "mypy", "--no-error-summary", tmp_path],
                timeout=30,
            )

            if result["returncode"] != 0:
                # Parse mypy output
                for line in result["stdout"].strip().split("\n"):
                    if line and ":" in line:
                        # Replace temp file path with original
                        if file_path:
                            line = line.replace(tmp_path, file_path)
                        if "error:" in line.lower():
                            errors.append(line)
                        elif "warning:" in line.lower():
                            warnings.append(line)
                        elif "note:" not in line.lower():
                            errors.append(line)

        except FileNotFoundError:
            warnings.append("mypy not installed - skipping type check")
        except Exception as e:
            warnings.append(f"Type check failed: {str(e)}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.TYPE_CHECK,
            execution_time=execution_time,
        )

    async def validate_linting(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None,
    ) -> ValidationResult:
        """
        Run linter on code.

        Args:
            code: Source code to validate
            language: Programming language
            file_path: Optional original file path for context

        Returns:
            ValidationResult with linting results
        """
        start_time = time.time()
        errors = []
        warnings = []

        if language.lower() != "python":
            return ValidationResult(
                is_valid=True,
                warnings=[f"Linting not supported for {language}"],
                strategy=ValidationStrategy.LINT,
                execution_time=time.time() - start_time,
            )

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run flake8
            result = await self._run_subprocess(
                [
                    self.python_executable,
                    "-m",
                    "flake8",
                    "--max-line-length=100",
                    tmp_path,
                ],
                timeout=30,
            )

            if result["returncode"] != 0:
                for line in result["stdout"].strip().split("\n"):
                    if line:
                        # Replace temp file path with original
                        if file_path:
                            line = line.replace(tmp_path, file_path)

                        # Classify by error code
                        if ":E" in line or ":F" in line:
                            errors.append(line)
                        elif ":W" in line:
                            warnings.append(line)
                        else:
                            warnings.append(line)

        except FileNotFoundError:
            warnings.append("flake8 not installed - skipping lint check")
        except Exception as e:
            warnings.append(f"Lint check failed: {str(e)}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.LINT,
            execution_time=execution_time,
        )

    async def validate_tests(self, file_path: Optional[str] = None) -> ValidationResult:
        """
        Run tests related to a file.

        Args:
            file_path: Path to the file being validated

        Returns:
            ValidationResult with test results
        """
        start_time = time.time()
        errors = []
        warnings = []
        details = {}

        if not file_path:
            return ValidationResult(
                is_valid=True,
                warnings=["No file path provided for test validation"],
                strategy=ValidationStrategy.TESTS,
                execution_time=time.time() - start_time,
            )

        # Find test file for the given source file
        test_file = self._find_test_file(file_path)

        if not test_file:
            return ValidationResult(
                is_valid=True,
                warnings=[f"No test file found for {file_path}"],
                strategy=ValidationStrategy.TESTS,
                execution_time=time.time() - start_time,
            )

        try:
            # Run pytest
            result = await self._run_subprocess(
                [
                    self.python_executable,
                    "-m",
                    "pytest",
                    str(test_file),
                    "-v",
                    "--tb=short",
                ],
                timeout=60,
                cwd=str(self.project_root),
            )

            details["test_output"] = result["stdout"]

            if result["returncode"] != 0:
                # Parse pytest output for failures
                for line in result["stdout"].split("\n"):
                    if "FAILED" in line:
                        errors.append(line.strip())
                    elif "ERROR" in line:
                        errors.append(line.strip())

                if not errors:
                    errors.append(f"Tests failed with exit code {result['returncode']}")

        except FileNotFoundError:
            warnings.append("pytest not installed - skipping test validation")
        except Exception as e:
            warnings.append(f"Test validation failed: {str(e)}")

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.TESTS,
            execution_time=execution_time,
            details=details,
        )

    async def validate_build(self) -> ValidationResult:
        """
        Attempt to build/compile the project.

        Returns:
            ValidationResult with build results
        """
        start_time = time.time()
        errors = []
        warnings = []

        # Check for common build files
        pyproject = self.project_root / "pyproject.toml"
        makefile = self.project_root / "Makefile"

        if pyproject.exists():
            try:
                # Try poetry check
                result = await self._run_subprocess(
                    ["poetry", "check"],
                    timeout=30,
                    cwd=str(self.project_root),
                )
                if result["returncode"] != 0:
                    errors.append(f"Poetry check failed: {result['stdout']}")
            except FileNotFoundError:
                # Try pip check
                result = await self._run_subprocess(
                    [self.python_executable, "-m", "pip", "check"],
                    timeout=30,
                )
                if result["returncode"] != 0:
                    errors.append(f"Pip check failed: {result['stdout']}")
        elif makefile.exists():
            try:
                result = await self._run_subprocess(
                    ["make", "--dry-run"],
                    timeout=30,
                    cwd=str(self.project_root),
                )
                if result["returncode"] != 0:
                    errors.append(f"Make dry-run failed: {result['stdout']}")
            except FileNotFoundError:
                warnings.append("make not available")
        else:
            warnings.append("No build configuration found")

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.BUILD,
            execution_time=execution_time,
        )

    async def validate_custom(self, script: str, code: str) -> ValidationResult:
        """
        Run user-defined validation script.

        Args:
            script: Custom validation script to run
            code: Code to validate (passed as stdin)

        Returns:
            ValidationResult with custom validation results
        """
        start_time = time.time()
        errors = []
        warnings = []

        try:
            result = await self._run_subprocess(
                ["/bin/sh", "-c", script],
                timeout=60,
                input_data=code,
                cwd=str(self.project_root),
            )

            if result["returncode"] != 0:
                for line in result["stdout"].split("\n"):
                    if line.strip():
                        errors.append(line.strip())
                for line in result["stderr"].split("\n"):
                    if line.strip():
                        errors.append(line.strip())

        except Exception as e:
            errors.append(f"Custom validation failed: {str(e)}")

        execution_time = time.time() - start_time

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy=ValidationStrategy.CUSTOM,
            execution_time=execution_time,
        )

    async def _run_subprocess(
        self,
        cmd: List[str],
        timeout: int = 30,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> Dict[str, any]:
        """Run a subprocess asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                cwd=cwd,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=timeout,
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            process.kill()
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }

    def _find_test_file(self, source_path: str) -> Optional[Path]:
        """Find the test file for a given source file."""
        source = Path(source_path)
        file_name = source.stem

        # Common test file patterns
        patterns = [
            f"test_{file_name}.py",
            f"{file_name}_test.py",
            f"tests/test_{file_name}.py",
            f"tests/{file_name}_test.py",
            f"test/test_{file_name}.py",
        ]

        # Try relative to project root
        for pattern in patterns:
            test_path = self.project_root / pattern
            if test_path.exists():
                return test_path

        # Try relative to source file
        for pattern in patterns:
            test_path = source.parent / pattern
            if test_path.exists():
                return test_path

        # Try in parallel tests directory
        if "vibe_coder" in str(source):
            relative = str(source).split("vibe_coder/")[-1]
            test_path = self.project_root / "tests" / f"test_{relative}"
            if test_path.exists():
                return test_path

        return None

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, any]:
        """Get summary of validation results."""
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        all_valid = all(r.is_valid for r in results)
        total_time = sum(r.execution_time for r in results)

        return {
            "all_valid": all_valid,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_time": total_time,
            "strategies_run": [r.strategy.value for r in results],
            "failed_strategies": [r.strategy.value for r in results if not r.is_valid],
        }
