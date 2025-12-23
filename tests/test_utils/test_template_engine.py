"""Tests for the TemplateEngine class."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from vibe_coder.utils.template_engine import TemplateEngine, TemplateInfo


class TestTemplateEngineInitialization:
    """Test TemplateEngine initialization."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_init_default_dir(self, mock_exists, mock_mkdir):
        """Test initialization with default directory."""
        mock_exists.return_value = False

        engine = TemplateEngine()

        assert str(engine.template_dir).endswith(".vibe/templates")
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch("pathlib.Path.mkdir")
    def test_init_custom_dir(self, mock_mkdir):
        """Test initialization with custom directory."""
        custom_dir = "/custom/templates"
        engine = TemplateEngine(template_dir=custom_dir)

        assert str(engine.template_dir) == custom_dir
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)


class TestLoadTemplates:
    """Test template loading."""

    @patch("pathlib.Path.mkdir")
    def test_load_builtin_templates(self, mock_mkdir):
        """Test loading built-in templates."""
        engine = TemplateEngine()

        # Should have built-in templates
        assert "python_class" in engine.templates
        assert "python_function" in engine.templates
        assert "js_function" in engine.templates
        assert "html_page" in engine.templates
        assert "api_endpoint" in engine.templates
        assert "sql_table" in engine.templates

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.rglob")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""# Name: Custom Template
# Description: A custom template
# Category: custom
# Language: python

def ${function_name}():
    ${body}
""",
    )
    def test_load_user_templates(self, mock_exists, mock_rglob, mock_mkdir, mock_file):
        """Test loading user templates."""
        mock_exists.return_value = True
        mock_file_path = MagicMock()
        mock_file_path.name = "custom.template"
        mock_file_path.stem = "custom"
        mock_rglob.return_value = [mock_file_path]

        engine = TemplateEngine()

        # Should have custom template
        assert "custom" in engine.templates
        custom = engine.templates["custom"]
        assert custom.name == "custom"
        assert custom.category == "custom"
        assert custom.language == "python"
        assert "function_name" in custom.variables
        assert "body" in custom.variables

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.rglob")
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_load_user_templates_error(self, mock_open, mock_rglob, mock_exists, mock_mkdir):
        """Test handling errors when loading user templates."""
        mock_exists.return_value = True
        mock_file_path = MagicMock()
        mock_file_path.name = "error.template"
        mock_rglob.return_value = [mock_file_path]

        engine = TemplateEngine()

        # Should still have built-in templates despite error
        assert "python_class" in engine.templates


class TestParseTemplateFile:
    """Test template file parsing."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='''# Name: Test Template
# Description: A test template
# Category: test
# Language: python
# Author: Test Author

def ${function_name}(${params}):
    """${docstring}"""
    return ${return_value}
''',
    )
    def test_parse_template_file_with_metadata(self, mock_file):
        """Test parsing template file with metadata."""
        engine = TemplateEngine()
        file_path = Path("/path/to/test.template")

        result = engine._parse_template_file(file_path)

        assert result is not None
        assert result.name == "Test Template"
        assert result.description == "A test template"
        assert result.category == "test"
        assert result.language == "python"
        assert "function_name" in result.variables
        assert "params" in result.variables
        assert "docstring" in result.variables
        assert "return_value" in result.variables
        assert str(file_path) == result.file_path

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""def ${function_name}():
    return "Hello, ${name}!"
""",
    )
    def test_parse_template_file_no_metadata(self, mock_file):
        """Test parsing template file without metadata."""
        engine = TemplateEngine()
        file_path = Path("/path/to/test.template")

        result = engine._parse_template_file(file_path)

        assert result is not None
        assert result.name == "test"
        assert result.description == "Template from test.template"
        assert result.category == "custom"
        assert result.language == "text"
        assert "function_name" in result.variables
        assert "name" in result.variables

    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_parse_template_file_error(self, mock_open):
        """Test handling errors when parsing template file."""
        engine = TemplateEngine()
        file_path = Path("/path/to/error.template")

        result = engine._parse_template_file(file_path)

        assert result is None


class TestExtractVariables:
    """Test variable extraction from templates."""

    def test_extract_variables(self):
        """Test extracting ${variable} patterns."""
        engine = TemplateEngine()

        template = '''
