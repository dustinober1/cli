"""Documentation generation slash commands."""

import json
from pathlib import Path
from typing import List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class DocsCommand(SlashCommand):
    """Generate documentation for code."""

    def __init__(self):
        super().__init__(
            name="docs",
            description="Generate documentation for code",
            aliases=["documentation", "docstring"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the docs command."""
        if not args:
            return """Usage: /docs <filename> [options]
Options:
- --format <type>: Output format (markdown, html, docstring)
- --output <file>: Save to specific file
- --include-examples: Include usage examples

Examples:
- /docs app.py
- /docs app.py --format html --output docs.html
- /docs app.py --include-examples"""

        filename = args[0]
        options = [arg for arg in args[1:] if arg.startswith("--")]
        format_type = "markdown"
        output_file = None
        include_examples = False

        # Parse options
        for i, opt in enumerate(options):
            if opt == "--format" and i + 1 < len(options):
                format_type = options[i + 1]
            elif opt == "--output" and i + 1 < len(options):
                output_file = options[i + 1]
            elif opt == "--include-examples":
                include_examples = True

        file_ops = FileOperations(context.working_directory)

        try:
            content = await file_ops.read_file(filename)
            language = file_ops.detect_language(filename)

            # Build documentation prompt
            prompt = f"""Generate comprehensive documentation for this {language} code:

Requirements:
- Format: {format_type}
- Include function/class descriptions
- Add parameter documentation
- Provide return value descriptions
- Include usage examples" if include_examples else ""

Code:
```{language}
{content}
```

Generate appropriate {"OpenAPI/Swagger" if "api" in filename.lower() or "route" in content.lower() else ""} documentation."""

            response = await context.provider.client.send_request([
                {"role": "system", "content": f"You are a technical writer who creates clear, comprehensive documentation. Generate documentation in {format_type} format.",
                 "name": "DocumentationGenerator"},
                {"role": "user", "content": prompt}
            ])

            docs_content = response.content.strip()

            # Save documentation if output file specified
            if output_file:
                await file_ops.write_file(output_file, docs_content)
                return f"📄 Documentation saved to {output_file}\n\nPreview:\n{docs_content[:500]}..."

            return f"""📖 Documentation for {filename}

{docs_content}"""

        except Exception as e:
            return f"Error generating documentation: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


class ApiDocsCommand(SlashCommand):
    """Generate API documentation (OpenAPI/Swagger)."""

    def __init__(self):
        super().__init__(
            name="docs-api",
            description="Generate OpenAPI/Swagger documentation",
            aliases=["api-docs", "openapi"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the api-docs command."""
        if not args:
            return """Usage: /docs-api <spec_file.py|output.yaml> [options]
Options:
- --format <type>: Output format (yaml, json)
- --server <url>: API server URL
- --info <title>: API title
- --version <ver>: API version

Examples:
- /docs-api app.py
- /docs-api api.yaml --format json
- /docs-api app.py --server https://api.example.com --info "My API" --version 1.0.0"""

        target = args[0]
        options = [arg for arg in args[1:] if arg.startswith("--")]
        format_type = "yaml"
        server_url = "http://localhost:8000"
        api_title = "API Documentation"
        api_version = "1.0.0"

        # Parse options
        for i, opt in enumerate(options):
            if opt == "--format" and i + 1 < len(options):
                format_type = options[i + 1]
            elif opt == "--server" and i + 1 < len(options):
                server_url = options[i + 1]
            elif opt == "--info" and i + 1 < len(options):
                api_title = options[i + 1]
            elif opt == "--version" and i + 1 < len(options):
                api_version = options[i + 1]

        file_ops = FileOperations(context.working_directory)
        target_path = Path(target)

        try:
            if target_path.exists() and target_path.suffix in ['.py', '.js', '.ts']:
                # Generate OpenAPI from code
                return await self._generate_openapi_from_code(context, target, file_ops, format_type, server_url, api_title, api_version)
            else:
                # Generate documentation from existing spec
                return await self._enhance_openapi_spec(context, target, file_ops, format_type, server_url, api_title, api_version)

        except Exception as e:
            return f"Error generating API docs: {e}"

    async def _generate_openapi_from_code(self, context: CommandContext, filename: str, file_ops: FileOperations, format_type: str, server_url: str, api_title: str, api_version: str) -> str:
        """Generate OpenAPI spec from code."""
        content = await file_ops.read_file(filename)
        language = file_ops.detect_language(filename)

        prompt = f"""Generate OpenAPI {format_type.upper()} specification from this {language} API code:

Requirements:
- Server URL: {server_url}
- API Title: {api_title}
- Version: {api_version}
- Include all endpoints with proper HTTP methods
- Define request/response schemas
- Add authentication if present
- Include parameter descriptions
- Add example responses

Code:
```{language}
{content}
```

Generate a complete OpenAPI {format_type.upper()} specification."""

        response = await context.provider.client.send_request([
            {"role": "system", "content": "You are an API documentation expert. Generate accurate OpenAPI specifications from code.",
                 "name": "OpenAPIGenerator"},
            {"role": "user", "content": prompt}
        ])

        spec_content = response.content.strip()

        # Save to file
        output_file = f"{Path(filename).stem}_openapi.{format_type}"
        await file_ops.write_file(output_file, spec_content)

        return f"""📚 OpenAPI {format_type.upper()} generated!
- Input: {filename}
- Output: {output_file}

Preview:
{spec_content[:500]}..."""

    async def _enhance_openapi_spec(self, context: CommandContext, spec_file: str, file_ops: FileOperations, format_type: str, server_url: str, api_title: str, api_version: str) -> str:
        """Enhance existing OpenAPI spec."""
        content = await file_ops.read_file(spec_file)

        prompt = f"""Enhance this OpenAPI specification:

Requirements:
- Format: {format_type}
- Server URL: {server_url}
- API Title: {api_title}
- Version: {api_version}
- Add missing descriptions
- Include example values
- Validate the specification
- Add common headers if missing

Current spec:
{content}"""

        response = await context.provider.client.send_request([
            {"role": "system", "content": "You are an OpenAPI expert. Enhance specifications with missing details and best practices.",
                 "name": "OpenAPIEnhancer"},
            {"role": "user", "content": prompt}
        ])

        enhanced_content = response.content.strip()

        # Save enhanced spec
        output_file = Path(spec_file).stem + f"_enhanced.{format_type}"
        await file_ops.write_file(output_file, enhanced_content)

        return f"""📚 OpenAPI specification enhanced!
- Input: {spec_file}
- Output: {output_file}

Preview:
{enhanced_content[:500]}..."""


class READMECommand(SlashCommand):
    """Generate README.md for projects."""

    def __init__(self):
        super().__init__(
            name="readme",
            description="Generate README.md for project",
            aliases=["generate-readme"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the readme command."""
        file_ops = FileOperations(context.working_directory)

        # Collect project information
        project_info = await self._analyze_project(context, file_ops)

        prompt = f"""Generate a comprehensive README.md for this project:

Project Information:
{json.dumps(project_info, indent=2)}

Requirements:
1. Project title and description
2. Installation instructions
3. Usage examples
4. API documentation (if applicable)
5. Contributing guidelines
6. License information
7. Badges for build status, coverage, etc.
8. Table of contents
9. Features list
10. Requirements/dependencies

Generate a professional, well-structured README.md"""

        response = await context.provider.client.send_request([
            {"role": "system", "content": "You are a technical writer who creates professional README files. Include markdown formatting, code blocks, and proper structure.",
                 "name": "READMEGenerator"},
            {"role": "user", "content": prompt}
        ])

        readme_content = response.content.strip()

        # Save README
        await file_ops.write_file("README.md", readme_content)

        return f"""📄 README.md generated successfully!

Content preview:
{readme_content[:800]}...

Saved to: README.md"""

    async def _analyze_project(self, context: CommandContext, file_ops: FileOperations) -> dict:
        """Analyze project structure and files."""
        info = {
            "name": Path(context.working_directory).name,
            "files": [],
            "languages": set(),
            "has_tests": False,
            "has_ci": False,
            "has_docs": False,
            "package_manager": None,
            "framework": None,
            "dependencies": []
        }

        # Scan project directory
        for item in Path(context.working_directory).iterdir():
            if item.is_file():
                info["files"].append(item.name)

                # Detect package manager
                if item.name == "package.json":
                    info["package_manager"] = "npm/yarn"
                    # Parse dependencies
                    try:
                        content = await file_ops.read_file(str(item))
                        import json
                        pkg_data = json.loads(content)
                        deps = list(pkg_data.get("dependencies", {}).keys())
                        info["dependencies"].extend(deps[:5])  # Limit to 5
                    except:
                        pass
                elif item.name == "requirements.txt":
                    info["package_manager"] = "pip"
                elif item.name in ["pyproject.toml", "Pipfile", "poetry.lock"]:
                    info["package_manager"] = "poetry/pipenv"
                elif item.name == "Cargo.toml":
                    info["package_manager"] = "cargo"
                elif item.name in ["pom.xml", "build.gradle"]:
                    info["package_manager"] = "maven/gradle"

                # Detect frameworks
                if "fastapi" in item.name.lower() or item.name == "main.py":
                    content = await file_ops.read_file(str(item))
                    if "FastAPI" in content:
                        info["framework"] = "FastAPI"
                    elif "Flask" in content:
                        info["framework"] = "Flask"
                    elif "Django" in content:
                        info["framework"] = "Django"

                # Detect language
                ext = item.suffix.lower()
                if ext == ".py":
                    info["languages"].add("Python")
                elif ext in [".js", ".ts", ".jsx", ".tsx"]:
                    info["languages"].add("JavaScript/TypeScript")
                elif ext == ".java":
                    info["languages"].add("Java")
                elif ext in [".c", ".cpp", ".h", ".hpp"]:
                    info["languages"].add("C/C++")
                elif ext == ".go":
                    info["languages"].add("Go")
                elif ext == ".rs":
                    info["languages"].add("Rust")

            elif item.is_dir():
                # Check for special directories
                if item.name == "tests" or item.name == "test":
                    info["has_tests"] = True
                elif item.name == ".github":
                    info["has_ci"] = True
                elif item.name == "docs":
                    info["has_docs"] = True

        info["languages"] = list(info["languages"])

        return info


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(DocsCommand())
command_registry.register(ApiDocsCommand())
command_registry.register(READMECommand())

def register():
    """Register all documentation commands."""
    return [
        DocsCommand(),
        ApiDocsCommand(),
        READMECommand(),
    ]