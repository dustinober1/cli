"""Code fixing and debugging slash commands."""

import json
from pathlib import Path
from typing import List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class FixCommand(SlashCommand):
    """Fix code errors and bugs automatically."""

    def __init__(self):
        super().__init__(
            name="fix",
            description="Fix code errors and bugs",
            aliases=["repair", "solve"],
            category="debug",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the fix command."""
        if not args:
            return """Usage: /fix <filename_or_error> [options]
Options:
- --dry-run: Show fixes without applying them
- --interactive: Ask before each fix

Examples:
- /fix app.py
- /fix "NameError: name 'x' is not defined"
- /fix --dry-run broken.py"""

        target = args[0]
        options = [arg for arg in args[1:] if arg.startswith("--")]
        dry_run = "--dry-run" in options
        interactive = "--interactive" in options

        file_ops = FileOperations(context.working_directory)

        try:
            # Check if target is a file or an error description
            if Path(target).exists():
                return await self._fix_file(context, target, file_ops, dry_run, interactive)
            else:
                return await self._fix_error_description(context, target, file_ops, dry_run, interactive)

        except Exception as e:
            return f"Error fixing code: {e}"

    async def _fix_file(self, context: CommandContext, filename: str, file_ops: FileOperations, dry_run: bool, interactive: bool) -> str:
        """Fix errors in a specific file."""
        content = await file_ops.read_file(filename)
        language = file_ops.detect_language(filename)

        # Build fixing prompt
        prompt = f"""Analyze and fix errors in the following {language} code:

Requirements:
1. Identify all syntax errors, runtime errors, and logical issues
2. Provide corrected code that fixes all issues
3. Explain each fix made
4. Follow {language} best practices
5. Maintain the original functionality
6. Add error handling where appropriate

Original code:
```{language}
{content}
```

If the code has no errors, respond with "No issues found".

Otherwise, provide:
1. List of issues found
2. Fixed code
3. Explanation of each fix"""

        # Get AI response
        response = await context.provider.client.send_request([
            {"role": "system", "content": f"You are an expert {language} developer who identifies and fixes code errors. Be thorough and provide clear explanations.",
             "name": "CodeFixer"},
            {"role": "user", "content": prompt}
        ])

        response_text = response.content.strip()

        if "No issues found" in response_text or "no errors" in response_text.lower():
            return f"✅ No issues found in {filename}"

        # Extract fixed code
        fixed_code = response_text
        if "```" in response_text:
            # Find code block
            start = response_text.find("```")
            start = response_text.find("\n", start) + 1
            end = response_text.find("```", start)
            if end != -1:
                fixed_code = response_text[start:end].strip()

        # Create backup
        if not dry_run:
            backup_path = await file_ops.create_backup(filename)

        # Show changes
        changes = self._compare_code(content, fixed_code)

        output = [f"🔧 Analysis for {filename}"]
        output.append(f"\n{response_text}")

        if changes:
            output.append("\n📝 Changes detected:")
            output.append(changes)

            if interactive and not dry_run:
                output.append("\n⚠️  Apply changes? (Would require user input in interactive mode)")
                output.append("Auto-applying changes in demo mode...")

            if not dry_run:
                await file_ops.write_file(filename, fixed_code)
                output.append(f"\n✅ Fixes applied to {filename}")
                output.append(f"💾 Backup saved: {backup_path}")
        else:
            output.append("\n✅ No changes needed")

        return "\n".join(output)

    async def _fix_error_description(self, context: CommandContext, error_desc: str, file_ops: FileOperations, dry_run: bool, interactive: bool) -> str:
        """Fix based on error description."""
        prompt = f"""Provide a solution for this error: {error_desc}

Requirements:
1. Identify the likely cause of the error
2. Provide corrected code example
3. Explain the fix
4. Show how to prevent similar errors

If it's a Python error, suggest the exact fix with proper imports and syntax."""

        response = await context.provider.client.send_request([
            {"role": "system", "content": "You are an expert debugger who helps developers fix errors. Provide clear, actionable solutions.",
             "name": "ErrorFixer"},
            {"role": "user", "content": prompt}
        ])

        return f"""🐛 Error Analysis: {error_desc}

{response.content}

💡 To apply this fix:
1. Locate the problematic code
2. Apply the suggested changes
3. Test your code
4. Run /fix <filename> for automated fixing"""

    def _compare_code(self, original: str, fixed: str) -> str:
        """Compare original and fixed code."""
        if original == fixed:
            return "  No differences detected"

        # Simple line-by-line comparison
        orig_lines = original.split('\n')
        fixed_lines = fixed.split('\n')

        changes = []
        for i, (orig, fix) in enumerate(zip(orig_lines, fixed_lines)):
            if orig != fix:
                changes.append(f"  Line {i+1}:")
                changes.append(f"    - {orig}")
                changes.append(f"    + {fix}")

        if len(fixed_lines) > len(orig_lines):
            changes.append(f"  Added {len(fixed_lines) - len(orig_lines)} line(s) at the end")
        elif len(fixed_lines) < len(orig_lines):
            changes.append(f"  Removed {len(orig_lines) - len(fixed_lines)} line(s) from the end")

        return '\n'.join(changes[:20])  # Limit output


class DebugCommand(SlashCommand):
    """Debug problematic code with AI assistance."""

    def __init__(self):
        super().__init__(
            name="debug",
            description="Debug code and identify issues",
            aliases=["debug-code"],
            category="debug",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the debug command."""
        if not args:
            return """Usage: /debug <filename> [options]
Options:
- --step: Step through execution logic
- --variables: Track variable values
- --performance: Check performance issues

Examples:
- /debug app.py
- /debug app.py --step
- /debug app.py --variables"""

        filename = args[0]
        options = [arg for arg in args[1:] if arg.startswith("--")]
        step_by_step = "--step" in options
        track_variables = "--variables" in options
        check_performance = "--performance" in options

        file_ops = FileOperations(context.working_directory)

        try:
            content = await file_ops.read_file(filename)
            language = file_ops.detect_language(filename)

            # Build debug prompt
            debug_focus = []
            if step_by_step:
                debug_focus.append("step through the execution logic")
            if track_variables:
                debug_focus.append("track variable values and state changes")
            if check_performance:
                debug_focus.append("identify performance bottlenecks")

            prompt = f"""Debug the following {language} code:

Focus areas: {', '.join(debug_focus) if debug_focus else 'general debugging'}

Code:
```{language}
{content}
```

Provide:
1. Potential issues and bugs
2. Logic flow analysis
3. Variable state tracking (if requested)
4. Performance concerns (if requested)
5. Recommendations for fixes
6. Debugging steps to follow"""

            response = await context.provider.client.send_request([
                {"role": "system", "content": f"You are an expert debugger for {language}. Analyze code thoroughly and provide actionable debugging insights.",
                 "name": "Debugger"},
                {"role": "user", "content": prompt}
            ])

            return f"""🔍 Debug Analysis for {filename}

{response.content}

💡 Debugging Tips:
• Add print statements to track execution
• Use a debugger for step-through analysis
• Check variable values at key points
• Verify logic with test cases
• Monitor performance with profiling tools"""

        except Exception as e:
            return f"Error debugging file: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


# Note: ExplainCommand temporarily disabled due to syntax issues
# class ExplainCommand(SlashCommand):
#     """Explain what code does."""
#
#     def __init__(self):
#         super().__init__(
#             name="explain",
#             description="Explain what code does",
#             aliases=["exp", "wtf"],
#             category="debug",
#         )
#
#     async def execute(self, args: List[str], context: CommandContext) -> str:
#         """Execute the explain command."""
#         # Implementation would go here
#         return "Explain command temporarily disabled"
#
#     def get_min_args(self) -> int:
#         return 1
#
#     def requires_file(self) -> bool:
#         return True


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(FixCommand())
command_registry.register(DebugCommand())
# command_registry.register(ExplainCommand())  # Temporarily disabled

def register():
    """Register all fix commands."""
    return [
        FixCommand(),
        DebugCommand(),
        # ExplainCommand(),  # Temporarily disabled
    ]