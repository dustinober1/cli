"""Project analysis tools for slash commands."""

import ast
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict, Counter


class ProjectAnalyzer:
    """Analyze project structure and dependencies."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.file_cache = {}
        self.import_graph = defaultdict(set)
        self.language_stats = Counter()

    async def scan_project(self) -> Dict[str, Any]:
        """Comprehensive project analysis."""
        analysis = {
            "project_name": self.root_path.name,
            "root_path": str(self.root_path),
            "scan_timestamp": "",
            "file_count": 0,
            "directory_count": 0,
            "languages": {},
            "file_types": Counter(),
            "dependencies": {},
            "structure": {},
            "code_metrics": {},
            "potential_issues": [],
            "recommendations": []
        }

        from datetime import datetime
        analysis["scan_timestamp"] = datetime.now().isoformat()

        # Scan file structure
        all_files = []
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                all_files.append(file_path)
                analysis["file_count"] += 1
                file_ext = file_path.suffix.lower()
                analysis["file_types"][file_ext] += 1

        # Count directories
        analysis["directory_count"] = len(set(f.parent for f in all_files))

        # Detect languages and analyze code files
        for file_path in all_files:
            language = self._detect_language(file_path)
            if language:
                analysis["languages"][language] = analysis["languages"].get(language, 0) + 1

            # Analyze code files
            if self._is_code_file(file_path):
                try:
                    await self._analyze_code_file(file_path)
                except Exception as e:
                    analysis["potential_issues"].append(f"Could not analyze {file_path}: {str(e)}")

        # Build dependency graph
        analysis["dependencies"] = self._build_dependency_graph()

        # Analyze project structure
        analysis["structure"] = self._analyze_project_structure()

        # Calculate code metrics
        analysis["code_metrics"] = self._calculate_code_metrics()

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def get_file_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        """Generate hierarchical file tree."""
        def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {
                    "name": path.name,
                    "type": "directory",
                    "truncated": True
                }

            node = {
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "path": str(path.relative_to(self.root_path))
            }

            if path.is_file():
                node["size"] = path.stat().st_size
                node["extension"] = path.suffix.lower()
                node["language"] = self._detect_language(path)

            elif path.is_dir():
                node["children"] = []
                try:
                    for item in sorted(path.iterdir()):
                        if not self._should_ignore_file(item):
                            node["children"].append(build_tree(item, current_depth + 1))
                except PermissionError:
                    node["children"] = [{
                        "name": "Permission denied",
                        "type": "error"
                    }]

            return node

        return build_tree(self.root_path)

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """Analyze import dependencies across project."""
        dependencies = defaultdict(list)

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and self._is_code_file(file_path):
                file_deps = self._extract_dependencies(file_path)
                relative_path = str(file_path.relative_to(self.root_path))
                dependencies[relative_path] = file_deps

        return dict(dependencies)

    def detect_languages(self) -> Dict[str, float]:
        """Detect programming languages and their usage percentages."""
        language_files = defaultdict(int)
        total_files = 0

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                language = self._detect_language(file_path)
                if language:
                    language_files[language] += 1
                    total_files += 1

        if total_files == 0:
            return {}

        # Convert to percentages
        return {lang: (count / total_files) * 100 for lang, count in language_files.items()}

    def _should_ignore_file(self, path: Path) -> bool:
        """Check if file should be ignored during analysis."""
        # Common ignore patterns
        ignore_patterns = {
            ".git", ".svn", ".hg",
            "__pycache__", ".pytest_cache", ".tox",
            "node_modules", ".npm", ".yarn",
            ".vscode", ".idea", ".DS_Store",
            "*.pyc", "*.pyo", "*.pyd",
            "*.so", "*.dylib", "*.dll",
            "*.exe", "*.bin",
            "*.log", "*.tmp"
        }

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str or path.match(pattern):
                return True

        return False

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React",
            ".tsx": "React TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bash": "Shell",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".md": "Markdown",
            ".dockerfile": "Docker",
        }

        return ext_map.get(file_path.suffix.lower())

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a source code file."""
        code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java",
            ".cpp", ".c", ".cs", ".go", ".rs", ".php", ".rb",
            ".swift", ".kt", ".scala", ".r", ".sql", ".sh",
            ".html", ".css", ".scss", ".sass", ".less"
        }
        return file_path.suffix.lower() in code_extensions

    async def _analyze_code_file(self, file_path: Path) -> None:
        """Analyze a single code file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract dependencies
            dependencies = self._extract_dependencies_from_content(content, file_path.suffix)
            relative_path = str(file_path.relative_to(self.root_path))

            for dep in dependencies:
                self.import_graph[relative_path].add(dep)

            # Store in cache
            self.file_cache[relative_path] = {
                "content": content,
                "dependencies": dependencies,
                "language": self._detect_language(file_path),
                "size": len(content)
            }

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._extract_dependencies_from_content(content, file_path.suffix)
        except Exception:
            return []

    def _extract_dependencies_from_content(self, content: str, extension: str) -> List[str]:
        """Extract dependencies from file content based on language."""
        dependencies = []

        if extension == ".py":
            # Python imports
            import_patterns = [
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)

        elif extension in [".js", ".ts", ".jsx", ".tsx"]:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'import\([\'"]([^\'"]+)[\'"]\)'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)

        elif extension == ".java":
            # Java imports
            import_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
            matches = re.findall(import_pattern, content)
            dependencies.extend(matches)

        elif extension in [".cpp", ".c"]:
            # C/C++ includes
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            matches = re.findall(include_pattern, content)
            dependencies.extend(matches)

        return list(set(dependencies))  # Remove duplicates

    def _build_dependency_graph(self) -> Dict[str, Any]:
        """Build dependency graph analysis."""
        # Internal dependencies (within project)
        internal_deps = defaultdict(set)
        # External dependencies (third-party)
        external_deps = defaultdict(set)

        for file_path, deps in self.import_graph.items():
            for dep in deps:
                if self._is_internal_dependency(dep):
                    internal_deps[file_path].add(dep)
                else:
                    external_deps[file_path].add(dep)

        return {
            "internal": {k: list(v) for k, v in internal_deps.items()},
            "external": {k: list(v) for k, v in external_deps.items()},
            "graph_stats": {
                "total_files_with_deps": len(self.import_graph),
                "total_internal_deps": sum(len(v) for v in internal_deps.values()),
                "total_external_deps": sum(len(v) for v in external_deps.values())
            }
        }

    def _is_internal_dependency(self, dep: str) -> bool:
        """Check if dependency is internal to the project."""
        # Simple heuristic - if it doesn't start with common external library patterns
        external_patterns = [
            "os", "sys", "json", "re", "datetime", "collections",
            "itertools", "functools", "operator", "pathlib", "typing",
            "react", "vue", "angular", "lodash", "moment", "axios",
            "numpy", "pandas", "scipy", "matplotlib", "sklearn"
        ]

        dep_lower = dep.lower()
        for pattern in external_patterns:
            if dep_lower.startswith(pattern):
                return False

        # If it contains a dot and doesn't start with common stdlib patterns
        if "." in dep and not dep.startswith(("os.", "sys.", "json.", "re.", "datetime.")):
            return True

        return False

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and patterns."""
        structure = {
            "type": "unknown",
            "frameworks": [],
            "patterns": [],
            "directories": {}
        }

        # Detect project type
        if (self.root_path / "package.json").exists():
            structure["type"] = "node.js"
            try:
                with open(self.root_path / "package.json", 'r') as f:
                    package_data = json.load(f)
                    structure["frameworks"] = [
                        dep for dep in package_data.get("dependencies", {}).keys()
                        if any(fw in dep for fw in ["react", "vue", "angular", "express", "next"])
                    ]
            except:
                pass

        elif (self.root_path / "requirements.txt").exists() or (self.root_path / "pyproject.toml").exists():
            structure["type"] = "python"

        elif (self.root_path / "pom.xml").exists():
            structure["type"] = "java"

        elif (self.root_path / "Cargo.toml").exists():
            structure["type"] = "rust"

        # Analyze directory structure
        for item in self.root_path.iterdir():
            if item.is_dir() and not self._should_ignore_file(item):
                structure["directories"][item.name] = {
                    "file_count": len(list(item.rglob("*"))),
                    "purpose": self._infer_directory_purpose(item.name)
                }

        # Detect common patterns
        structure["patterns"] = self._detect_patterns()

        return structure

    def _infer_directory_purpose(self, dir_name: str) -> str:
        """Infer the purpose of a directory from its name."""
        purposes = {
            "src": "Source code",
            "source": "Source code",
            "lib": "Library code",
            "test": "Test files",
            "tests": "Test files",
            "spec": "Test specifications",
            "docs": "Documentation",
            "doc": "Documentation",
            "build": "Build output",
            "dist": "Distribution",
            "out": "Output files",
            "config": "Configuration",
            "scripts": "Build/utility scripts",
            "assets": "Static assets",
            "static": "Static files",
            "public": "Public files",
            "vendor": "Third-party dependencies",
            "node_modules": "Node.js dependencies",
            "__pycache__": "Python cache",
            ".git": "Git repository",
            "examples": "Example code",
            "samples": "Sample code"
        }

        return purposes.get(dir_name.lower(), "Unknown")

    def _detect_patterns(self) -> List[str]:
        """Detect common project patterns."""
        patterns = []

        # Check for common configuration files
        config_files = [
            "package.json", "requirements.txt", "pyproject.toml",
            "Dockerfile", "docker-compose.yml", "Makefile",
            "tsconfig.json", "webpack.config.js", ".eslintrc.js",
            "pom.xml", "build.gradle", "Cargo.toml"
        ]

        for config_file in config_files:
            if (self.root_path / config_file).exists():
                patterns.append(f"Uses {config_file}")

        # Check for testing setup
        test_patterns = ["test/", "tests/", "spec/", "__tests__/"]
        for pattern in test_patterns:
            if any(self.root_path.glob(pattern)):
                patterns.append("Has test directory")
                break

        # Check for CI/CD
        ci_files = [".github", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml"]
        for ci_file in ci_files:
            if (self.root_path / ci_file).exists():
                patterns.append("Has CI/CD setup")
                break

        return patterns

    def _calculate_code_metrics(self) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        metrics = {
            "total_lines": 0,
            "total_files": len(self.file_cache),
            "avg_file_size": 0,
            "largest_files": [],
            "most_complex_files": [],
            "language_distribution": {}
        }

        if not self.file_cache:
            return metrics

        total_lines = 0
        file_sizes = []

        for file_path, file_info in self.file_cache.items():
            lines = len(file_info["content"].splitlines())
            size = file_info["size"]
            total_lines += lines
            file_sizes.append((file_path, size))

            language = file_info.get("language", "Unknown")
            metrics["language_distribution"][language] = metrics["language_distribution"].get(language, 0) + 1

        metrics["total_lines"] = total_lines
        metrics["avg_file_size"] = total_lines // len(self.file_cache) if self.file_cache else 0
        metrics["largest_files"] = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:10]

        return metrics

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate project improvement recommendations."""
        recommendations = []

        # File count recommendations
        if analysis["file_count"] > 1000:
            recommendations.append("Consider breaking down large projects into modules")

        # Language diversity
        if len(analysis["languages"]) > 5:
            recommendations.append("Project uses many languages - consider standardizing tech stack")

        # Test coverage check
        has_tests = any("test" in dir_name.lower() for dir_name in analysis["structure"].get("directories", {}))
        if not has_tests and analysis["file_count"] > 10:
            recommendations.append("Consider adding test files and test directory")

        # Documentation check
        has_docs = any("doc" in dir_name.lower() for dir_name in analysis["structure"].get("directories", {}))
        if not has_docs:
            recommendations.append("Consider adding documentation")

        # Configuration management
        if analysis["structure"]["type"] == "unknown":
            recommendations.append("Consider adding configuration files for better project management")

        return recommendations