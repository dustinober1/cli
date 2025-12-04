"""Git integration for slash commands."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class GitOperations:
    """Handle Git repository operations and analysis."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.git_dir = None

    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            self.git_dir = Path(result.stdout.strip())
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_git_info(self) -> Dict[str, any]:
        """Get comprehensive Git repository information."""
        if not self.is_git_repo():
            return {}

        info = {
            "repo_path": str(self.repo_path),
            "git_dir": str(self.git_dir) if self.git_dir else None,
        }

        # Get current branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            info["current_branch"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            info["current_branch"] = None

        # Get remote information
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            remotes = {}
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    name = parts[0]
                    url = parts[1].split(" ")[0]
                    remotes[name] = url
            info["remotes"] = remotes
        except subprocess.CalledProcessError:
            info["remotes"] = {}

        # Get last commit info
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%an|%ae|%ad|%s", "--date=iso"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            parts = result.stdout.strip().split("|")
            if len(parts) >= 5:
                info["last_commit"] = {
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4],
                }
        except subprocess.CalledProcessError:
            info["last_commit"] = {}

        return info

    async def get_status(self) -> Dict[str, any]:
        """Get detailed git status with AI-friendly formatting."""
        if not self.is_git_repo():
            return {"error": "Not a Git repository"}

        try:
            # Get porcelain status
            result = subprocess.run(
                ["git", "status", "--porcelain=v2", "--branch"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            lines = result.stdout.strip().split("\n")
            status = {
                "branch": "unknown",
                "ahead": 0,
                "behind": 0,
                "staged": [],
                "modified": [],
                "untracked": [],
                "renamed": [],
                "deleted": [],
                "conflicts": [],
            }

            for line in lines:
                if line.startswith("# branch.oid "):
                    status["commit"] = line.split(" ")[2]
                elif line.startswith("# branch.head "):
                    status["branch"] = line.split(" ")[2]
                elif line.startswith("# branch.ab "):
                    parts = line.split(" ")
                    if len(parts) >= 4:
                        status["ahead"] = int(parts[2][1:])
                        status["behind"] = int(parts[3][1:])
                elif line and not line.startswith("#"):
                    parts = line.split(" ")
                    if len(parts) >= 3:
                        change_type = parts[1]
                        file_path = parts[2]

                        if change_type == "M" and parts[0] == "1":
                            status["modified"].append(file_path)
                        elif change_type == "A" and parts[0] == "1":
                            status["staged"].append(file_path)
                        elif change_type == "D" and parts[0] == "1":
                            status["deleted"].append(file_path)
                        elif change_type == "??":
                            status["untracked"].append(file_path)
                        elif change_type == "R":
                            status["renamed"].append(
                                f"{file_path} -> {parts[3] if len(parts) > 3 else 'unknown'}"
                            )
                        elif change_type == "U" or "U" in parts[0]:
                            status["conflicts"].append(file_path)

            return status

        except subprocess.CalledProcessError as e:
            return {"error": f"Git status failed: {e.stderr}"}

    async def get_diff(self, filepath: Optional[str] = None, staged: bool = False) -> str:
        """Get git diff for specified file or all changes."""
        if not self.is_git_repo():
            return "Not a Git repository"

        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if filepath:
                cmd.append(filepath)

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            return result.stdout

        except subprocess.CalledProcessError as e:
            return f"Git diff failed: {e.stderr}"

    async def get_log(
        self, max_count: int = 10, filepath: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get commit history."""
        if not self.is_git_repo():
            return []

        try:
            cmd = ["git", "log", f"-{max_count}", "--format=%H|%an|%ad|%s", "--date=iso"]
            if filepath:
                cmd.append("--")
                cmd.append(filepath)

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        commits.append(
                            {
                                "hash": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3],
                            }
                        )

            return commits

        except subprocess.CalledProcessError:
            return []

    async def add_file(self, filepath: str) -> bool:
        """Add file to staging area."""
        if not self.is_git_repo():
            return False

        try:
            subprocess.run(
                ["git", "add", filepath], cwd=self.repo_path, check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    async def commit(self, message: str) -> bool:
        """Create a commit with the given message."""
        if not self.is_git_repo():
            return False

        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    async def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """Create and optionally checkout a new branch."""
        if not self.is_git_repo():
            return False

        try:
            if checkout:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["git", "branch", branch_name],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                )
            return True
        except subprocess.CalledProcessError:
            return False

    async def checkout_branch(self, branch_name: str) -> bool:
        """Checkout an existing branch."""
        if not self.is_git_repo():
            return False

        try:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    async def get_branches(self) -> Dict[str, List[str]]:
        """Get all local and remote branches."""
        if not self.is_git_repo():
            return {"local": [], "remote": []}

        try:
            # Get local branches
            result = subprocess.run(
                ["git", "branch", "--format='%(refname:short)'"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            local_branches = [
                b.strip("'") for b in result.stdout.strip().split("\n") if b.strip("'")
            ]

            # Get remote branches
            result = subprocess.run(
                ["git", "branch", "-r", "--format='%(refname:short)'"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            remote_branches = [
                b.strip("'") for b in result.stdout.strip().split("\n") if b.strip("'")
            ]

            return {"local": local_branches, "remote": remote_branches}

        except subprocess.CalledProcessError:
            return {"local": [], "remote": []}

    async def get_file_blame(self, filepath: str) -> List[Dict[str, str]]:
        """Get blame information for a file."""
        if not self.is_git_repo():
            return []

        try:
            result = subprocess.run(
                ["git", "blame", "--line-porcelain", filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            blame_info = []
            current_commit = {}

            for line in result.stdout.split("\n"):
                if line.startswith("\t"):
                    # This is a code line
                    if current_commit:
                        blame_info.append(
                            {
                                "commit": current_commit.get("hash", ""),
                                "author": current_commit.get("author", ""),
                                "date": current_commit.get("date", ""),
                                "line": line[1:],  # Remove the tab
                            }
                        )
                        current_commit = {}
                else:
                    # Parse blame metadata
                    if line.startswith("author "):
                        current_commit["author"] = line[7:]
                    elif line.startswith("author-mail "):
                        current_commit["email"] = line[12:]
                    elif line.startswith("author-time "):
                        current_commit["timestamp"] = line[12:]
                    elif line.startswith("author-tz "):
                        current_commit["timezone"] = line[10:]
                    elif line.startswith("summary "):
                        current_commit["summary"] = line[8:]
                    elif not line.startswith("filename ") and " " in line:
                        # Likely the commit hash and other metadata
                        parts = line.split(" ")
                        if parts[0].startswith("0"):  # Commit hash
                            current_commit["hash"] = parts[0]

            return blame_info

        except subprocess.CalledProcessError:
            return []

    def get_ignore_patterns(self) -> List[str]:
        """Get .gitignore patterns."""
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            return []

        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                return [
                    line.strip()
                    for line in f.readlines()
                    if line.strip() and not line.startswith("#")
                ]
        except Exception:
            return []

    def is_ignored(self, filepath: str) -> bool:
        """Check if a file is ignored by Git."""
        if not self.is_git_repo():
            return False

        try:
            result = subprocess.run(
                ["git", "check-ignore", filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    async def get_changed_files(self, since_commit: Optional[str] = None) -> List[str]:
        """Get list of changed files since a commit or in working directory."""
        if not self.is_git_repo():
            return []

        try:
            cmd = ["git", "diff", "--name-only"]
            if since_commit:
                cmd.append(since_commit)

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            return [f.strip() for f in result.stdout.split("\n") if f.strip()]

        except subprocess.CalledProcessError:
            return []

    async def generate_commit_message(self, changes: str) -> str:
        """
        Generate a conventional commit message using AI.
        This is a placeholder that would integrate with the AI client.
        """
        # This would typically call the AI client with the changes
        # For now, return a basic commit message
        return "Update files"
