"""Advanced code generation and manipulation slash commands."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class CompleteCommand(SlashCommand):
    """AI-powered code completion."""

    def __init__(self):
        super().__init__(
            name="complete",
            description="Complete partial code using AI",
            aliases=["comp", "autocomplete"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the complete command."""
        if not args:
            return "Usage: /complete <partial_code>. Complete the provided code snippet."

        # Join all args as the code to complete
        code_snippet = " ".join(args)

        # If code looks like a file path, read the file
        if len(args) == 1 and Path(args[0]).exists():
            file_ops = FileOperations(context.working_directory)
            code_snippet = await file_ops.read_file(args[0])

        # Build the completion prompt
        prompt = f"""Complete the following code snippet. Provide only the completed code without explanations:

{code_snippet}

Continue from where the code ends."""

        try:
            # Get AI response
            response = await context.provider.client.send_request([
                {"role": "system", "content": "You are a code completion assistant. Complete the given code snippet accurately and concisely."},
                {"role": "user", "content": prompt}
            ])

            completed_code = response.content.strip()

            # If we read from a file, offer to update it
            if len(args) == 1 and Path(args[0]).exists():
                file_ops = FileOperations(context.working_directory)
                await file_ops.write_file(args[0], code_snippet + "\n" + completed_code)
                return f"Code completed and saved to {args[0]}:\n\n{completed_code}"

            return f"Completed code:\n{completed_code}"

        except Exception as e:
            return f"Error completing code: {e}"

    def get_min_args(self) -> int:
        return 1


