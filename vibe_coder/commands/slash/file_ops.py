"""File operations utilities for slash commands."""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class FileOperations:
    """Handle file reading, writing, and analysis operations."""

    def __init__(self, working_directory: str = "."):
        self.working_directory = Path(working_directory).resolve()
        self.backup_dir = self.working_directory / ".vibe" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_absolute_path(self, filepath: str) -> Path:
        """Get absolute path from relative path."""
        if os.path.isabs(filepath):
            return Path(filepath).resolve()
        return (self.working_directory / filepath).resolve()

    def detect_language(self, filepath: str) -> str:
        """Detect the programming language of a file based on its extension."""
        path = self.get_absolute_path(filepath)
        return self._detect_file_type(path)

    async def read_file(self, filepath: str) -> str:
        """Read file content with error handling."""
        try:
            path = self.get_absolute_path(filepath)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {filepath}")
        except UnicodeDecodeError:
            raise UnicodeDecodeError(f"File is not text or uses unknown encoding: {filepath}")

    async def write_file(
        self, filepath: str, content: str, backup: bool = True, create_dirs: bool = True
    ) -> bool:
        """
        Write content to file with optional backup.
        Returns True if successful, False otherwise.
        """
        try:
            path = self.get_absolute_path(filepath)

            # Create backup if file exists and backup is requested
            if backup and path.exists():
                self._create_backup(path)

            # Create directories if they don't exist
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except PermissionError:
            raise PermissionError(f"Permission denied writing to file: {filepath}")
        except Exception as e:
            raise Exception(f"Error writing file {filepath}: {str(e)}")

    def _create_backup(self, path: Path) -> str:
        """Create a backup of the file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        backup_name = f"{path.name}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(path, backup_path)
        return str(backup_path)

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze file structure and properties."""
        path = self.get_absolute_path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        stat = path.stat()

        # Basic file info
        analysis = {
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "extension": path.suffix.lower() if path.suffix else None,
        }

        # File type detection
        analysis["file_type"] = self._detect_file_type(path)

        # If it's a text file, add content analysis
        if path.is_file() and self._is_text_file(path):
            try:
                content = path.read_text(encoding="utf-8")
                analysis.update(
                    {
                        "line_count": len(content.splitlines()),
                        "char_count": len(content),
                        "encoding": "utf-8",
                        "hash": hashlib.md5(content.encode()).hexdigest(),
                    }
                )

                # Language-specific analysis
                if analysis["file_type"] in ["python", "javascript", "typescript", "java"]:
                    analysis.update(self._analyze_code_file(content, analysis["file_type"]))

            except UnicodeDecodeError:
                analysis["encoding"] = "binary"
        else:
            analysis["encoding"] = "binary"

        return analysis

    def _detect_file_type(self, path: Path) -> str:
        """Detect file type based on extension and content."""
        ext = path.suffix.lower()

        # Language mappings
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".sql": "sql",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            ".md": "markdown",
            ".markdown": "markdown",
            ".txt": "text",
            ".csv": "csv",
            ".tsv": "tsv",
            ".pdf": "pdf",
            ".doc": "word",
            ".docx": "word",
            ".xls": "excel",
            ".xlsx": "excel",
            ".ppt": "powerpoint",
            ".pptx": "powerpoint",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".gif": "image",
            ".svg": "image",
            ".ico": "image",
            ".mp3": "audio",
            ".mp4": "video",
            ".zip": "archive",
            ".tar": "archive",
            ".gz": "archive",
            ".rar": "archive",
        }

        return language_map.get(ext, "unknown")

    def _is_text_file(self, path: Path) -> bool:
        """Check if file is likely a text file."""
        # Simple heuristic based on extension
        text_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".r",
            ".sql",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".html",
            ".htm",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".md",
            ".markdown",
            ".txt",
            ".csv",
            ".tsv",
            ".log",
            ".gitignore",
            ".dockerfile",
        }

        return path.suffix.lower() in text_extensions

    def _analyze_code_file(self, content: str, language: str) -> Dict[str, Any]:
        """Analyze code file content."""
        lines = content.splitlines()
        analysis = {}

        if language == "python":
            analysis.update(self._analyze_python_code(content, lines))
        elif language in ["javascript", "typescript"]:
            analysis.update(self._analyze_javascript_code(content, lines))
        elif language == "java":
            analysis.update(self._analyze_java_code(content, lines))
        elif language == "cpp" or language == "c":
            analysis.update(self._analyze_cpp_code(content, lines))

        return analysis

    def _analyze_python_code(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze Python code."""
        analysis = {
            "classes": 0,
            "functions": 0,
            "imports": 0,
            "comments": 0,
            "docstrings": 0,
        }

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                analysis["classes"] += 1
            elif stripped.startswith("def "):
                analysis["functions"] += 1
            elif stripped.startswith(("import ", "from ")):
                analysis["imports"] += 1
            elif stripped.startswith("#"):
                analysis["comments"] += 1
            elif '"""' in line or "'''" in line:
                analysis["docstrings"] += 1

        return analysis

    def _analyze_javascript_code(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code."""
        analysis = {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "exports": 0,
            "comments": 0,
        }

        for line in lines:
            stripped = line.strip()
            if "function " in stripped or "=>" in stripped:
                analysis["functions"] += 1
            if "class " in stripped:
                analysis["classes"] += 1
            if stripped.startswith("import "):
                analysis["imports"] += 1
            if "export " in stripped:
                analysis["exports"] += 1
            if stripped.startswith("//") or "/*" in stripped:
                analysis["comments"] += 1

        return analysis

    def _analyze_java_code(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze Java code."""
        analysis = {
            "classes": 0,
            "methods": 0,
            "imports": 0,
            "comments": 0,
        }

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                analysis["classes"] += 1
            elif any(
                stripped.startswith(f"{mod} ")
                for mod in ["public", "private", "protected", "static"]
            ):
                analysis["methods"] += 1
            elif stripped.startswith("import "):
                analysis["imports"] += 1
            elif stripped.startswith("//") or "/*" in stripped:
                analysis["comments"] += 1

        return analysis

    def _analyze_cpp_code(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze C/C++ code."""
        analysis = {
            "functions": 0,
            "classes": 0,
            "includes": 0,
            "comments": 0,
        }

        for line in lines:
            stripped = line.strip()
            if "class " in stripped:
                analysis["classes"] += 1
            elif "(" in stripped and ")" in stripped and "{" in stripped:
                analysis["functions"] += 1
            elif stripped.startswith("#include"):
                analysis["includes"] += 1
            elif stripped.startswith("//") or "/*" in stripped:
                analysis["comments"] += 1

        return analysis

    def list_files(
        self,
        directory: str = ".",
        pattern: str = "*",
        recursive: bool = False,
        include_hidden: bool = False,
    ) -> List[str]:
        """List files in directory with optional filtering."""
        path = self.get_absolute_path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        files = []

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # Filter out hidden files if not included
        if not include_hidden:
            files = [f for f in files if not f.name.startswith(".")]

        # Convert to relative paths
        return [str(f.relative_to(self.working_directory)) for f in files if f.is_file()]

    def get_file_tree(self, directory: str = ".", max_depth: int = 3) -> Dict[str, Any]:
        """Generate hierarchical file tree."""
        path = self.get_absolute_path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        def build_tree(current_path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {"type": "directory", "name": current_path.name, "truncated": True}

            tree = {
                "type": "directory",
                "name": current_path.name,
                "path": str(current_path.relative_to(self.working_directory)),
                "children": [],
            }

            try:
                for item in sorted(current_path.iterdir()):
                    if item.name.startswith("."):
                        continue  # Skip hidden files

                    if item.is_file():
                        tree["children"].append(
                            {
                                "type": "file",
                                "name": item.name,
                                "size": item.stat().st_size,
                                "extension": item.suffix.lower() if item.suffix else None,
                            }
                        )
                    elif item.is_dir():
                        tree["children"].append(build_tree(item, current_depth + 1))
            except PermissionError:
                tree["children"].append(
                    {
                        "type": "error",
                        "name": "Permission denied",
                        "message": f"Cannot access {current_path}",
                    }
                )

            return tree

        return build_tree(path)