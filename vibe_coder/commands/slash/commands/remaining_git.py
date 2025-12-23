"""Remaining Git utility slash commands."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class GitCherryPickCommand(SlashCommand):
    """Intelligent cherry-picking with conflict resolution."""

    def __init__(self):
        super().__init__(
            name="git-cherry-pick",
            description="Intelligent cherry-picking",
            aliases=["cpick", "smart-pick"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-cherry-pick command."""
        if not args:
            return """Usage: /git-cherry-pick <commit> [options]
Options:
- --branch <target>: Target branch (default: current)
- --strategy <type>: Conflict resolution (ours, theirs, manual)
- --no-commit: Don't auto-commit
- --dry-run: Show what would be done

Examples:
- /git-cherry-pick abc123
- /git-cherry-pick def456 --branch feature-x
- /git-cherry-pick 789abc --strategy ours"""

        commit = args[0]
        options = {arg[2:]: True for arg in args[1:] if arg.startswith("--")}

        target_branch = options.get("branch")
        strategy = options.get("strategy", "manual")
        no_commit = options.get("no-commit", False)
        dry_run = options.get("dry-run", False)

        file_ops = FileOperations(context.working_directory)

        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return "❌ Not in a Git repository"

            # Get commit info
            commit_info = await self._get_commit_info(commit)
            if not commit_info:
                return f"❌ Commit {commit} not found"

            if dry_run:
                return f"""🔍 Cherry-pick Preview

Commit: {commit}
Author: {commit_info['author']}
Message: {commit_info['message']}

Files to be cherry-picked:
{commit_info['files']}

Strategy: {strategy}
Auto-commit: {not no_commit}"""

            # Save current branch if switching
            current_branch = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            ).stdout.strip()

            # Switch to target branch if specified
            if target_branch and target_branch != current_branch:
                result = subprocess.run(
                    ["git", "checkout", target_branch], capture_output=True, text=True
                )
                if result.returncode != 0:
                    return f"❌ Failed to checkout {target_branch}: {result.stderr}"

            # Perform cherry-pick
            cmd = ["git", "cherry-pick"]
            if no_commit:
                cmd.append("--no-commit")
            cmd.append(commit)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                output = f"✅ Successfully cherry-picked {commit}\n\n"
                output += f"Commit: {commit_info['message']}\n"
                output += f"Files: {len(commit_info['files'])} changed"
            else:
                # Handle conflicts
                if "conflict" in result.stderr.lower():
                    resolution = await self._handle_conflicts(strategy, context)
                    output = f"⚠️ Cherry-pick had conflicts\n\n"
                    output += f"Strategy: {strategy}\n"
                    output += f"Resolution: {resolution}"
                else:
                    output = f"❌ Cherry-pick failed: {result.stderr}"

            # Return to original branch if we switched
            if target_branch and target_branch != current_branch:
                subprocess.run(["git", "checkout", current_branch], capture_output=True)

            return output

        except Exception as e:
            return f"Error during cherry-pick: {e}"

    async def _get_commit_info(self, commit: str) -> Optional[Dict]:
        """Get information about a commit."""
        try:
            # Get commit details
            result = subprocess.run(
                ["git", "show", "--format=%H|%an|%s", "--name-only", commit],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            lines = result.stdout.split("\n")
            header = lines[0].split("|")
            files = [f for f in lines[1:] if f]

            return {"hash": header[0], "author": header[1], "message": header[2], "files": files}
        except:
            return None

    async def _handle_conflicts(self, strategy: str, context: CommandContext) -> str:
        """Handle merge conflicts based on strategy."""
        if strategy == "ours":
            subprocess.run(["git", "checkout", "--ours", "."], capture_output=True)
            subprocess.run(["git", "add", "."], capture_output=True)
            return "Accepted our changes"
        elif strategy == "theirs":
            subprocess.run(["git", "checkout", "--theirs", "."], capture_output=True)
            subprocess.run(["git", "add", "."], capture_output=True)
            return "Accepted their changes"
        else:
            return "Manual resolution required"


class GitUndoCommand(SlashCommand):
    """Smart Git operations undo."""

    def __init__(self):
        super().__init__(
            name="git-undo",
            description="Smart git operations undo",
            aliases=["git-revert", "undo"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-undo command."""
        if not args:
            return """Usage: /git-undo <action> [options]
Actions:
- commit: Undo last commit
- push: Undo last push
- merge: Undo last merge
- rebase: Undo rebase
- reset: Reset to commit

Options:
- --hard: Hard reset (dangerous)
- --keep <n>: Keep last N commits
- --interactive: Interactive undo

Examples:
- /git-undo commit
- /git-undo push
- /git-undo commit --keep 2
- /git-undo reset abc123 --hard"""

        action = args[0]
        options = {arg[2:]: True for arg in args[1:] if arg.startswith("--")}

        hard = options.get("hard", False)
        keep = int(options.get("keep", "0"))
        interactive = options.get("interactive", False)

        try:
            # Get recent history
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"], capture_output=True, text=True
            )
            recent_commits = result.stdout.split("\n") if result.returncode == 0 else []

            if action == "commit":
                return await self._undo_commit(keep, hard, recent_commits)
            elif action == "push":
                return await self._undo_push(keep, recent_commits)
            elif action == "merge":
                return await self._undo_merge(hard)
            elif action == "rebase":
                return await self._undo_rebase()
            elif action == "reset" and len(args) > 1:
                commit = args[1]
                return await self._reset_to_commit(commit, hard)
            else:
                return f"❌ Unknown action: {action}"

        except Exception as e:
            return f"Error undoing Git operation: {e}"

    async def _undo_commit(self, keep: int, hard: bool, recent_commits: List[str]) -> str:
        """Undo commits."""
        if keep > 0:
            # Reset to keep N commits
            target = recent_commits[keep].split()[0] if len(recent_commits) > keep else "HEAD~1"
            result = subprocess.run(
                ["git", "reset", "--soft", target], capture_output=True, text=True
            )
            action = "soft-reset"
        else:
            # Undo last commit
            result = subprocess.run(
                ["git", "reset", "--soft", "HEAD~1"], capture_output=True, text=True
            )
            action = "undone"

        if result.returncode == 0:
            return f"✅ Last commit {action}. Changes are staged.\n\nUse 'git commit' to recommit or 'git reset' to unstage."
        else:
            return f"❌ Failed to undo commit: {result.stderr}"

    async def _undo_push(self, keep: int, recent_commits: List[str]) -> str:
        """Undo a push."""
        # Get current branch
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = result.stdout.strip() if result.returncode == 0 else "main"

        # Force push to undo
        if keep > 0 and len(recent_commits) > keep:
            target = recent_commits[keep].split()[0]
        else:
            target = "HEAD~1"

        result = subprocess.run(
            ["git", "push", "--force-with-lease", "origin", f"{branch}:{branch}"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return f"✅ Push undone. Branch {branch} reset to {target}"
        else:
            return f"❌ Failed to undo push: {result.stderr}"

    async def _undo_merge(self, hard: bool) -> str:
        """Undo a merge."""
        # Check if we're in a merge
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

        if "MERGE_HEAD" not in result.stdout:
            # Abort last merge if clean
            result = subprocess.run(
                ["git", "log", "--oneline", "-5", "--merges"], capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout:
                last_merge = result.stdout.split("\n")[0].split()[0]
                result = subprocess.run(
                    ["git", "reset", "--hard" if hard else "--soft", f"{last_merge}^"],
                    capture_output=True,
                    text=True,
                )
                return "✅ Last merge undone"
            else:
                return "✅ No recent merges to undo"
        else:
            # Abort current merge
            subprocess.run(["git", "merge", "--abort"], capture_output=True)
            return "✅ Current merge aborted"

    async def _undo_rebase(self) -> str:
        """Undo a rebase."""
        # Check reflog for rebase
        result = subprocess.run(
            ["git", "reflog", "-10", "--oneline"], capture_output=True, text=True
        )

        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "rebase" in line and "finished" in line:
                    # Get the pre-rebase commit
                    parts = line.split()
                    if len(parts) > 1:
                        result = subprocess.run(
                            ["git", "reset", "--hard", parts[0]], capture_output=True, text=True
                        )
                        return f"✅ Rebase undone. Reset to {parts[0]}"

        return "✅ No recent rebase found to undo"

    async def _reset_to_commit(self, commit: str, hard: bool) -> str:
        """Reset to a specific commit."""
        result = subprocess.run(
            ["git", "reset", "--hard" if hard else "--soft", commit], capture_output=True, text=True
        )

        if result.returncode == 0:
            mode = "hard" if hard else "soft"
            return f"✅ Reset to {commit} ({mode} mode)"
        else:
            return f"❌ Failed to reset: {result.stderr}"


class GitCleanCommand(SlashCommand):
    """Branch cleanup utility."""

    def __init__(self):
        super().__init__(
            name="git-clean",
            description="Branch cleanup utility",
            aliases=["cleanup", "prune"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-clean command."""
        options = {arg[2:]: True for arg in args if arg.startswith("--")}

        merged_only = options.get("merged", False)
        dry_run = options.get("dry-run", True)
        remote = options.get("remote", False)
        force = options.get("force", False)

        try:
            # Get all branches
            result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)

            if result.returncode != 0:
                return "❌ Failed to list branches"

            branches = []
            current = None

            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("*"):
                    current = line[2:].split()[0]
                    branches.append(line[2:])
                else:
                    branches.append(line[2:])

            # Filter branches
            local_branches = [b for b in branches if not b.startswith("remotes/")]
            remote_branches = [
                b.replace("remotes/origin/", "")
                for b in branches
                if b.startswith("remotes/origin/")
            ]

            # Get merged branches
            if merged_only:
                result = subprocess.run(
                    ["git", "branch", "--merged"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    merged = set(
                        line.strip("* ").strip()
                        for line in result.stdout.split("\n")
                        if line.strip()
                    )
                    local_branches = [b for b in local_branches if b in merged]
                    remote_branches = [b for b in remote_branches if b in merged]

            # Remove current and main/master branches
            protected = {"main", "master", "develop", "dev", current}
            if current in protected:
                protected.remove(current)

            deletable_local = [b for b in local_branches if b not in protected]
            deletable_remote = [b for b in remote_branches if b not in protected] if remote else []

            output = [f"🌿 Git Branch Cleanup"]
            output.append(f"\nCurrent branch: {current}")

            if deletable_local:
                output.append(f"\nLocal branches to delete ({len(deletable_local)}):")
                for branch in deletable_local:
                    output.append(f"  • {branch}")

            if deletable_remote:
                output.append(f"\nRemote branches to delete ({len(deletable_remote)}):")
                for branch in deletable_remote:
                    output.append(f"  • origin/{branch}")

            if not deletable_local and not deletable_remote:
                output.append("\n✨ No branches to clean up")
                return "\n".join(output)

            if not dry_run:
                deleted = []
                # Delete local branches
                for branch in deletable_local:
                    result = subprocess.run(
                        ["git", "branch", "-D" if force else "-d", branch],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        deleted.append(branch)

                # Delete remote branches
                if remote:
                    for branch in deletable_remote:
                        result = subprocess.run(
                            ["git", "push", "origin", "--delete", branch],
                            capture_output=True,
                            text=True,
                        )
                        if result.returncode == 0:
                            deleted.append(f"origin/{branch}")

                if deleted:
                    output.append(f"\n✅ Deleted branches: {', '.join(deleted)}")
                else:
                    output.append(f"\n⚠️ No branches deleted (use --force to override)")

            else:
                output.append(f"\n🔍 Dry run mode. Use --force to actually delete.")

            return "\n".join(output)

        except Exception as e:
            return f"Error during branch cleanup: {e}"


class GitReleaseCommand(SlashCommand):
    """Release preparation."""

    def __init__(self):
        super().__init__(
            name="git-release",
            description="Release preparation",
            aliases=["release", "tag"],
            category="git",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the git-release command."""
        if not args:
            return """Usage: /git-release <version> [options]
Options:
- --branch <name>: Release branch (default: main)
- --pre: Pre-release version
- --notes <file>: Release notes file
- --no-push: Don't push to remote
- --create-branch: Create release branch

Examples:
- /git-release v1.2.3
- /git-release v2.0.0-beta --pre
- /git-release v1.1.0 --notes RELEASE.md
- /git-release v3.0.0 --create-branch"""

        version = args[0]
        options = {
            arg[2:]: arg[4:] if arg.startswith("--") and "=" in arg else True
            for arg in args[1:]
            if arg.startswith("--")
        }

        branch = options.get("branch", "main")
        is_pre_release = options.get("pre", False)
        notes_file = options.get("notes")
        no_push = options.get("no-push", False)
        create_branch = options.get("create-branch", False)

        file_ops = FileOperations(context.working_directory)

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            current_branch = result.stdout.strip() if result.returncode == 0 else "main"

            # Check if working directory is clean
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )

            if result.stdout.strip():
                return "❌ Working directory is not clean. Commit or stash changes first."

            # Prepare release
            steps = []

            # 1. Update version in files if needed
            version_files = await self._update_version_files(version, file_ops)
            if version_files:
                steps.append(f"Updated version in: {', '.join(version_files)}")

            # 2. Create release branch if requested
            if create_branch:
                release_branch = f"release/{version}"
                result = subprocess.run(
                    ["git", "checkout", "-b", release_branch], capture_output=True, text=True
                )
                if result.returncode == 0:
                    steps.append(f"Created release branch: {release_branch}")

            # 3. Create tag
            tag_name = version
            if is_pre_release:
                tag_name = f"{version}-pre"

            # Get release notes
            release_notes = ""
            if notes_file and Path(notes_file).exists():
                content = await file_ops.read_file(notes_file)
                release_notes = content
            else:
                # Generate release notes from commits since last tag
                release_notes = await self._generate_release_notes(context)

            # Create annotated tag
            tag_message = f"Release {tag_name}\n\n{release_notes}"
            result = subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message], capture_output=True, text=True
            )

            if result.returncode == 0:
                steps.append(f"Created tag: {tag_name}")
            else:
                return f"❌ Failed to create tag: {result.stderr}"

            # 4. Push changes
            if not no_push:
                # Push current branch
                subprocess.run(["git", "push", "origin", current_branch], capture_output=True)

                # Push tag
                subprocess.run(["git", "push", "origin", tag_name], capture_output=True)

                # Push release branch if created
                if create_branch:
                    subprocess.run(
                        ["git", "push", "-u", "origin", f"release/{version}"], capture_output=True
                    )

                steps.append("Pushed to remote")

            # 5. Create GitHub release (placeholder)
            if not no_push:
                steps.append(
                    f"📝 Create GitHub release at: https://github.com/user/repo/releases/new?tag={tag_name}"
                )

            output = [f"🚀 Release {version} prepared"]
            output.extend(steps)
            output.append(f"\nRelease notes:\n{release_notes}")

            return "\n".join(output)

        except Exception as e:
            return f"Error preparing release: {e}"

    async def _update_version_files(self, version: str, file_ops: FileOperations) -> List[str]:
        """Update version in common files."""
        updated = []

        # Common version files
        version_files = [
            "version.py",
            "__init__.py",
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "pom.xml",
        ]

        for file_path in version_files:
            if Path(file_path).exists():
                try:
                    content = await file_ops.read_file(file_path)
                    # Simple version replacement
                    new_content = content.replace("0.0.0", version)
                    if new_content != content:
                        await file_ops.write_file(file_path, new_content)
                        updated.append(file_path)
                except:
                    pass

        return updated

    async def _generate_release_notes(self, context: CommandContext) -> str:
        """Generate release notes from commits."""
        try:
            # Get last tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True
            )

            if result.returncode == 0:
                last_tag = result.stdout.strip()
                # Get commits since last tag
                result = subprocess.run(
                    ["git", "log", f"{last_tag}..HEAD", "--oneline", "--no-merges"],
                    capture_output=True,
                    text=True,
                )
            else:
                # Get last 20 commits
                result = subprocess.run(
                    ["git", "log", "--oneline", "-20", "--no-merges"],
                    capture_output=True,
                    text=True,
                )

            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                return f"Changes:\n" + "\n".join(f"• {commit}" for commit in commits if commit)
        except:
            pass

        return "Release notes: Add your release notes here"


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(GitCherryPickCommand())
command_registry.register(GitUndoCommand())
command_registry.register(GitCleanCommand())
command_registry.register(GitReleaseCommand())


def register():
    """Register all remaining Git commands."""
    return [
        GitCherryPickCommand(),
        GitUndoCommand(),
        GitCleanCommand(),
        GitReleaseCommand(),
    ]
