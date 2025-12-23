"""Project management and utilities slash commands."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class InitCommand(SlashCommand):
    """Smart project initialization with templates."""

    def __init__(self):
        super().__init__(
            name="init",
            description="Initialize a new project with smart templates",
            aliases=["new-project", "scaffold"],
            category="project",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the init command."""
        if not args:
            return """Usage: /init <template> [project_name]
Available templates:
- api: REST API project
- cli: Command-line tool
- lib: Library/package
- web: Web application
- ml: Machine learning project
- data: Data science project
- mobile: Mobile app (React Native)
- microservice: Microservice with Docker
- game: Game project (Unity/Godot)
- docs: Documentation site

Examples:
- /init api my-api-project
- /init cli
- /init ml sentiment-analyzer"""

        template = args[0].lower()
        project_name = args[1] if len(args) > 1 else None

        # Get current directory for project
        project_dir = Path(context.working_directory)
        if project_name:
            project_dir = project_dir / project_name

        try:
            # Check if directory exists and is not empty
            if project_dir.exists() and any(project_dir.iterdir()):
                return f"Error: Directory '{project_dir}' is not empty. Choose an empty directory or provide a project name."

            # Create project directory
            project_dir.mkdir(parents=True, exist_ok=True)

            # Initialize based on template
            if template == "api":
                await self._init_api_project(project_dir, project_name or "my-api")
            elif template == "cli":
                await self._init_cli_project(project_dir, project_name or "my-cli")
            elif template == "lib":
                await self._init_lib_project(project_dir, project_name or "my-lib")
            elif template == "web":
                await self._init_web_project(project_dir, project_name or "my-web")
            elif template == "ml":
                await self._init_ml_project(project_dir, project_name or "my-ml")
            elif template == "data":
                await self._init_data_project(project_dir, project_name or "my-data")
            elif template == "microservice":
                await self._init_microservice_project(project_dir, project_name or "my-service")
            elif template == "docs":
                await self._init_docs_project(project_dir, project_name or "my-docs")
            else:
                return f"Unknown template: {template}. Use /init to see available templates."

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)

            # Create initial commit
            subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from vibe-coder"],
                cwd=project_dir,
                capture_output=True,
            )

            return f"""✅ Project initialized successfully!

Template: {template}
Location: {project_dir}
Git repository: Initialized

Next steps:
1. cd {project_dir.relative_to(context.working_directory)}
2. Review generated files
3. Install dependencies
4. Start coding!

{await self._get_next_steps(template)}"""

        except Exception as e:
            return f"Error initializing project: {e}"

    async def _init_api_project(self, project_dir: Path, project_name: str):
        """Initialize an API project."""
        file_ops = FileOperations(str(project_dir))

        # Python API with FastAPI
        await file_ops.write_file(
            "requirements.txt",
            """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
httpx>=0.25.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
""",
        )

        await file_ops.write_file(
            "main.py",
            f"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn

app = FastAPI(
    title="{project_name.title()} API",
    description="API for {project_name}",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name.title()} API"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "version": "0.1.0"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
        )

        await file_ops.write_file(
            "app/models.py",
            """from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BaseResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseResponse):
    version: str
    timestamp: datetime


class ErrorResponse(BaseResponse):
    error_code: Optional[str] = None
    details: Optional[dict] = None
""",
        )

        await file_ops.write_file(
            "tests/test_main.py",
            """import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
""",
        )

        await file_ops.write_file(
            ".env.example",
            """# Environment variables
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db
API_V1_STR=/api/v1
PROJECT_NAME={project_name}
""",
        )

        await file_ops.write_file(
            ".gitignore",
            """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env
.env.local
.env.production

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
        )

    async def _init_cli_project(self, project_dir: Path, project_name: str):
        """Initialize a CLI project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "requirements.txt",
            """click>=8.1.0
rich>=13.7.0
typer>=0.9.0
pydantic>=2.5.0
pytest>=7.4.0
pytest-cov>=4.1.0
""",
        )

        await file_ops.write_file(
            f"{project_name.replace('-', '_')}.py",
            f'''"""CLI application for {project_name}."""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="{project_name.title()} CLI Tool")
console = Console()


@app.command()
def hello(name: str = "World"):
    """Say hello to someone."""
    console.print(f"Hello [bold green]{{name}}[/bold green]!")


@app.command()
def version():
    """Show version information."""
    console.print(f"{project_name} v0.1.0")


@app.command()
def status():
    """Show current status."""
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("CLI", "✅ Running")
    table.add_row("Config", "✅ Loaded")
    table.add_row("System", "✅ Ready")

    console.print(table)


if __name__ == "__main__":
    app()
''',
        )

        await file_ops.write_file(
            "setup.py",
            f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "rich>=13.7.0",
        "typer>=0.9.0",
    ],
    entry_points={{
        "console_scripts": [
            "{project_name} = {project_name.replace('-', '_')}:app",
        ],
    }},
)
""",
        )

    async def _init_lib_project(self, project_dir: Path, project_name: str):
        """Initialize a library project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "pyproject.toml",
            f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "A Python library"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "flake8>=6.0.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