def ${function_name}(${param1}, ${param2}):
    """${docstring}"""
    ${variable_name} = ${default_value}
    return ${variable_name}
'''
        variables = engine._extract_variables(template)

        expected = {
            "function_name",
            "param1",
            "param2",
            "docstring",
            "variable_name",
            "default_value",
        }
        assert set(variables) == expected

    def test_extract_variables_no_duplicates(self):
        """Test that duplicate variables are not included."""
        engine = TemplateEngine()

        template = """
${name} = "${name}"
print(${name})
"""
        variables = engine._extract_variables(template)

        assert variables == ["name"]

    def test_extract_variables_empty(self):
        """Test extracting variables from template with no variables."""
        engine = TemplateEngine()

        template = """
def function():
    return "Hello, World!"
"""
        variables = engine._extract_variables(template)

        assert variables == []

    def test_extract_variables_nested_patterns(self):
        """Test extracting variables with nested braces."""
        engine = TemplateEngine()

        template = """
console.log("${prefix}: ${message}");
"""
        variables = engine._extract_variables(template)

        assert set(variables) == {"prefix", "message"}

    def test_extract_variables_edge_cases(self):
        """Test edge cases in variable extraction."""
        engine = TemplateEngine()

        # Incomplete patterns
        template1 = "${variable"
        assert engine._extract_variables(template1) == []

        # Empty variable name
        template2 = "${}"
        assert engine._extract_variables(template2) == []

        # Multiple braces
        template3 = "${var${nested}}"
        # regex will match 'var${nested' as one variable name
        result = engine._extract_variables(template3)
        assert "var${nested" in result


class TestRenderTemplate:
    """Test template rendering."""

    @patch("pathlib.Path.mkdir")
    def test_render_builtin_template(self, mock_mkdir):
        """Test rendering built-in template."""
        engine = TemplateEngine()

        result = engine.render_template(
            "python_function",
            {
                "function_name": "greet",
                "params": "name: str",
                "return_type": "str",
                "docstring": "Greet someone by name",
                "args_doc": "name: The name to greet",
                "return_description": "A greeting message",
                "function_body": 'return f"Hello, {name}!"',
            },
        )

        assert "def greet(name: str) -> str:" in result
        assert "Greet someone by name" in result
        assert 'return f"Hello, {name}!"' in result

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.rglob")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""# Name: Custom
# Description: Custom template
# Category: custom
# Language: python

def ${func}():
    return ${value}
""",
    )
    def test_render_user_template(self, mock_file, mock_rglob, mock_exists, mock_mkdir):
        """Test rendering user template."""
        mock_exists.return_value = True
        mock_file_path = MagicMock()
        mock_file_path.name = "custom.template"
        mock_file_path.stem = "custom"
        mock_rglob.return_value = [mock_file_path]

        engine = TemplateEngine()

        result = engine.render_template("custom", {"func": "test", "value": "42"})

        assert "def test():" in result
        assert "return 42" in result

    @patch("pathlib.Path.mkdir")
    def test_render_template_not_found(self, mock_mkdir):
        """Test rendering non-existent template."""
        engine = TemplateEngine()

        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            engine.render_template("nonexistent", {})

    @patch("pathlib.Path.mkdir")
    def test_render_template_missing_variable(self, mock_mkdir):
        """Test rendering template with missing variable."""
        engine = TemplateEngine()

        with pytest.raises(ValueError, match="Missing required variable"):
            engine.render_template(
                "python_function",
                {
                    "function_name": "test"
                    # Missing other required variables
                },
            )

    @patch("pathlib.Path.mkdir")
    def test_render_template_partial_substitution(self, mock_mkdir):
        """Test template with partial variable substitution."""
        engine = TemplateEngine()

        result = engine.render_template(
            "python_function",
            {
                "function_name": "test",
                "params": "",
                "return_type": "None",
                "docstring": "Test function",
                "args_doc": "",
                "return_description": "",
                "function_body": "pass",
                "other_var": "This will not be used",
            },
        )

        # Should substitute known variables, leave unknown as-is
        assert "def test() -> None:" in result
        assert "${other_var}" not in result

    @patch("pathlib.Path.mkdir")
    def test_render_template_special_chars(self, mock_mkdir):
        """Test rendering template with special characters in variables."""
        engine = TemplateEngine()

        result = engine.render_template(
            "python_function",
            {
                "function_name": "test",
                "params": 'name: str = "World"',
                "return_type": "str",
                "docstring": "Test with 'quotes' and \\${} syntax",
                "args_doc": "",
                "return_description": "",
                "function_body": 'return f"Hello, {name}"',
            },
        )

        assert 'name: str = "World"' in result
        assert "Test with 'quotes'" in result


class TestListTemplates:
    """Test template listing."""

    @patch("pathlib.Path.mkdir")
    def test_list_templates_all(self, mock_mkdir):
        """Test listing all templates."""
        engine = TemplateEngine()

        templates = engine.list_templates()

        assert len(templates) > 0
        template_names = [t.name for t in templates]
        assert "python_class" in template_names
        assert "js_function" in template_names
        assert "html_page" in template_names

    @patch("pathlib.Path.mkdir")
    def test_list_templates_by_category(self, mock_mkdir):
        """Test listing templates by category."""
        engine = TemplateEngine()

        python_templates = engine.list_templates(category="python")
        web_templates = engine.list_templates(category="web")
        api_templates = engine.list_templates(category="api")

        # Check categories
        assert all(t.category == "python" for t in python_templates)
        assert all(t.category == "web" for t in web_templates)
        assert all(t.category == "api" for t in api_templates)

        # Python templates should include python_class and python_function
        python_names = [t.name for t in python_templates]
        assert "python_class" in python_names
        assert "python_function" in python_names

    @patch("pathlib.Path.mkdir")
    def test_list_templates_by_language(self, mock_mkdir):
        """Test listing templates by language."""
        engine = TemplateEngine()

        python_templates = engine.list_templates(language="python")
        javascript_templates = engine.list_templates(language="javascript")
        html_templates = engine.list_templates(language="html")

        # Check languages
        assert all(t.language == "python" for t in python_templates)
        assert all(t.language == "javascript" for t in javascript_templates)
        assert all(t.language == "html" for t in html_templates)

    @patch("pathlib.Path.mkdir")
    def test_list_templates_combined_filters(self, mock_mkdir):
        """Test listing templates with multiple filters."""
        engine = TemplateEngine()

        templates = engine.list_templates(category="python", language="python")

        # Should only include templates that match both
        assert all(t.category == "python" and t.language == "python" for t in templates)

    @patch("pathlib.Path.mkdir")
    def test_list_templates_sorted(self, mock_mkdir):
        """Test that templates are sorted by name."""
        engine = TemplateEngine()

        templates = engine.list_templates()

        # Check sorting
        names = [t.name for t in templates]
        assert names == sorted(names)

    @patch("pathlib.Path.mkdir")
    def test_list_templates_no_matches(self, mock_mkdir):
        """Test listing with no matching templates."""
        engine = TemplateEngine()

        templates = engine.list_templates(category="nonexistent")

        assert len(templates) == 0


class TestCreateTemplate:
    """Test template creation."""

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.__str__", return_value="/path/to/template")
    def test_create_template(self, mock_str, mock_file, mock_mkdir):
        """Test creating a new template."""
        engine = TemplateEngine()
        engine.template_dir = Path("/path/to")

        content = 'def ${name}():\n    return "${message}"'
        result = engine.create_template(
            name="custom_function",
            content=content,
            description="Custom function template",
            category="custom",
            language="python",
        )

        assert "custom_function" in result
        assert "/path/to" in result

        # Check template was added
        assert "custom_function" in engine.templates
        template = engine.templates["custom_function"]
        assert template.name == "custom_function"
        assert template.description == "Custom function template"
        assert template.category == "custom"
        assert template.language == "python"
        assert "name" in template.variables
        assert "message" in template.variables

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.__str__", return_value="/path/to/template")
    def test_create_template_overwrite(self, mock_str, mock_file, mock_mkdir):
        """Test overwriting existing template."""
        engine = TemplateEngine()
        engine.template_dir = Path("/path/to")

        # Create initial template
        engine.create_template(
            name="test", content="initial", description="Initial", category="old", language="python"
        )

        # Overwrite it
        result = engine.create_template(
            name="test",
            content="updated",
            description="Updated",
            category="new",
            language="javascript",
        )

        assert "test" in result

        # Check template was updated
        template = engine.templates["test"]
        assert template.description == "Updated"
        assert template.category == "new"
        assert template.language == "javascript"
        assert template.content == "updated"

    @patch("pathlib.Path.mkdir")
    def test_create_template_extracts_variables(self, mock_mkdir):
        """Test that create template extracts variables."""
        engine = TemplateEngine()
        engine.template_dir = Path("/tmp")

        with patch("builtins.open", mock_open()):
            with patch("pathlib.Path.__str__", return_value="/tmp/test.template"):
                engine.create_template(
                    name="test",
                    content="function ${func}(${param1}, ${param2}) { return ${param1} + ${param2}; }",
                    description="Test",
                    category="test",
                    language="javascript",
                )

        template = engine.templates["test"]
        expected_vars = {"func", "param1", "param2"}
        assert set(template.variables) == expected_vars


class TestDeleteTemplate:
    """Test template deletion."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_delete_user_template(self, mock_exists, mock_unlink, mock_mkdir):
        """Test deleting user template."""
        engine = TemplateEngine()

        # Create a user template
        template_info = TemplateInfo(
            name="test_template",
            description="Test",
            category="test",
            language="python",
            variables=[],
            file_path="/path/to/test.template",
        )
        template_info.content = "test content"
        engine.templates["test_template"] = template_info

        mock_exists.return_value = True

        result = engine.delete_template("test_template")

        assert "test_template" in result
        assert "deleted" in result
        mock_unlink.assert_called_once()
        assert "test_template" not in engine.templates

    @patch("pathlib.Path.mkdir")
    def test_delete_builtin_template(self, mock_mkdir):
        """Test deleting built-in template."""
        engine = TemplateEngine()

        # Try to delete built-in template
        result = engine.delete_template("python_class")

        assert "python_class" in result
        assert "deleted" in result
        # Built-in template should be removed from memory
        assert "python_class" not in engine.templates

    @patch("pathlib.Path.mkdir")
    def test_delete_nonexistent_template(self, mock_mkdir):
        """Test deleting non-existent template."""
        engine = TemplateEngine()

        result = engine.delete_template("nonexistent")

        assert "nonexistent" in result
        assert "not found" in result

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_delete_template_no_file(self, mock_exists, mock_unlink, mock_mkdir):
        """Test deleting template with no associated file."""
        engine = TemplateEngine()

        # Create template without file
        template_info = TemplateInfo(
            name="test",
            description="Test",
            category="test",
            language="python",
            variables=[],
            file_path="",
        )
        engine.templates["test"] = template_info

        mock_exists.return_value = False

        result = engine.delete_template("test")

        assert "test" in result
        assert "deleted" in result
        mock_unlink.assert_not_called()  # Should not try to unlink if no file
        assert "test" not in engine.templates


class TestGetTemplateInfo:
    """Test getting template information."""

    @patch("pathlib.Path.mkdir")
    def test_get_template_info_exists(self, mock_mkdir):
        """Test getting info for existing template."""
        engine = TemplateEngine()

        info = engine.get_template_info("python_class")

        assert info is not None
        assert info.name == "python_class"
        assert info.category == "python"
        assert info.language == "python"

    @patch("pathlib.Path.mkdir")
    def test_get_template_info_not_exists(self, mock_mkdir):
        """Test getting info for non-existent template."""
        engine = TemplateEngine()

        info = engine.get_template_info("nonexistent")

        assert info is None


class TestExportImportTemplate:
    """Test template export and import."""

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_export_template(self, mock_json_dump, mock_file, mock_mkdir):
        """Test exporting template."""
        engine = TemplateEngine()

        result = engine.export_template("python_class", "/path/to/export.json")

        assert "python_class" in result
        assert "/path/to/export.json" in result

        # Check JSON dump was called
        mock_json_dump.assert_called_once()
        args = mock_json_dump.call_args[0]
        export_data = args[0]

        assert export_data["name"] == "python_class"
        assert "description" in export_data
        assert "content" in export_data
        assert "variables" in export_data

    @patch("pathlib.Path.mkdir")
    def test_export_nonexistent_template(self, mock_mkdir):
        """Test exporting non-existent template."""
        engine = TemplateEngine()

        result = engine.export_template("nonexistent", "/path/to/file.json")

        assert "nonexistent" in result
        assert "not found" in result

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("json.dump")
    def test_import_template(self, mock_json_dump, mock_json_load, mock_file, mock_mkdir):
        """Test importing template."""
        engine = TemplateEngine()
        engine.template_dir = Path("/tmp")

        import_data = {
            "name": "imported_template",
            "description": "An imported template",
            "category": "imported",
            "language": "javascript",
            "content": "function ${name}() { return ${value}; }",
        }
        mock_json_load.return_value = import_data

        with patch("pathlib.Path.__str__", return_value="/tmp/imported_template.template"):
            result = engine.import_template("/path/to/import.json")

        assert "imported_template" in result
        assert "imported_template" in engine.templates

        template = engine.templates["imported_template"]
        assert template.name == "imported_template"
        assert template.description == "An imported template"
        assert template.category == "imported"
        assert template.language == "javascript"

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_import_template_missing_fields(self, mock_open, mock_mkdir):
        """Test importing template with missing required fields."""
        engine = TemplateEngine()

        with patch("json.load") as mock_json_load:
            mock_json_load.return_value = {
                "name": "incomplete",
                # Missing "content" field
            }

            result = engine.import_template("/path/to/file.json")

            assert "Missing required field: content" in result

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_import_template_invalid_json(self, mock_open, mock_mkdir):
        """Test importing template with invalid JSON."""
        engine = TemplateEngine()

        with patch("json.load", side_effect=json.JSONDecodeError("", "", 0)):
            result = engine.import_template("/path/to/file.json")

            assert "Error importing template" in result


class TestGenerateFromSchema:
    """Test generating code from schema."""

    @patch("pathlib.Path.mkdir")
    def test_generate_from_simple_schema(self, mock_mkdir):
        """Test generating code from simple schema."""
        engine = TemplateEngine()

        schema = {"name": "User", "fields": ["id", "email", "password"], "table": "users"}

        result = engine.generate_from_schema(schema, "sql_table")

        assert result is not None
        # Schema values should be available as variables
        # (This is a basic test - actual implementation would be more sophisticated)

    @patch("pathlib.Path.mkdir")
    def test_generate_from_nested_schema(self, mock_mkdir):
        """Test generating code from nested schema."""
        engine = TemplateEngine()

        schema = {
            "api": {
                "version": "v1",
                "endpoints": [
                    {"path": "/users", "method": "GET"},
                    {"path": "/users", "method": "POST"},
                ],
            }
        }

        result = engine.generate_from_schema(schema, "api_endpoint")

        assert result is not None

    @patch("pathlib.Path.mkdir")
    def test_generate_from_schema_list_items(self, mock_mkdir):
        """Test generating code from schema with list items."""
        engine = TemplateEngine()

        schema = {
            "columns": [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
        }

        result = engine.generate_from_schema(schema, "sql_table")

        assert result is not None


class TestBuiltinTemplates:
    """Test built-in template content."""

    @patch("pathlib.Path.mkdir")
    def test_builtin_python_class_template(self, mock_mkdir):
        """Test Python class built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("python_class")

        assert "class ${class_name}" in result
        assert "def __init__" in result
        assert "${methods}" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_python_function_template(self, mock_mkdir):
        """Test Python function built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("python_function")

        assert "def ${function_name}" in result
        assert "-> ${return_type}:" in result
        assert "${docstring}" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_js_function_template(self, mock_mkdir):
        """Test JavaScript function built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("js_function")

        assert "function ${function_name}" in result
        assert "/**" in result
        assert "@returns" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_html_template(self, mock_mkdir):
        """Test HTML page built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("html_page")

        assert "<!DOCTYPE html>" in result
        assert "<title>${title}</title>" in result
        assert "<body>" in result
        assert "${body_content}" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_react_template(self, mock_mkdir):
        """Test React component built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("react_component")

        assert "import React from 'react';" in result
        assert "const ${component_name}" in result
        assert "export default ${component_name};" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_api_endpoint_template(self, mock_mkdir):
        """Test API endpoint built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("api_endpoint")

        assert "@${method.lower()}" in result
        assert "async def ${endpoint_name}" in result
        assert "db: Session = Depends(get_db)" in result

    @patch("pathlib.Path.mkdir")
    def test_builtin_unknown_template(self, mock_mkdir):
        """Test getting unknown built-in template."""
        engine = TemplateEngine()

        result = engine._get_builtin_template_content("nonexistent")

        assert result == ""


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("pathlib.Path.mkdir")
    def test_template_name_conflict_builtin_user(self, mock_mkdir):
        """Test when user template conflicts with built-in."""
        engine = TemplateEngine()

        # Create user template with same name as built-in
        with (
            patch("builtins.open", mock_open()),
            patch("pathlib.Path.__str__", return_value="/tmp/python_function.template"),
        ):
            engine.create_template(
                name="python_function",
                content="custom content",
                description="Custom version",
                category="custom",
                language="python",
            )

        # User template should override built-in
        template = engine.templates["python_function"]
        assert template.description == "Custom version"
        assert template.content == "custom content"

    @patch("pathlib.Path.mkdir")
    def test_render_with_invalid_variable_names(self, mock_mkdir):
        """Test rendering with variable names that might cause issues."""
        engine = TemplateEngine()

        # Template should handle any variable names
        result = engine.render_template(
            "python_function",
            {
                "function_name": "test",
                "params": "",
                "return_type": "None",
                "docstring": "Test",
                "args_doc": "",
                "return_description": "",
                "function_body": "pass",
                # Variables with special characters
                "special_var": "value",
                "var-with-dash": "value",  # This won't work in Python dict keys
            },
        )

        assert "def test() -> None:" in result

    @patch("pathlib.Path.mkdir")
    def test_extract_variables_malformed_template(self, mock_mkdir):
        """Test extracting variables from malformed template."""
        engine = TemplateEngine()

        # Template with unmatched braces
        template = "${var1} ${var2 ${var3}} ${var4"
        variables = engine._extract_variables(template)

        # Should handle gracefully
        assert "var1" in variables
        assert "var2" in variables

    @patch("pathlib.Path.mkdir")
    def test_template_with_unicode(self, mock_mkdir):
        """Test handling unicode in templates."""
        engine = TemplateEngine()

        result = engine.render_template(
            "python_function",
            {
                "function_name": "greet",
                "params": "name: str",
                "return_type": "str",
                "docstring": "问候世界! 🌍",
                "args_doc": "",
                "return_description": "",
                "function_body": 'return f"你好, {name}!"',
            },
        )

        assert "def greet(name: str) -> str:" in result
        assert "问候世界" in result
        assert "你好" in result
