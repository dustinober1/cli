"""Template engine for generating code from templates."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional


@dataclass
class TemplateInfo:
    """Information about a template."""

    name: str
    description: str
    category: str
    language: str
    variables: List[str]
    file_path: str


class TemplateEngine:
    """Template engine for code generation."""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template engine."""
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Default to user's .vibe/templates directory
            self.template_dir = Path.home() / ".vibe" / "templates"

        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, TemplateInfo]:
        """Load all available templates."""
        templates = {}

        # Load built-in templates
        builtin_templates = self._get_builtin_templates()
        templates.update(builtin_templates)

        # Load user templates from directory
        if self.template_dir.exists():
            for template_file in self.template_dir.rglob("*.template"):
                try:
                    template_info = self._parse_template_file(template_file)
                    if template_info:
                        templates[template_info.name] = template_info
                except Exception:
                    continue

        return templates

    def _get_builtin_templates(self) -> Dict[str, TemplateInfo]:
        """Get built-in templates."""
        templates = {}

        # Python templates
        templates["python_class"] = TemplateInfo(
            name="python_class",
            description="Python class with methods",
            category="python",
            language="python",
            variables=["class_name", "base_class", "methods"],
            file_path="",
        )

        templates["python_function"] = TemplateInfo(
            name="python_function",
            description="Python function with type hints",
            category="python",
            language="python",
            variables=["function_name", "params", "return_type", "docstring"],
            file_path="",
        )

        templates["python_async"] = TemplateInfo(
            name="python_async",
            description="Python async function",
            category="python",
            language="python",
            variables=["function_name", "params", "return_type", "docstring"],
            file_path="",
        )

        # JavaScript templates
        templates["js_function"] = TemplateInfo(
            name="js_function",
            description="JavaScript function",
            category="javascript",
            language="javascript",
            variables=["function_name", "params", "docstring"],
            file_path="",
        )

        templates["js_class"] = TemplateInfo(
            name="js_class",
            description="JavaScript ES6 class",
            category="javascript",
            language="javascript",
            variables=["class_name", "constructor_params", "methods"],
            file_path="",
        )

        templates["react_component"] = TemplateInfo(
            name="react_component",
            description="React functional component",
            category="react",
            language="javascript",
            variables=["component_name", "props", "hooks"],
            file_path="",
        )

        # Web templates
        templates["html_page"] = TemplateInfo(
            name="html_page",
            description="HTML5 page structure",
            category="web",
            language="html",
            variables=["title", "meta_tags", "body_content"],
            file_path="",
        )

        templates["css_class"] = TemplateInfo(
            name="css_class",
            description="CSS class definition",
            category="web",
            language="css",
            variables=["class_name", "properties"],
            file_path="",
        )

        # API templates
        templates["api_endpoint"] = TemplateInfo(
            name="api_endpoint",
            description="REST API endpoint",
            category="api",
            language="python",
            variables=["endpoint_name", "method", "path", "request_model", "response_model"],
            file_path="",
        )

        templates["api_client"] = TemplateInfo(
            name="api_client",
            description="API client class",
            category="api",
            language="python",
            variables=["service_name", "base_url", "methods"],
            file_path="",
        )

        # Database templates
        templates["sql_table"] = TemplateInfo(
            name="sql_table",
            description="SQL table definition",
            category="database",
            language="sql",
            variables=["table_name", "columns", "constraints"],
            file_path="",
        )

        templates["sql_query"] = TemplateInfo(
            name="sql_query",
            description="SQL query with parameters",
            category="database",
            language="sql",
            variables=["query_type", "table_name", "columns", "conditions"],
            file_path="",
        )

        return templates

    def _parse_template_file(self, file_path: Path) -> Optional[TemplateInfo]:
        """Parse a template file and extract metadata."""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract metadata from comments at top of file
            lines = content.split("\n")
            metadata = {}
            template_start = 0

            for i, line in enumerate(lines):
                if line.strip().startswith("#"):
                    key_value = line.strip()[1:].strip().split(":", 1)
                    if len(key_value) == 2:
                        metadata[key_value[0].strip().lower()] = key_value[1].strip()
                    template_start = i + 1
                elif line.strip() and not line.strip().startswith("#"):
                    break

            # Extract template content
            template_content = "\n".join(lines[template_start:])

            # Create template info
            template_info = TemplateInfo(
                name=metadata.get("name", file_path.stem),
                description=metadata.get("description", f"Template from {file_path.name}"),
                category=metadata.get("category", "custom"),
                language=metadata.get("language", "text"),
                variables=self._extract_variables(template_content),
                file_path=str(file_path),
            )

            # Store template content
            template_info.content = template_content
            return template_info

        except Exception:
            return None

    def _extract_variables(self, template: str) -> List[str]:
        """Extract variables from template string."""
        import re

        # Find ${variable} patterns
        variables = re.findall(r"\$\{([^}]+)\}", template)
        return list(set(variables))

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a template with provided variables."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template_info = self.templates[template_name]

        # Get template content
        if hasattr(template_info, "content"):
            template_content = template_info.content
        else:
            # Use built-in template
            template_content = self._get_builtin_template_content(template_name)

        # Create template and substitute variables
        template = Template(template_content)

        try:
            rendered = template.safe_substitute(variables)
            return rendered
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")

    def _get_builtin_template_content(self, template_name: str) -> str:
        """Get content for built-in templates."""
        builtin_contents = {
            "python_class": '''class ${class_name}(${base_class}):
    """${class_name} class implementation."""

    def __init__(self${', ' + ', '.join([f'${p}' for p in filter(None, ['constructor_params'])]) if 'constructor_params' in locals() else ''}):
        """Initialize ${class_name}.")
        super().__init__()
        ${initialization_code}

    ${methods}
''',
            "python_function": '''def ${function_name}(${params}) -> ${return_type}:
    """${docstring}

    Args:
        ${args_doc}

    Returns:
        ${return_type}: ${return_description}
    """
    ${function_body}
''',
            "python_async": '''async def ${function_name}(${params}) -> ${return_type}:
    """${docstring}

    Args:
        ${args_doc}

    Returns:
        ${return_type}: ${return_description}
    """
    ${function_body}
''',
            "js_function": """/**
 * ${docstring}
 * ${params_doc}
 * @returns {$return_type}
 */
function ${function_name}(${params}) {
    ${function_body}
}
""",
            "js_class": """class ${class_name} {
    /**
     * Constructor for ${class_name}
     * @param {${constructor_params}}
     */
    constructor(${constructor_params}) {
        ${constructor_body}
    }

    ${methods}
}
""",
            "react_component": """import React from 'react';

/**
 * ${component_name} component
 * ${props_doc}
 */
const ${component_name} = (${props}) => {
    ${hooks}

    return (
        ${jsx_content}
    );
};

export default ${component_name};
""",
            "html_page": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    ${meta_tags}
    ${styles}
</head>
<body>
    ${body_content}
    ${scripts}
</body>
</html>
""",
            "css_class": """.${class_name} {
    ${properties}
}
""",
            "api_endpoint": '''@${method.lower()}("${path}")
async def ${endpoint_name}(
    request: ${request_model},
    db: Session = Depends(get_db)
) -> ${response_model}:
    """
    ${description}
    """
    ${endpoint_logic}
''',
            "api_client": '''class ${service_name}Client:
    """Client for ${service_name} API."""

    def __init__(self, base_url: str = "${base_url}"):
        self.base_url = base_url
        self.session = httpx.Client()

    ${methods}

    async def close(self):
        """Close the client session."""
        await self.session.aclose()
''',
            "sql_table": """CREATE TABLE ${table_name} (
    ${columns}
    ${constraints}
);
""",
            "sql_query": """${query_type} ${columns}
FROM ${table_name}
${conditions}
${additional_clauses};
""",
        }

        return builtin_contents.get(template_name, "")

    def list_templates(
        self, category: Optional[str] = None, language: Optional[str] = None
    ) -> List[TemplateInfo]:
        """List available templates with optional filters."""
        templates = list(self.templates.values())

        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]
        if language:
            templates = [t for t in templates if t.language == language]

        # Sort by name
        templates.sort(key=lambda x: x.name)
        return templates

    def create_template(
        self, name: str, content: str, description: str, category: str, language: str
    ) -> str:
        """Create a new template."""
        template_info = TemplateInfo(
            name=name,
            description=description,
            category=category,
            language=language,
            variables=self._extract_variables(content),
            file_path="",
        )

        # Create template file
        template_file = self.template_dir / f"{name}.template"

        # Add metadata header
        file_content = f"""# Name: {name}
# Description: {description}
# Category: {category}
# Language: {language}

{content}"""

        with open(template_file, "w") as f:
            f.write(file_content)

        # Add to templates
        template_info.file_path = str(template_file)
        template_info.content = content
        self.templates[name] = template_info

        return f"Template '{name}' created at {template_file}"

    def delete_template(self, name: str) -> str:
        """Delete a template."""
        if name not in self.templates:
            return f"Template '{name}' not found"

        template_info = self.templates[name]

        # Remove file if it exists
        if template_info.file_path and Path(template_info.file_path).exists():
            Path(template_info.file_path).unlink()

        # Remove from templates
        del self.templates[name]

        return f"Template '{name}' deleted"

    def get_template_info(self, name: str) -> Optional[TemplateInfo]:
        """Get information about a template."""
        return self.templates.get(name)

    def export_template(self, name: str, file_path: str) -> str:
        """Export a template to a file."""
        if name not in self.templates:
            return f"Template '{name}' not found"

        template_info = self.templates[name]

        # Get template content
        if hasattr(template_info, "content"):
            content = template_info.content
        else:
            content = self._get_builtin_template_content(name)

        # Export with metadata
        export_data = {
            "name": template_info.name,
            "description": template_info.description,
            "category": template_info.category,
            "language": template_info.language,
            "variables": template_info.variables,
            "content": content,
        }

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return f"Template '{name}' exported to {file_path}"

    def import_template(self, file_path: str) -> str:
        """Import a template from a file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["name", "content"]
            for field in required_fields:
                if field not in data:
                    return f"Missing required field: {field}"

            # Create template
            return self.create_template(
                name=data["name"],
                content=data["content"],
                description=data.get("description", ""),
                category=data.get("category", "imported"),
                language=data.get("language", "text"),
            )

        except Exception as e:
            return f"Error importing template: {e}"

    def generate_from_schema(self, schema: Dict[str, Any], template_name: str) -> str:
        """Generate code from a schema using a template."""
        # This would parse the schema and generate appropriate variables
        # For now, just pass the schema as variables
        variables = {}

        # Flatten schema for template substitution
        def flatten_dict(d, parent_key=""):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}_{i}").items())
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    items.append((new_key, v))
            return dict(items)

        variables = flatten_dict(schema)

        return self.render_template(template_name, variables)