line_length = 100
""",
        )

        await file_ops.write_file("src/__init__.py", "")
        await file_ops.write_file(
            f"src/{project_name.replace('-', '_')}/__init__.py",
            f'''"""{project_name.title()} - A Python library."""

__version__ = "0.1.0"
__author__ = "Your Name"

from .core import {project_name.replace('-', '_').title()}

__all__ = ["{project_name.replace('-', '_').title()}"]
''',
        )

        await file_ops.write_file(
            f"src/{project_name.replace('-', '_')}/core.py",
            f'''"""Core functionality for {project_name}."""

from typing import Any, Dict, List


class {project_name.replace('-', '_').title()}:
    """Main class for {project_name} library."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize {project_name.title()}."""
        self.config = config or {{}}

    def process(self, data: Any) -> Any:
        """Process data using {project_name} logic."""
        # TODO: Implement your processing logic here
        return data

    def get_info(self) -> Dict[str, Any]:
        """Get information about the instance."""
        return {{
            "version": "0.1.0",
            "config": self.config,
        }}
''',
        )

    async def _init_web_project(self, project_dir: Path, project_name: str):
        """Initialize a web project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "package.json",
            f"""{{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "Web application for {project_name}",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.6.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "eslint": "^8.45.0",
    "typescript": "^5.0.0"
  }}
}}""",
        )

        await file_ops.write_file(
            "vite.config.ts",
            """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
""",
        )

    async def _init_ml_project(self, project_dir: Path, project_name: str):
        """Initialize an ML project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "requirements.txt",
            """numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
jupyter>=1.0.0
pytest>=7.4.0
torch>=2.0.0
transformers>=4.35.0
""",
        )

        await file_ops.write_file(
            "src/data.py",
            """import pandas as pd
import numpy as np
from typing import Tuple, Optional


def load_data(filepath: str) -> pd.DataFrame:
    \"\"\"Load data from file.\"\"\"
    return pd.read_csv(filepath)


def preprocess_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    \"\"\"Preprocess data for ML.\"\"\"
    # TODO: Implement preprocessing
    X = df.drop('target', axis=1).values
    y = df['target'].values
    return X, y


def split_data(X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Tuple:
    \"\"\"Split data into train and test sets.\"\"\"
    from sklearn.model_selection import train_test_split
    return train_test_split(X, y, test_size=test_size, random_state=42)
""",
        )

    async def _init_data_project(self, project_dir: Path, project_name: str):
        """Initialize a data science project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "requirements.txt",
            """pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.17.0
jupyter>=1.0.0
scipy>=1.11.0
statsmodels>=0.14.0
""",
        )

        await file_ops.write_file(
            "analysis.ipynb",
            """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Data Analysis Notebook\\n",
    "\\n",
    "This notebook contains the analysis for """
            + project_name
            + """"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "source": [
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "\\n",
    "%matplotlib inline"
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 2
}""",
        )

    async def _init_microservice_project(self, project_dir: Path, project_name: str):
        """Initialize a microservice project."""
        # Create API project first
        await self._init_api_project(project_dir, project_name)

        # Add Docker files
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "Dockerfile",
            f"""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        )

        await file_ops.write_file(
            "docker-compose.yml",
            f"""version: '3.8'

services:
  {project_name}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/{project_name}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB={project_name}
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""",
        )

    async def _init_docs_project(self, project_dir: Path, project_name: str):
        """Initialize a documentation project."""
        file_ops = FileOperations(str(project_dir))

        await file_ops.write_file(
            "mkdocs.yml",
            f"""site_name: {project_name.title()}
site_description: Documentation for {project_name}

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api.md
  - Examples: examples.md

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections

plugins:
  - search
  - mkdocstrings

markdown_extensions:
  - codehilite
  - admonition
  - toc
""",
        )

        await file_ops.write_file(
            "docs/index.md",
            f"""# Welcome to {project_name.title()}

This is the documentation for {project_name}.

## Getting Started

1. Read the [Getting Started guide](getting-started.md)
2. Check the [API Reference](api.md)
3. Browse the [Examples](examples.md)
""",
        )

    async def _get_next_steps(self, template: str) -> str:
        """Get next steps based on template."""
        steps = {
            "api": "\n🚀 Run your API:\n   pip install -r requirements.txt\n   uvicorn main:app --reload",
            "cli": "\n🔧 Install your CLI:\n   pip install -e .\n   "
            + (Path.cwd().name if Path.cwd().name else "my-cli")
            + " --help",
            "lib": "\n📦 Install in development mode:\n   pip install -e .[dev]",
            "web": "\n🌐 Start development:\n   npm install\n   npm run dev",
            "ml": "\n🧪 Start experimenting:\n   pip install -r requirements.txt\n   jupyter notebook",
            "data": "\n📊 Start analyzing:\n   pip install -r requirements.txt\n   jupyter notebook analysis.ipynb",
            "microservice": "\n🐳 Run with Docker:\n   docker-compose up",
            "docs": "\n📚 Build documentation:\n   pip install mkdocs-material\n   mkdocs serve",
        }
        return steps.get(template, "\n✨ Review your new project files!")

    def get_min_args(self) -> int:
        return 1


class DependenciesCommand(SlashCommand):
    """Dependency management."""

    def __init__(self):
        super().__init__(
            name="dependencies",
            description="Manage project dependencies",
            aliases=["deps", "requirements"],
            category="project",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the dependencies command."""
        if not args:
            return """Usage: /dependencies <action> [options]
Actions:
- update: Update all dependencies
- audit: Check for security vulnerabilities
- clean: Remove unused dependencies
- tree: Show dependency tree
- outdated: List outdated packages

Examples:
- /dependencies update
- /dependencies audit
- /dependencies clean"""

        action = args[0].lower()

        if action == "update":
            return await self._update_dependencies(context)
        elif action == "audit":
            return await self._audit_dependencies(context)
        elif action == "clean":
            return await self._clean_dependencies(context)
        elif action == "tree":
            return await self._show_dependency_tree(context)
        elif action == "outdated":
            return await self._show_outdated(context)
        else:
            return f"Unknown action: {action}"

    async def _update_dependencies(self, context: CommandContext) -> str:
        """Update project dependencies."""
        project_files = [
            "package.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "requirements.txt",
            "poetry.lock",
            "Pipfile.lock",
            "Cargo.lock",
            "go.mod",
            "pom.xml",
            "build.gradle",
        ]

        detected_project = None
        for file in project_files:
            if Path(context.working_directory / file).exists():
                detected_project = file
                break

        if not detected_project:
            return "No package manager detected. Supported: npm, yarn, pnpm, pip, poetry, cargo, go, maven, gradle"

        if detected_project == "package.json":
            return "Run: npm update\nOr: npm install package@latest"
        elif detected_project == "requirements.txt":
            return "Run: pip install --upgrade -r requirements.txt\nOr use pip-tools: pip-compile requirements.in"
        elif detected_project == "pyproject.toml":
            return "Run: poetry update\nOr: poetry upgrade"
        elif detected_project == "Cargo.lock":
            return "Run: cargo update"
        elif detected_project == "go.mod":
            return "Run: go get -u ./..."
        else:
            return f"Update command for {detected_project} not implemented yet"

    async def _audit_dependencies(self, context: CommandContext) -> str:
        """Check for security vulnerabilities."""
        results = []

        # Check for Python dependencies
        if Path(context.working_directory / "requirements.txt").exists():
            results.append("🐍 Python:\n   Run: pip-audit\n   Install: pip install pip-audit")

        # Check for Node.js dependencies
        if Path(context.working_directory / "package.json").exists():
            results.append("📦 Node.js:\n   Run: npm audit\n   Or: yarn audit")

        # Check for Rust dependencies
        if Path(context.working_directory / "Cargo.lock").exists():
            results.append("🦀 Rust:\n   Run: cargo audit\n   Install: cargo install cargo-audit")

        if not results:
            return "No supported dependencies found for auditing"

        return "\n\n".join(results)

    async def _clean_dependencies(self, context: CommandContext) -> str:
        """Remove unused dependencies."""
        results = []

        # Python
        if Path(context.working_directory / "requirements.txt").exists():
            results.append(
                "🐍 Python:\n   Run: pip-autoremove\n   Install: pip install pip-autoremove"
            )

        # Node.js
        if Path(context.working_directory / "package.json").exists():
            results.append("📦 Node.js:\n   Run: npm prune\n   Or use depcheck: npx depcheck")

        return "\n\n".join(results) if results else "No dependencies to clean"

    async def _show_dependency_tree(self, context: CommandContext) -> str:
        """Show dependency tree."""
        results = []

        if Path(context.working_directory / "package.json").exists():
            results.append("📦 Node.js:\n   Run: npm ls --tree\n   Or: npm ls --all")

        if Path(context.working_directory / "requirements.txt").exists():
            results.append("🐍 Python:\n   Run: pip show -t requirements.txt")

        return "\n\n".join(results) if results else "No dependencies to show"

    async def _show_outdated(self, context: CommandContext) -> str:
        """Show outdated packages."""
        results = []

        if Path(context.working_directory / "package.json").exists():
            results.append("📦 Node.js:\n   Run: npm outdated")

        if Path(context.working_directory / "requirements.txt").exists():
            results.append("🐍 Python:\n   Run: pip list --outdated")

        if Path(context.working_directory / "pyproject.toml").exists():
            results.append("🐍 Python (Poetry):\n   Run: poetry show --outdated")

        return "\n\n".join(results) if results else "No dependencies to check"

    def get_min_args(self) -> int:
        return 1


class SecurityCommand(SlashCommand):
    """Security scanning."""

    def __init__(self):
        super().__init__(
            name="security",
            description="Scan code for security vulnerabilities",
            aliases=["sec-scan", "audit"],
            category="project",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the security command."""
        target = args[0] if args else "."

        try:
            # Determine file type
            target_path = Path(target)
            if target_path.is_file():
                language = self._detect_language(target_path.name)
                return await self._scan_file(context, target, language)
            else:
                return await self._scan_directory(context, target)

        except Exception as e:
            return f"Error during security scan: {e}"

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        ext = Path(filename).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
        }
        return lang_map.get(ext, "unknown")

    async def _scan_file(self, context: CommandContext, filepath: str, language: str) -> str:
        """Scan a single file for security issues."""
        file_ops = FileOperations(context.working_directory)

        try:
            content = await file_ops.read_file(filepath)

            # Build security scan prompt
            prompt = f"""Scan the following {language} code for security vulnerabilities:

Focus on:
1. SQL injection vulnerabilities
2. Cross-site scripting (XSS)
3. Path traversal attacks
4. Command injection
5. Insecure cryptographic usage
6. Hard-coded secrets or API keys
7. Insecure random number generation
8. Buffer overflow risks
9. Race conditions
10. Authentication bypass

Code to scan:
```{language}
{content}
```

Provide:
- List of found vulnerabilities with severity
- Line numbers where issues occur
- Recommended fixes for each issue"""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": "You are a security expert. Identify potential vulnerabilities in code and provide actionable recommendations for fixing them.",
                        "name": "SecurityScanner",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            return f"""Security scan completed for: {filepath}

{response.content}

Additional security tools to consider:
- Python: bandit, semgrep
- JavaScript: eslint-plugin-security
- Java: SpotBugs, PMD
- Go: gosec
- Rust: cargo-audit

To run automated scans:
pip install bandit
bandit {filepath}
"""

        except Exception as e:
            return f"Error scanning file: {e}"

    async def _scan_directory(self, context: CommandContext, directory: str) -> str:
        """Scan directory for security issues."""
        dir_path = Path(directory) if directory != "." else Path(context.working_directory)

        # Find code files to scan
        code_extensions = [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".go",
            ".rb",
            ".php",
            ".cs",
            ".cpp",
            ".c",
            ".rs",
        ]
        code_files = []

        for ext in code_extensions:
            code_files.extend(dir_path.rglob(f"*{ext}"))

        if not code_files:
            return f"No code files found in {directory}"

        # Limit scan to 20 files for performance
        files_to_scan = code_files[:20]

        results = [f"🔒 Security scan for directory: {directory}"]
        results.append(f"📁 Scanning {len(files_to_scan)} files (of {len(code_files)} total)\n")

        for file_path in files_to_scan:
            rel_path = file_path.relative_to(context.working_directory)
            language = self._detect_language(file_path.name)

            # Quick scan for common issues
            try:
                content = file_path.read_text(encoding="utf-8")

                # Check for common vulnerability patterns
                issues = []

                # Check for hard-coded secrets
                import re

                if re.search(
                    r'(password|secret|key)\s*[=:]\s*["\'][^"\']+["\']', content, re.IGNORECASE
                ):
                    issues.append("Potential hard-coded secret")

                # Check for SQL injection patterns
                if re.search(r'execute\s*\(\s*["\'].*%.*["\']', content):
                    issues.append("Potential SQL injection")

                # Check for eval usage
                if "eval(" in content or "exec(" in content:
                    issues.append("Dangerous eval/exec usage")

                if issues:
                    results.append(f"⚠️  {rel_path} ({language}):")
                    for issue in issues:
                        results.append(f"   • {issue}")

            except Exception:
                pass

        # Add recommendations
        results.append("\n💡 Security Recommendations:")
        results.append("1. Run automated security scanners:")
        results.append("   - Python: bandit, safety, semgrep")
        results.append("   - JavaScript: npm audit, semgrep")
        results.append("   - All languages: CodeQL, Snyk")
        results.append("\n2. Enable static analysis in CI/CD")
        results.append("3. Regular dependency updates")
        results.append("4. Security code reviews")

        return "\n".join(results)

    def get_min_args(self) -> int:
        return 0


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(InitCommand())
command_registry.register(DependenciesCommand())
command_registry.register(SecurityCommand())


def register():
    """Register all project management commands."""
    return [
        InitCommand(),
        DependenciesCommand(),
        SecurityCommand(),
    ]
