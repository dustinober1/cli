"""Git integration slash commands."""

from typing import List

from ..base import CommandContext, SlashCommand
from ..git_ops import GitOperations


class GitStatusCommand(SlashCommand):
    """Show git status with AI insights."""

    def __init__(self):
        super().__init__(
            name="git-status",
            description="Show git status with AI insights",
            aliases=["gst", "status"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        status = await git_ops.get_status()

        if "error" in status:
            return f"Error getting git status: {status['error']}"

        # Format the status information
        result = f"Git Status - Branch: {status.get('branch', 'unknown')}\n\n"

        if status.get("ahead", 0) > 0 or status.get("behind", 0) > 0:
            result += f"Branch is {status['ahead']} ahead, {status['behind']} behind\n\n"

        if status.get("staged"):
            result += f"Staged changes ({len(status['staged'])} files):\n"
            for file in status["staged"]:
                result += f"  ✓ {file}\n"

        if status.get("modified"):
            result += f"\nModified files ({len(status['modified'])} files):\n"
            for file in status["modified"]:
                result += f"  • {file}\n"

        if status.get("untracked"):
            result += f"\nUntracked files ({len(status['untracked'])} files):\n"
            for file in status["untracked"]:
                result += f"  ? {file}\n"

        if status.get("conflicts"):
            result += f"\nConflicts ({len(status['conflicts'])} files):\n"
            for file in status["conflicts"]:
                result += f"  ✗ {file}\n"

        # Add AI insights placeholder
        result += "\nAI Insights (placeholder):\n"
        result += "- Consider staging modified files before committing\n"
        result += "- Untracked files may need to be added to .gitignore\n"

        return result

    def requires_git_repo(self) -> bool:
        return True


class GitCommitCommand(SlashCommand):
    """Generate smart commit messages."""

    def __init__(self):
        super().__init__(
            name="git-commit",
            description="Generate smart commit messages",
            aliases=["gc", "commit"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        message = " ".join(args) if args else None

        if message:
            # Commit with provided message
            success = await git_ops.commit(message)
            if success:
                return f"Successfully committed with message: {message}"
            else:
                return "Failed to commit. Check if there are staged changes."
        else:
            # Generate commit message
            diff = await git_ops.get_diff(staged=True)
            if not diff.strip():
                return "No staged changes to commit. Use /git-status to see changes."

            # This would call AI to generate commit message
            generated_message = await git_ops.generate_commit_message(diff)
            return (
                f"Generated commit message: {generated_message}\n"
                f"Use '/git-commit \"{generated_message}\"' to commit."
            )


class GitDiffCommand(SlashCommand):
    """Explain git diff."""

    def __init__(self):
        super().__init__(
            name="git-diff", description="Explain git diff", aliases=["gd", "diff"], category="git"
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        filepath = args[0] if args else None
        staged = "--staged" in args if args else False

        diff = await git_ops.get_diff(filepath, staged)

        if not diff.strip():
            return "No differences found."

        return f"""Git Diff{f' for {filepath}' if filepath else ''}:

```
{diff[:1000]}{'...' if len(diff) > 1000 else ''}
```

AI Summary (placeholder):
- [AI would summarize the changes here]
- [AI would identify potential issues]
- [AI would suggest next steps]
"""


class GitReviewCommand(SlashCommand):
    """Review recent commits."""

    def __init__(self):
        super().__init__(
            name="git-review",
            description="Review recent commits",
            aliases=["gr", "review"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        max_count = 10
        if args and args[0].isdigit():
            max_count = int(args[0])

        commits = await git_ops.get_log(max_count)

        if not commits:
            return "No commits found."

        result = f"Recent {len(commits)} commits:\n\n"
        for i, commit in enumerate(commits, 1):
            result += f"{i}. {commit['hash'][:8]} - {commit['author']}\n"
            result += f"   {commit['date']}\n"
            result += f"   {commit['message']}\n\n"

        result += "AI Analysis (placeholder):\n"
        result += "- [AI would analyze commit patterns]\n"
        result += "- [AI would identify potential issues]\n"

        return result

    def requires_git_repo(self) -> bool:
        return True


class GitMergeCommand(SlashCommand):
    """Merge conflict assistance."""

    def __init__(self):
        super().__init__(
            name="git-merge",
            description="Merge conflict assistance",
            aliases=["merge", "gm"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        if not args:
            return (
                "Usage: /git-merge <branch_name>. Get assistance with merging the specified branch."
            )

        branch_name = args[0]

        # Check for conflicts
        status = await git_ops.get_status()
        if status.get("conflicts"):
            return f"""Merge conflicts detected in {len(status['conflicts'])} files:

{chr(10).join(f"  ✗ {file}" for file in status['conflicts'])}

AI Resolution Suggestions (placeholder):
- [AI would analyze each conflict]
- [AI would suggest resolutions]
- [AI would provide code examples]

Use /git-diff to see detailed conflicts."""
        else:
            return f"No active merge conflicts detected. Ready to merge {branch_name}."

    def requires_git_repo(self) -> bool:
        return True

    def get_min_args(self) -> int:
        return 1


class GitBranchCommand(SlashCommand):
    """Create and switch branches."""

    def __init__(self):
        super().__init__(
            name="git-branch",
            description="Create and switch branches",
            aliases=["branch", "gb"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        git_ops = GitOperations(context.working_directory)

        if not git_ops.is_git_repo():
            return "This directory is not a Git repository."

        if not args:
            # List branches
            branches = await git_ops.get_branches()
            result = "Branches:\n\n"
            result += "Local branches:\n"
            for branch in branches["local"]:
                result += f"  {branch}\n"
            result += "\nRemote branches:\n"
            for branch in branches["remote"]:
                result += f"  {branch}\n"
            return result

        branch_name = args[0]
        create_new = "--create" in args or "-c" in args

        if create_new:
            success = await git_ops.create_branch(branch_name)
            if success:
                return f"Created and switched to new branch: {branch_name}"
            else:
                return f"Failed to create branch: {branch_name}"
        else:
            success = await git_ops.checkout_branch(branch_name)
            if success:
                return f"Switched to branch: {branch_name}"
            else:
                return f"Failed to switch to branch: {branch_name}"

    def requires_git_repo(self) -> bool:
        return True