class OptimizeCommand(SlashCommand):
    """Performance optimization for code."""

    def __init__(self):
        super().__init__(
            name="optimize",
            description="Optimize code for better performance",
            aliases=["perf", "performance"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the optimize command."""
        if not args:
            return "Usage: /optimize <filename>. Optimize the specified file for performance."

        file_path = args[0]
        file_ops = FileOperations(context.working_directory)

        try:
            # Read the file
            content = await file_ops.read_file(file_path)

            # Determine language for specific optimizations
            language = file_ops.detect_language(file_path)

            # Build optimization prompt
            prompt = f"""Optimize the following {language} code for better performance. Focus on:
1. Algorithm efficiency
2. Memory usage
3. I/O operations
4. Language-specific optimizations
5. Best practices

Provide:
- Optimized code
- Brief explanation of key optimizations made
- Performance improvements expected

Original code:
```{language}
{content}
```"""

            # Get AI response
            response = await context.provider.client.send_request([
                {"role": "system", "content": "You are a performance optimization expert. Analyze code and provide optimized versions with clear explanations."},
                {"role": "user", "content": prompt}
            ])

            # Create backup before optimizing
            backup_path = await file_ops.create_backup(file_path)

            # Extract the optimized code (assume it's in a code block)
            optimized_content = response.content
            if "```" in optimized_content:
                # Extract code from markdown block
                start = optimized_content.find("```") + 3
                end = optimized_content.find("```", start)
                if end != -1:
                    # Remove language identifier if present
                    code_start = start
                    if "\n" in optimized_content[start:end]:
                        code_start = optimized_content.find("\n", start) + 1
                    optimized_content = optimized_content[code_start:end]

            # Write optimized code
            await file_ops.write_file(file_path, optimized_content)

            return f"""Code optimized successfully!
- Backup saved to: {backup_path}
- Optimizations applied by AI

{response.content}"""

        except Exception as e:
            return f"Error optimizing code: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


class TemplateCommand(SlashCommand):
    """Generate code from templates."""

    def __init__(self):
        super().__init__(
            name="template",
            description="Generate code from predefined templates",
            aliases=["tmpl", "boilerplate"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the template command."""
        if not args:
            return """Usage: /template <type> <name>
Available template types:
- api <name>: REST API endpoint
- class <name>: Class with methods
- test <name>: Test file template
- cli <name>: CLI command structure
- config <name>: Configuration file
- docker <name>: Dockerfile template
- github <name>: GitHub Actions workflow
- readme <name>: README.md template"""

        if len(args) < 2:
            return "Error: Template requires type and name. Use /template to see available types."

        template_type = args[0].lower()
        name = args[1]
        extra_args = args[2:] if len(args) > 2 else []

        # Define templates
        templates = {
            "api": self._get_api_template,
            "class": self._get_class_template,
            "test": self._get_test_template,
            "cli": self._get_cli_template,
            "config": self._get_config_template,
            "docker": self._get_docker_template,
            "github": self._get_github_template,
            "readme": self._get_readme_template,
        }

        if template_type not in templates:
            return f"Unknown template type: {template_type}. Use /template to see available types."

        try:
            # Generate template content
            template_func = templates[template_type]
            content = template_func(name, extra_args)

            # Determine output file
            file_ops = FileOperations(context.working_directory)
            filename = self._get_filename_for_template(template_type, name)

            # Write the template
            await file_ops.write_file(filename, content)

            return f"Template generated: {filename}"

        except Exception as e:
            return f"Error generating template: {e}"

    def _get_api_template(self, name: str, args: List[str]) -> str:
        """Generate API endpoint template."""
        method = args[0] if args else "GET"
        path = args[1] if len(args) > 1 else f"/{name.lower()}"

        return f'''from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="{path}", tags=["{name}"])

class {name.title()}Request(BaseModel):
    """Request model for {name} endpoint."""
    pass

class {name.title()}Response(BaseModel):
    """Response model for {name} endpoint."""
    pass

@router.{method.lower()}("/")
async def {name.lower()}_endpoint(
    request: Optional[{name.title()}Request] = None
) -> {name.title()}Response:
    """
    {method} {path}

    Description: {name} endpoint implementation
    """
    # TODO: Implement endpoint logic
    return {name.title()}Response(
        status="success",
        message="{name} endpoint"
    )
'''

    def _get_class_template(self, name: str, args: List[str]) -> str:
        """Generate class template."""
        base_class = args[0] if args else "object"

        return f'''class {name.title()}({base_class}):
    """
    {name.title()} class implementation.

    Description: [Add class description here]
    """

    def __init__(self{", " + ", ".join([f"{arg}: str" for arg in args[1:]]) if len(args) > 1 else ""}):
        """
        Initialize {name.title()} instance.
        """
        super().__init__()
        {chr(10).join([f"        self.{arg} = {arg}" for arg in args[1:]]) if len(args) > 1 else ""}
        # TODO: Add initialization logic

    def __str__(self) -> str:
        """String representation of {name.title()}."""
        return f"{name.title()}({{self._get_attributes()}})"

    def _get_attributes(self) -> str:
        """Get attributes for string representation."""
        return ", ".join([f"{arg}={{self.{arg}}}" for arg in args[1:]]) if len(args) > 1 else ""

    # TODO: Add methods
'''

    def _get_test_template(self, name: str, args: List[str]) -> str:
        """Generate test file template."""
        import pytest

        return f'''"""Tests for {name} module."""

import pytest
from unittest.mock import Mock, patch

# TODO: Import the module/class to test
# from {name} import {name.title()}

class Test{name.title()}:
    """Test suite for {name.title()}."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        # TODO: Create test fixtures
        pass

    def teardown_method(self):
        """Clean up after each test."""
        # TODO: Clean up test fixtures
        pass

    def test_initialization(self):
        """Test {name.title()} initialization."""
        # TODO: Write initialization test
        assert True  # Placeholder

    def test_basic_functionality(self):
        """Test basic functionality of {name.title()}."""
        # TODO: Write functionality test
        assert True  # Placeholder

    @pytest.mark.parametrize("input_data,expected", [
        # TODO: Add test cases
        (None, None),
    ])
    def test_with_parameters(self, input_data, expected):
        """Test {name.title()} with different parameters."""
        # TODO: Write parameterized test
        assert True  # Placeholder
'''

    def _get_cli_template(self, name: str, args: List[str]) -> str:
        """Generate CLI command template."""
        import typer

        return f'''"""CLI command implementation for {name}."""

import typer
from typing import Optional, List

app = typer.Typer(help="{name.title()} command")

@app.command()
def {name.lower()}(
    input_file: Optional[str] = typer.Option(None, "--input", "-i", help="Input file path"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    {name.title()} CLI command.

    Description: [Add command description here]
    """
    # TODO: Implement command logic
    if verbose:
        typer.echo(f"Running {name} command...")

    if input_file:
        typer.echo(f"Processing input: {{input_file}}")

    # TODO: Add implementation

    if output_file:
        typer.echo(f"Results saved to: {{output_file}}")

if __name__ == "__main__":
    app()
'''

    def _get_config_template(self, name: str, args: List[str]) -> str:
        """Generate configuration file template."""
        return f'''# {name.title()} Configuration

# Application settings
app_name = "{name}"
debug = true
version = "0.1.0"

# Database settings
database_url = "sqlite:///./{name.lower()}.db"
database_pool_size = 10

# API settings
api_host = "localhost"
api_port = 8000
api_prefix = "/api/v1"

# Security settings
secret_key = "your-secret-key-here"
access_token_expire_minutes = 30

# Logging settings
log_level = "INFO"
log_file = "{name.lower()}.log"

# TODO: Add additional configuration as needed
'''

    def _get_docker_template(self, name: str, args: List[str]) -> str:
        """Generate Dockerfile template."""
        return f'''# Dockerfile for {name}
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV {name.upper()}_ENV=production

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "{name}"]
'''

    def _get_github_template(self, name: str, args: List[str]) -> str:
        """Generate GitHub Actions workflow template."""
        return f'''name: {name.title()} CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint with flake8
      run: |
        flake8 {name} tests

    - name: Type check with mypy
      run: mypy {name}

    - name: Test with pytest
      run: |
        pytest --cov={name} --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      run: |
        echo "Deploying {name} to production..."
        # TODO: Add deployment steps
'''

    def _get_readme_template(self, name: str, args: List[str]) -> str:
        """Generate README.md template."""
        return f'''# {name.title()}

{args[0] if args else "Description of the " + name + " project."}

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Clone the repository
git clone https://github.com/username/{name}.git
cd {name}

# Install dependencies
pip install -r requirements.txt

# Or with poetry
poetry install
```

## Usage

```python
# TODO: Add usage example
from {name} import {name.title()}

# Create instance
instance = {name.title()}()

# Use the functionality
result = instance.some_method()
print(result)
```

## API Reference

### {name.title()}

Main class for {name} functionality.

#### Methods

##### `__init__()`
Initialize {name.title()} instance.

##### `some_method()`
Perform some operation.

**Returns:**
- `result`: The operation result

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov={name}

# Lint code
flake8 {name}

# Type check
mypy {name}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### [0.1.0] - 2024-01-01

#### Added
- Initial release
- Basic functionality
'''

    def _get_filename_for_template(self, template_type: str, name: str) -> str:
        """Get appropriate filename for template type."""
        extensions = {
            "api": f"{name.lower()}_endpoint.py",
            "class": f"{name.lower()}.py",
            "test": f"test_{name.lower()}.py",
            "cli": f"{name.lower()}.py",
            "config": f"{name.lower()}.py",
            "docker": "Dockerfile",
            "github": ".github/workflows/ci.yml",
            "readme": "README.md",
        }
        return extensions.get(template_type, f"{name.lower()}.txt")

    def get_min_args(self) -> int:
        return 2

    def get_max_args(self) -> Optional[int]:
        return 10


class ConvertCommand(SlashCommand):
    """Convert code between programming languages."""

    def __init__(self):
        super().__init__(
            name="convert",
            description="Convert code from one language to another",
            aliases=["transform", "language-switch"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the convert command."""
        if len(args) < 3:
            return """Usage: /convert <from_lang> <to_lang> <file_or_code>
Supported languages: python, javascript, typescript, java, csharp, go, rust
Example: /convert python javascript app.py"""

        from_lang = args[0].lower()
        to_lang = args[1].lower()
        target = args[2]

        # Validate languages
        supported = ["python", "javascript", "typescript", "java", "csharp", "go", "rust"]
        if from_lang not in supported or to_lang not in supported:
            return f"Unsupported language. Supported: {', '.join(supported)}"

        try:
            file_ops = FileOperations(context.working_directory)

            # Get the code to convert
            if Path(target).exists():
                code_content = await file_ops.read_file(target)
                output_file = f"{Path(target).stem}.{to_lang}"
            else:
                code_content = target
                output_file = f"converted.{to_lang}"

            # Build conversion prompt
            prompt = f"""Convert the following {from_lang} code to {to_lang}.

Requirements:
- Maintain the same functionality
- Follow {to_lang} best practices and idioms
- Add appropriate error handling
- Include necessary imports/dependencies
- Preserve comments where applicable

Original code:
```{from_lang}
{code_content}
```

Provide only the converted {to_lang} code without explanations."""

            # Get AI response
            response = await context.provider.client.send_request([
                {"role": "system", "content": f"You are an expert in both {from_lang} and {to_lang}. Convert code accurately while maintaining functionality."},
                {"role": "user", "content": prompt}
            ])

            converted_code = response.content.strip()

            # Save converted code
            await file_ops.write_file(output_file, converted_code)

            return f"""Code converted successfully!
- From: {from_lang} → To: {to_lang}
- Output: {output_file}

Preview:
```{to_lang}
{converted_code[:500]}{"..." if len(converted_code) > 500 else ""}
```"""

        except Exception as e:
            return f"Error converting code: {e}"

    def get_min_args(self) -> int:
        return 3

    def get_max_args(self) -> Optional[int]:
        return 3


class ParallelizeCommand(SlashCommand):
    """Add concurrency patterns to sequential code."""

    def __init__(self):
        super().__init__(
            name="parallelize",
            description="Add concurrency patterns to code",
            aliases=["async", "concurrent"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the parallelize command."""
        if not args:
            return "Usage: /parallelize <filename>. Add concurrency patterns to the specified file."

        file_path = args[0]
        file_ops = FileOperations(context.working_directory)

        try:
            # Read the file
            content = await file_ops.read_file(file_path)
            language = file_ops.detect_language(file_path)

            # Build parallelization prompt
            if language == "python":
                prompt = f"""Parallelize the following Python code using appropriate patterns:

For CPU-bound tasks: Use multiprocessing or concurrent.futures
For I/O-bound tasks: Use asyncio or threading
For web requests: Use aiohttp + asyncio
For data processing: Use concurrent.futures.ProcessPoolExecutor

Original code:
```python
{content}
```

Provide:
- Parallelized version with appropriate imports
- Explanation of the parallelization strategy used
- Any considerations for shared resources or race conditions"""
            else:
                return f"Parallelization not yet supported for {language}. Currently supports Python only."

            # Get AI response
            response = await context.provider.client.send_request([
                {"role": "system", "content": "You are an expert in concurrent programming. Add appropriate parallelization patterns to code while maintaining correctness."},
                {"role": "user", "content": prompt}
            ])

            # Create backup
            backup_path = await file_ops.create_backup(file_path)

            # Extract parallelized code
            parallelized_content = response.content
            if "```" in parallelized_content:
                start = parallelized_content.find("```python") + 9
                end = parallelized_content.find("```", start)
                if end != -1:
                    parallelized_content = parallelized_content[start:end]

            # Save parallelized version
            parallel_file = file_path.replace('.py', '_parallel.py')
            await file_ops.write_file(parallel_file, parallelized_content)

            return f"""Code parallelized successfully!
- Original: {file_path}
- Parallelized: {parallel_file}
- Backup: {backup_path}

{response.content}"""

        except Exception as e:
            return f"Error parallelizing code: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(CompleteCommand())
command_registry.register(OptimizeCommand())
command_registry.register(TemplateCommand())
command_registry.register(ConvertCommand())
command_registry.register(ParallelizeCommand())

def register():
    """Register all advanced code commands."""
    return [
        CompleteCommand(),
        OptimizeCommand(),
        TemplateCommand(),
        ConvertCommand(),
        ParallelizeCommand(),
    ]