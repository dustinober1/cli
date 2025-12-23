"""Specialized code manipulation slash commands."""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class InterfaceCommand(SlashCommand):
    """Extract interfaces/contracts from code."""

    def __init__(self):
        super().__init__(
            name="interface",
            description="Extract interfaces/contracts from code",
            aliases=["extract-abi", "contracts"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the interface command."""
        if not args:
            return """Usage: /interface <filename> [options]
Options:
- --language <lang>: Target language for interface (typescript, java, csharp, etc.)
- --format <type>: Output format (interface, abstract, protocol)
- --include-private: Include private methods/properties
- --output <file>: Save to specific file

Examples:
- /interface app.py
- /interface user.py --language typescript
- /interface models.py --format abstract --output interfaces.py"""

        filename = args[0]
        options = {arg[2:]: True for arg in args[1:] if arg.startswith("--")}

        language = options.get("language", "typescript")
        format_type = options.get("format", "interface")
        include_private = options.get("include-private", False)
        output_file = options.get("output")

        file_ops = FileOperations(context.working_directory)

        try:
            content = await file_ops.read_file(filename)
            source_lang = file_ops.detect_language(filename)

            # Parse the file based on language
            if source_lang == "python":
                interfaces = await self._extract_python_interfaces(content, include_private)
            elif source_lang in ["javascript", "typescript"]:
                interfaces = await self._extract_js_interfaces(content, include_private)
            elif source_lang == "java":
                interfaces = await self._extract_java_interfaces(content, include_private)
            else:
                return f"❌ Unsupported language: {source_lang}"

            if not interfaces:
                return f"✅ No interfaces found in {filename}"

            # Generate target language code
            generated = await self._generate_interfaces(interfaces, language, format_type, context)

            # Save if output file specified
            if output_file:
                await file_ops.write_file(output_file, generated)
                return f"📄 Interfaces saved to {output_file}\n\nPreview:\n{generated[:500]}..."

            return f"""🔧 Extracted Interfaces from {filename}

{generated}"""

        except Exception as e:
            return f"Error extracting interfaces: {e}"

    async def _extract_python_interfaces(self, content: str, include_private: bool) -> List[Dict]:
        """Extract interfaces from Python code."""
        try:
            tree = ast.parse(content)
            interfaces = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = []
                    properties = []

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Skip private methods unless requested
                            if not include_private and item.name.startswith("_"):
                                continue

                            # Extract method signature
                            args = []
                            for arg in item.args.args[1:]:  # Skip self
                                args.append(arg.arg)

                            returns = None
                            if item.returns:
                                returns = (
                                    ast.unparse(item.returns) if hasattr(ast, "unparse") else "Any"
                                )

                            methods.append(
                                {
                                    "name": item.name,
                                    "args": args,
                                    "returns": returns,
                                    "doc": ast.get_docstring(item),
                                    "async": isinstance(item, ast.AsyncFunctionDef),
                                }
                            )

                        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            # Property with type annotation
                            if not include_private and item.target.id.startswith("_"):
                                continue
                            properties.append(
                                {
                                    "name": item.target.id,
                                    "type": (
                                        ast.unparse(item.annotation)
                                        if hasattr(ast, "unparse")
                                        else "Any"
                                    ),
                                }
                            )

                    interfaces.append(
                        {
                            "name": node.name,
                            "methods": methods,
                            "properties": properties,
                            "doc": ast.get_docstring(node),
                            "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                        }
                    )

            return interfaces

        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

    async def _extract_js_interfaces(self, content: str, include_private: bool) -> List[Dict]:
        """Extract interfaces from JavaScript/TypeScript code."""
        # Simple regex-based extraction for JS/TS
        interfaces = []

        # Find classes
        class_pattern = r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            base_class = match.group(2)

            # Extract methods (simplified)
            method_pattern = (
                r"(?:async\s+)?(?:public|private|protected)?\s*(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?"
            )
            methods = []

            # Find methods within this class (simplified)
            class_start = match.start()
            brace_count = 0
            class_end = len(content)

            for i, char in enumerate(content[class_start:], class_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break

            class_content = content[class_start:class_end]
            for method_match in re.finditer(method_pattern, class_content):
                method_name = method_match.group(1)
                if not include_private and method_name.startswith("_"):
                    continue
                methods.append(
                    {
                        "name": method_name,
                        "args": [
                            arg.strip() for arg in method_match.group(2).split(",") if arg.strip()
                        ],
                        "returns": method_match.group(3) or "void",
                    }
                )

            interfaces.append(
                {
                    "name": class_name,
                    "methods": methods,
                    "properties": [],
                    "doc": None,
                    "bases": [base_class] if base_class else [],
                }
            )

        return interfaces

    async def _extract_java_interfaces(self, content: str, include_private: bool) -> List[Dict]:
        """Extract interfaces from Java code."""
        # Simplified Java interface extraction
        interfaces = []

        # Find interfaces and classes
        pattern = r"(?:public\s+)?(interface|class)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?"
        for match in re.finditer(pattern, content):
            type_type = match.group(1)
            name = match.group(2)
            extends = match.group(3)
            implements = match.group(4).split(", ") if match.group(4) else []

            # Extract methods
            methods = []
            method_pattern = r"(?:public|private|protected)?\s*(?:static\s+)?(?:abstract\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)(?:\s+throws\s+([^{]+))?"

            # Get the class/interface body
            start = match.end()
            brace_count = 0
            end = len(content)

            for i, char in enumerate(content[start:], start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break

            body = content[start:end]

            for method_match in re.finditer(method_pattern, body):
                return_type = method_match.group(1)
                method_name = method_match.group(2)
                if not include_private and method_name.startswith("_"):
                    continue

                args = []
                if method_match.group(3):
                    for arg in method_match.group(3).split(","):
                        arg = arg.strip()
                        if arg:
                            parts = arg.split()
                            if len(parts) >= 2:
                                args.append(parts[-1])

                methods.append(
                    {"name": method_name, "args": args, "returns": return_type, "doc": None}
                )

            interfaces.append(
                {
                    "name": name,
                    "methods": methods,
                    "properties": [],
                    "doc": None,
                    "bases": [extends] if extends else implements,
                }
            )

        return interfaces

    async def _generate_interfaces(
        self, interfaces: List[Dict], language: str, format_type: str, context: CommandContext
    ) -> str:
        """Generate interface code in target language."""

        prompt = f"""Generate {language} {format_type} definitions from these extracted interfaces:

Interfaces:
{interfaces}

Requirements:
1. Language: {language}
2. Format: {format_type}
3. Include proper type annotations
4. Add documentation comments
5. Follow {language} conventions
6. Handle inheritance relationships
7. Include method signatures with proper types

Generate clean, production-ready {language} code."""

        response = await context.provider.client.send_request(
            [
                {
                    "role": "system",
                    "content": f"You are an expert {language} developer. Generate idiomatic, type-safe interface definitions.",
                    "name": "InterfaceGenerator",
                },
                {"role": "user", "content": prompt},
            ]
        )

        return response.content.strip()


class SchemaCommand(SlashCommand):
    """Generate database schemas from models."""

    def __init__(self):
        super().__init__(
            name="schema",
            description="Generate database schemas from models",
            aliases=["db-schema", "model-schema"],
            category="code",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the schema command."""
        if not args:
            return """Usage: /schema <model_file> [options]
Options:
- --database <type>: Target database (postgresql, mysql, sqlite, mongodb)
- --orm <framework>: ORM framework (sqlalchemy, django, sqlalchemy-core, prisma)
- --output <file>: Output file for schema
- --migrations: Generate migration scripts
- --indexes: Add index suggestions

Examples:
- /schema models.py
- /schema user.py --database postgresql --orm sqlalchemy
- /schema models.py --database mongodb --orm django --migrations"""

        filename = args[0]
        options = {arg[2:]: True for arg in args[1:] if arg.startswith("--")}

        database = options.get("database", "postgresql")
        orm = options.get("orm", "sqlalchemy")
        output_file = options.get("output")
        migrations = options.get("migrations", False)
        indexes = options.get("indexes", False)

        file_ops = FileOperations(context.working_directory)

        try:
            content = await file_ops.read_file(filename)
            language = file_ops.detect_language(filename)

            # Extract models from code
            if language == "python":
                models = await self._extract_python_models(content)
            elif language == "javascript":
                models = await self._extract_js_models(content)
            else:
                return f"❌ Unsupported language: {language}"

            if not models:
                return f"✅ No models found in {filename}"

            # Generate database schema
            schema = await self._generate_database_schema(
                models, database, orm, migrations, indexes, context
            )

            # Save if output file specified
            if output_file:
                await file_ops.write_file(output_file, schema)
                return f"📄 Schema saved to {output_file}\n\nPreview:\n{schema[:500]}..."

            return f"""🗄️ Database Schema for {filename}

Target: {database} with {orm}
Migrations: {'Yes' if migrations else 'No'}
Indexes: {'Yes' if indexes else 'No'}

{schema}"""

        except Exception as e:
            return f"Error generating schema: {e}"

    async def _extract_python_models(self, content: str) -> List[Dict]:
        """Extract database models from Python code."""
        try:
            tree = ast.parse(content)
            models = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's likely a model (has specific attributes or inherits from certain classes)
                    fields = []
                    relationships = []

                    for item in node.body:
                        if isinstance(item, ast.AnnAssign):
                            if isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                field_type = (
                                    ast.unparse(item.annotation)
                                    if hasattr(ast, "unparse")
                                    else "Any"
                                )
                                default = None

                                if item.value:
                                    default = (
                                        ast.unparse(item.value)
                                        if hasattr(ast, "unparse")
                                        else str(item.value)
                                    )

                                fields.append(
                                    {
                                        "name": field_name,
                                        "type": field_type,
                                        "default": default,
                                        "nullable": default is None or "Optional" in field_type,
                                    }
                                )

                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    field_name = target.id
                                    field_type = "Any"
                                    default = (
                                        ast.unparse(item.value)
                                        if hasattr(ast, "unparse")
                                        else str(item.value)
                                    )

                                    fields.append(
                                        {
                                            "name": field_name,
                                            "type": field_type,
                                            "default": default,
                                            "nullable": False,
                                        }
                                    )

                    models.append(
                        {
                            "name": node.name,
                            "fields": fields,
                            "relationships": relationships,
                            "doc": ast.get_docstring(node),
                            "table_name": node.name.lower(),
                        }
                    )

            return models

        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

    async def _extract_js_models(self, content: str) -> List[Dict]:
        """Extract models from JavaScript/TypeScript code."""
        models = []

        # Simple regex-based model extraction
        # Look for class definitions with typical model fields
        class_pattern = r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{"

        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)

            # Get class body
            start = match.end()
            brace_count = 0
            end = len(content)

            for i, char in enumerate(content[start:], start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break

            body = content[start:end]

            # Extract properties
            fields = []
            prop_pattern = (
                r"(?:public|private|protected)?\s*(\w+(?:\??\s*:\s*[^;=]+)?)(?:\s*=\s*([^;]+))?;"
            )

            for prop_match in re.finditer(prop_pattern, body):
                field_def = prop_match.group(1)
                default = prop_match.group(2)

                if ":" in field_def:
                    field_name, field_type = field_def.split(":", 1)
                    field_name = field_name.strip()
                    field_type = field_type.strip()
                else:
                    field_name = field_def
                    field_type = "any"

                fields.append(
                    {
                        "name": field_name,
                        "type": field_type,
                        "default": default.strip() if default else None,
                        "nullable": "?" in field_def,
                    }
                )

            if fields:  # Only add if has fields
                models.append(
                    {
                        "name": class_name,
                        "fields": fields,
                        "relationships": [],
                        "doc": None,
                        "table_name": class_name.lower(),
                    }
                )

        return models

    async def _generate_database_schema(
        self,
        models: List[Dict],
        database: str,
        orm: str,
        migrations: bool,
        indexes: bool,
        context: CommandContext,
    ) -> str:
        """Generate database schema code."""

        prompt = f"""Generate {database} database schema using {orm} ORM from these models:

Models:
{models}

Requirements:
1. Database: {database}
2. ORM: {orm}
3. Generate migration scripts: {migrations}
4. Include index suggestions: {indexes}
5. Handle relationships properly
6. Add constraints and indexes
7. Follow {orm} best practices
8. Include table definitions
9. Handle data types properly for {database}

Generate complete, production-ready database schema code."""

        response = await context.provider.client.send_request(
            [
                {
                    "role": "system",
                    "content": f"You are a database expert specializing in {orm} and {database}. Generate proper schemas with relationships, constraints, and optimizations.",
                    "name": "DatabaseSchemaGenerator",
                },
                {"role": "user", "content": prompt},
            ]
        )

        return response.content.strip()


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(InterfaceCommand())
command_registry.register(SchemaCommand())


def register():
    """Register all specialized code commands."""
    return [
        InterfaceCommand(),
        SchemaCommand(),
    ]
