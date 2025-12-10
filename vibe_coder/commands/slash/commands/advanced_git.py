"""Advanced Git and version control slash commands."""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..base import CommandContext, SlashCommand
from ..git_ops import GitOperations


class GitBisectCommand(SlashCommand):
    """Automated git bisect for finding bugs."""

    def __init__(self):
        super().__init__(
            name="git-bisect",
            description="Automated git bisect to find the commit that introduced a bug",
            aliases=["bisect", "find-bug"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-bisect command."""
        if len(args) < 2:
            return """Usage: /git-bisect <start_commit> <end_commit> [test_command]
Arguments:
- start_commit: Known good commit (or tag/branch)
- end_commit: Known bad commit (defaults to HEAD)
- test_command: Command to test for the bug (default: runs tests)

Example:
- /git-bisect v1.0.0 HEAD "python -m pytest test_failing.py"
- /git-bisect HEAD~10 HEAD "npm test"
- /git-bisect main main "make test" """

        start_commit = args[0]
        end_commit = args[1] if len(args) > 1 else "HEAD"
        test_command = args[2] if len(args) > 2 else None

        git_ops = GitOperations(context.working_directory)

        try:
            # Verify we're in a git repo
            if not git_ops.is_git_repo():
                return "Error: Not in a Git repository."

            # Check if bisect is already in progress
            bisect_status = subprocess.run(
                ["git", "bisect", "log"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if bisect_status.returncode == 0 and bisect_status.stdout.strip():
                # Bisect is in progress, offer to reset
                return """Git bisect is already in progress.
Options:
- Continue: /git-bisect continue
- Reset: /git-bisect reset
- View status: /git-bisect status"""

            # If no test command provided, try to auto-detect
            if not test_command:
                test_command = await self._detect_test_command(context)

            # Create a bisect script
            bisect_script = await self._create_bisect_script(
                context, test_command, start_commit, end_commit
            )

            # Start the bisect
            bisect_start = subprocess.run(
                ["git", "bisect", "start"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if bisect_start.returncode != 0:
                return f"Error starting bisect: {bisect_start.stderr}"

            # Mark commits
            subprocess.run(
                ["git", "bisect", "bad", end_commit],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            subprocess.run(
                ["git", "bisect", "good", start_commit],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            # Run automated bisect
            if test_command:
                bisect_result = subprocess.run(
                    ["git", "bisect", "run", test_command],
                    capture_output=True,
                    text=True,
                    cwd=context.working_directory
                )

                # Get bisect results
                bisect_log = subprocess.run(
                    ["git", "bisect", "log"],
                    capture_output=True,
                    text=True,
                    cwd=context.working_directory
                )

                return f"""
Git bisect completed!

Results:
- First bad commit: {self._extract_first_bad_commit(bisect_log.stdout)}
- Test command: {test_command}
- Bisect script saved: {bisect_script}

Next steps:
- View the commit: git show <commit-hash>
- Reset bisect: git bisect reset
- Analyze the changes: git diff <commit-hash>^ <commit-hash>

{bisect_result.stdout if bisect_result.returncode == 0 else bisect_result.stderr}
"""
            else:
                return f"""
Git bisect started manually!

Range: {start_commit} (good) → {end_commit} (bad)
Status: Ready for manual testing

Commands:
- Test current commit: {test_command or '[your test command]'}
- Mark as good: git bisect good
- Mark as bad: git bisect bad
- View current commit: git bisect visualize
- Reset: git bisect reset

Bisect script created: {bisect_script}
"""

        except Exception as e:
            return f"Error running git bisect: {e}"

    async def _detect_test_command(self, context: CommandContext) -> Optional[str]:
        """Auto-detect appropriate test command."""
        test_commands = [
            # Python
            "python -m pytest",
            "python -m unittest discover",
            "python setup.py test",
            # JavaScript/Node
            "npm test",
            "yarn test",
            "pnpm test",
            # Java
            "mvn test",
            "gradle test",
            # Go
            "go test ./...",
            # Ruby
            "bundle exec rspec",
            "bundle exec rake test",
            # PHP
            "composer test",
            "php vendor/bin/phpunit",
            # Rust
            "cargo test",
        ]

        # Check for project files to determine language
        project_files = {
            "package.json": ["npm test", "yarn test", "pnpm test"],
            "requirements.txt": ["python -m pytest", "python -m unittest discover"],
            "setup.py": ["python setup.py test"],
            "pyproject.toml": ["python -m pytest", "python -m unittest discover"],
            "Cargo.toml": ["cargo test"],
            "pom.xml": ["mvn test", "gradle test"],
            "build.gradle": ["gradle test", "mvn test"],
            "Gemfile": ["bundle exec rspec", "bundle exec rake test"],
            "composer.json": ["composer test", "php vendor/bin/phpunit"],
        }

        # Check for project files
        for file, commands in project_files.items():
            if Path(context.working_directory / file).exists():
                return commands[0]

        # Default to pytest if Python files exist
        if list(Path(context.working_directory).glob("**/*.py")):
            return "python -m pytest"

        return None

    async def _create_bisect_script(
        self,
        context: CommandContext,
        test_command: str,
        start_commit: str,
        end_commit: str
    ) -> str:
        """Create a bisect script for reproducibility."""
        script_content = f'''#!/bin/bash
# Git bisect script for finding the bug

# Bisect range: {start_commit} (good) → {end_commit} (bad)
# Test command: {test_command}

echo "Starting git bisect..."
git bisect start
git bisect bad {end_commit}
git bisect good {start_commit}

echo "Running automated bisect with: {test_command}"
git bisect run {test_command}

echo "Bisect complete. First bad commit:"
git bisect log | grep "first bad commit"

echo "\\nTo reset bisect, run: git bisect reset"
'''

        script_path = Path(context.working_directory) / "bisect_bug.sh"
        script_path.write_text(script_content)
        script_path.chmod(0o755)

        return str(script_path)

    def _extract_first_bad_commit(self, log_output: str) -> str:
        """Extract the first bad commit from bisect log."""
        for line in log_output.split('\n'):
            if "first bad commit" in line:
                # Extract commit hash
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "commit" and i + 1 < len(parts):
                        return parts[i + 1]
        return "Unknown"

    def requires_git_repo(self) -> bool:
        return True

    def get_min_args(self) -> int:
        return 2


class GitRebaseCommand(SlashCommand):
    """Smart rebase assistance."""

    def __init__(self):
        super().__init__(
            name="git-rebase",
            description="Intelligent rebase assistance with conflict prevention",
            aliases=["rebase-help", "smart-rebase"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-rebase command."""
        if not args:
            return """Usage: /git-rebase <branch_or_commit> [options]
Options:
- --interactive: Start interactive rebase
- --auto-squash: Automatically group related commits
- --conflict-check: Check for potential conflicts before rebasing

Examples:
- /git-rebase main --conflict-check
- /git-rebase HEAD~5 --interactive
- /git-rebase feature-branch --auto-squash"""

        target = args[0]
        options = args[1:] if len(args) > 1 else []

        git_ops = GitOperations(context.working_directory)

        try:
            # Check for potential conflicts if requested
            if "--conflict-check" in options:
                conflicts = await self._check_rebase_conflicts(context, target)
                if conflicts:
                    conflict_info = "\n⚠️  Potential conflicts detected:\n"
                    for file, conflict_type in conflicts:
                        conflict_info += f"  • {file}: {conflict_type}\n"

                    conflict_info += f"\nRecommendations:\n"
                    conflict_info += "  1. Commit or stash your changes first\n"
                    conflict_info += "  2. Consider merging instead of rebasing\n"
                    conflict_info += "  3. Resolve conflicts manually after rebase\n"

                    return conflict_info

            # Auto-squash related commits if requested
            if "--auto-squash" in options:
                squash_info = await self._auto_squash_commits(context, target)
                return f"""Auto-squash recommendations:

{squash_info}

To execute:
git rebase -i {target} --autosquash
"""

            # Start interactive rebase if requested
            if "--interactive" in options:
                # Generate rebase plan
                plan = await self._generate_rebase_plan(context, target)
                return f"""Interactive rebase plan for '{target}':

{plan}

To start interactive rebase:
git rebase -i {target}

Rebase commands:
- pick: Use commit
- reword: Use commit, edit message
- edit: Use commit, stop for amending
- squash: Combine with previous commit
- fixup: Like squash, discard message
- exec: Run command
"""

            # Default: provide rebase guidance
            return f"""Rebase guidance for '{target}':

Current status:
- Current branch: {git_ops.get_current_branch()}
- Target: {target}
- Commits ahead: {git_ops.get_commits_ahead(target)}

Before rebasing:
1. Ensure working directory is clean
2. Commit or stash changes
3. Pull latest changes from remote
4. Consider backing up current branch

Rebase command:
git rebase {target}

If conflicts occur:
1. git status to see conflicts
2. Resolve conflicts in files
3. git add <resolved-files>
4. git rebase --continue
5. Or git rebase --abort to cancel

To undo rebase:
git reflog
git reset --hard HEAD@{{n}}
"""

        except Exception as e:
            return f"Error with rebase: {e}"

    async def _check_rebase_conflicts(
        self, context: CommandContext, target: str
    ) -> List[tuple]:
        """Check for potential rebase conflicts."""
        conflicts = []

        # Get files that changed between branches
        try:
            # Get merge base
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", target],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if merge_base.returncode != 0:
                return []

            # Check for conflicting changes
            diff_result = subprocess.run(
                ["git", "diff", "--name-only", merge_base.stdout.strip(), "HEAD"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if diff_result.returncode == 0:
                changed_files = diff_result.stdout.strip().split('\n')

                # Check if target also changed these files
                for file in changed_files:
                    if file:
                        target_diff = subprocess.run(
                            ["git", "diff", "--name-only", merge_base.stdout.strip(), target, "--", file],
                            capture_output=True,
                            text=True,
                            cwd=context.working_directory
                        )

                        if target_diff.returncode == 0 and target_diff.stdout.strip():
                            conflicts.append((file, "Modified in both branches"))

        except Exception:
            pass

        return conflicts

    async def _auto_squash_commits(
        self, context: CommandContext, target: str
    ) -> str:
        """Analyze commits and suggest squashing."""
        try:
            # Get commit list
            commits = subprocess.run(
                ["git", "log", "--oneline", f"{target}..HEAD"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if commits.returncode != 0:
                return "Could not retrieve commit history"

            commit_lines = commits.stdout.strip().split('\n')
            if not commit_lines or commit_lines == ['']:
                return "No commits to analyze"

            # Group commits by message patterns
            groups = {}
            for line in commit_lines:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    hash_val, message = parts
                    # Simple grouping by first word
                    key = message.split()[0] if message else "misc"
                    if key not in groups:
                        groups[key] = []
                    groups[key].append((hash_val, message))

            # Generate suggestions
            suggestions = ""
            for group_name, group_commits in groups.items():
                if len(group_commits) > 1:
                    suggestions += f"\n📦 {group_name.title()} ({len(group_commits)} commits):\n"
                    for hash_val, message in group_commits:
                        suggestions += f"  {hash_val} {message}\n"
                    suggestions += f"  → Suggestion: squash into '{group_name.title()}'\n"

            return suggestions if suggestions else "No related commits to squash"

        except Exception as e:
            return f"Error analyzing commits: {e}"

    async def _generate_rebase_plan(
        self, context: CommandContext, target: str
    ) -> str:
        """Generate an interactive rebase plan."""
        try:
            # Get detailed commit info
            commits = subprocess.run(
                ["git", "log", "--oneline", "--format=%h %s", f"{target}..HEAD"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if commits.returncode != 0:
                return "Could not generate rebase plan"

            commit_lines = commits.stdout.strip().split('\n')
            plan = ""

            for line in commit_lines:
                if not line:
                    continue
                parts = line.split(' ', 1)
                hash_val = parts[0]
                message = parts[1] if len(parts) > 1 else ""

                # Suggest rebase action based on message
                action = "pick"  # default

                if "fixup" in message.lower() or "fix:" in message.lower():
                    action = "fixup"
                elif "wip" in message.lower():
                    action = "squash"
                elif message.startswith("Revert"):
                    action = "drop"
                elif "temp" in message.lower():
                    action = "drop"

                plan += f"{action} {hash_val} {message}\n"

            return plan

        except Exception as e:
            return f"Error generating plan: {e}"

    def requires_git_repo(self) -> bool:
        return True

    def get_min_args(self) -> int:
        return 1


class GitCherryPickCommand(SlashCommand):
    """Intelligent cherry-picking with dependency detection."""

    def __init__(self):
        super().__init__(
            name="git-cherry-pick",
            description="Intelligent cherry-picking with dependency detection",
            aliases=["cpick", "smart-pick"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-cherry-pick command."""
        if not args:
            return """Usage: /git-cherry-pick <commit> [options]
Options:
- --with-deps: Automatically include dependent commits
- --no-conflict: Check for conflicts before cherry-picking

Examples:
- /git-cherry-pick abc123
- /git-cherry-pick abc123 --with-deps
- /git-cherry-pick abc123 --no-conflict"""

        commit = args[0]
        options = args[1:] if len(args) > 1 else []

        try:
            # Check for dependencies if requested
            if "--with-deps" in options:
                deps = await self._find_commit_dependencies(context, commit)
                if deps:
                    dep_list = " ".join(deps)
                    return f"""Found dependencies for {commit}:

Dependent commits:
{chr(10).join([f"  • {dep}" for dep in deps])}

To cherry-pick with dependencies:
git cherry-pick {dep_list} {commit}

Or pick individually:
{chr(10).join([f"git cherry-pick {dep}" for dep in deps + [commit]])}
"""

            # Check for conflicts if requested
            if "--no-conflict" in options:
                conflict_check = await self._check_cherry_pick_conflicts(context, commit)
                if conflict_check:
                    return f"""⚠️  Potential conflicts detected for {commit}:

{conflict_check}

Recommendations:
1. Resolve conflicts manually after cherry-picking
2. Consider merging instead
3. Create a new branch for cherry-picking
"""

            # Provide cherry-pick guidance
            return f"""Cherry-pick guidance for commit {commit}:

Commit details:
{await self._get_commit_details(context, commit)}

Cherry-pick command:
git cherry-pick {commit}

If conflicts occur:
1. git status to see conflicts
2. Resolve conflicts in affected files
3. git add <resolved-files>
4. git cherry-pick --continue
5. Or git cherry-pick --abort to cancel

To cherry-pick without committing:
git cherry-pick --no-commit {commit}

To cherry-pick multiple commits:
git cherry-pick <start>..<end>
"""

        except Exception as e:
            return f"Error with cherry-pick: {e}"

    async def _find_commit_dependencies(
        self, context: CommandContext, commit: str
    ) -> List[str]:
        """Find commits that depend on the given commit."""
        try:
            # Get commit hash (handle short hashes)
            full_hash = subprocess.run(
                ["git", "rev-parse", commit],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if full_hash.returncode != 0:
                return []

            # Find commits that reference this commit
            find_refs = subprocess.run(
                ["git", "log", "--grep", full_hash.stdout.strip(), "--oneline"],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if find_refs.returncode != 0:
                return []

            refs = []
            for line in find_refs.stdout.strip().split('\n'):
                if line:
                    hash_val = line.split()[0]
                    if hash_val != full_hash.stdout.strip():
                        refs.append(hash_val)

            return refs[:5]  # Limit to 5 most recent

        except Exception:
            return []

    async def _check_cherry_pick_conflicts(
        self, context: CommandContext, commit: str
    ) -> str:
        """Check for potential cherry-pick conflicts."""
        try:
            # Simulate cherry-pick to check conflicts
            # Create temporary branch
            temp_branch = f"temp-cherry-{commit[:8]}"
            subprocess.run(
                ["git", "checkout", "-b", temp_branch],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            # Try cherry-pick with --no-commit
            result = subprocess.run(
                ["git", "cherry-pick", "--no-commit", commit],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            # Check for conflicts
            conflicts = ""
            if result.returncode != 0:
                conflicts = result.stderr

            # Clean up
            subprocess.run(["git", "reset", "--hard"], capture_output=True)
            subprocess.run(["git", "checkout", "-"], capture_output=True)
            subprocess.run(["git", "branch", "-D", temp_branch], capture_output=True)

            return conflicts if conflicts else "No conflicts detected"

        except Exception as e:
            return f"Could not check for conflicts: {e}"

    async def _get_commit_details(self, context: CommandContext, commit: str) -> str:
        """Get detailed information about a commit."""
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--format=fuller", commit],
                capture_output=True,
                text=True,
                cwd=context.working_directory
            )

            if result.returncode == 0:
                # Limit output to first 20 lines
                lines = result.stdout.split('\n')[:20]
                return '\n'.join(lines)

            return "Could not retrieve commit details"

        except Exception:
            return "Could not retrieve commit details"

    def requires_git_repo(self) -> bool:
        return True

    def get_min_args(self) -> int:
        return 1


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(GitBisectCommand())
command_registry.register(GitRebaseCommand())
command_registry.register(GitCherryPickCommand())

def register():
    """Register all advanced Git commands."""
    return [
        GitBisectCommand(),
        GitRebaseCommand(),
        GitCherryPickCommand(),
    ]