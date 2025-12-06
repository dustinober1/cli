"""Security and auditing commands."""

import asyncio
from typing import List

from vibe_coder.commands.slash.base import CommandContext, SlashCommand
from vibe_coder.commands.slash.file_ops import FileOperations


class SecurityScanCommand(SlashCommand):
    """Run security scan on codebase."""

    def __init__(self):
        super().__init__(
            name="security-scan",
            description="Run security scan on codebase (using bandit if available)",
            aliases=["scan", "audit"],
            category="security",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # Check for bandit
        import shutil
        bandit_path = shutil.which("bandit")

        if not bandit_path:
            return "Security scan requires `bandit`. Install it with `pip install bandit`."

        import subprocess
        target = args[0] if args else "."

        try:
            # Run bandit
            process = await asyncio.create_subprocess_exec(
                "bandit", "-r", target, "-f", "txt",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if stdout:
                return f"🛡️ **Security Scan Results**\n\n```\n{stdout.decode()[:2000]}\n```"
            else:
                return "No issues found or scan failed."

        except Exception as e:
            return f"Scan failed: {e}"


class SecretsCommand(SlashCommand):
    """Scan for hardcoded secrets."""

    def __init__(self):
        super().__init__(
            name="secrets",
            description="Scan for potential hardcoded secrets",
            aliases=["leaks"],
            category="security",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        # Simple regex-based scanner for MVP
        import re

        patterns = {
            "API Key": r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?key).*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
            "AWS Key": r"AKIA[0-9A-Z]{16}",
            "Private Key": r"-----BEGIN PRIVATE KEY-----",
        }

        file_ops = FileOperations(context.working_directory)
        # We need to scan files. file_ops doesn't have "list_files" public method easily accessible
        # that returns all files recursively efficiently without implementing it.
        # But we can use os.walk or git ls-files if repo.

        found_secrets = []

        import os
        for root, _, files in os.walk(context.working_directory):
            if ".git" in root or "__pycache__" in root:
                continue

            for file in files:
                if file.endswith((".py", ".env", ".json", ".yaml", ".yml", ".js", ".ts")):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            for name, pattern in patterns.items():
                                if re.search(pattern, content):
                                    found_secrets.append(f"{name} in {os.path.relpath(path, context.working_directory)}")
                    except:
                        pass

        if found_secrets:
            return "⚠️ **Potential Secrets Found:**\n" + "\n".join(f"- {s}" for s in found_secrets)
        else:
            return "✅ No obvious secrets found (basic scan)."
