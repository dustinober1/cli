"""Tests for the SnippetManager class."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import json
import os
from datetime import datetime

from vibe_coder.utils.snippet_manager import SnippetManager


class TestSnippetManagerInitialization:
    """Test SnippetManager initialization."""

    def test_init_with_default_workspace(self):
        """Test initialization with default workspace directory."""
        with patch('os.getcwd', return_value='/default/workspace'):
            manager = SnippetManager()

            assert manager.workspace_dir == '/default/workspace'
            assert manager.snippets_dir.name == 'snippets'
            assert '.vibe' in str(manager.snippets_dir)

    def test_init_with_custom_workspace(self):
        """Test initialization with custom workspace directory."""
        manager = SnippetManager(workspace_dir='/custom/workspace')

        assert manager.workspace_dir == '/custom/workspace'

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_init_creates_directories(self, mock_exists, mock_mkdir):
        """Test that initialization creates necessary directories."""
        mock_exists.return_value = False

        manager = SnippetManager()

        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('json.load')
    def test_load_index_existing(self, mock_json_load, mock_exists, mock_file):
        """Test loading existing index file."""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "snippets": {"test": {"name": "test"}},
            "categories": {},
            "tags": {}
        }

        manager = SnippetManager()

        assert manager.index["snippets"] == {"test": {"name": "test"}}
        mock_json_load.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_index_creates_new(self, mock_exists):
        """Test creating new index when none exists."""
        mock_exists.return_value = False

        manager = SnippetManager()

        assert "snippets" in manager.index
        assert "categories" in manager.index
        assert "tags" in manager.index
        assert "created_at" in manager.index
        assert "updated_at" in manager.index

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('json.load')
    def test_load_index_corrupted(self, mock_json_load, mock_exists, mock_file):
        """Test handling corrupted index file."""
        mock_exists.return_value = True
        mock_json_load.side_effect = json.JSONDecodeError("", "", 0)

        manager = SnippetManager()

        # Should create new index when file is corrupted
        assert "snippets" in manager.index
        assert len(manager.index["snippets"]) == 0


class TestSaveSnippet:
    """Test snippet saving functionality."""

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_basic(self, mock_file, mock_json_dump, mock_mkdir):
        """Test basic snippet saving."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        result = manager.save_snippet(
            name="Test Snippet",
            code="def hello():\n    return 'world'",
            language="python",
            description="A test snippet",
            category="testing",
            tags=["test", "example"]
        )

        assert "Test Snippet" in result
        assert "test_snippet" in result

        # Check index was updated
        assert "test_snippet" in manager.index["snippets"]
        snippet_data = manager.index["snippets"]["test_snippet"]
        assert snippet_data["name"] == "Test Snippet"
        assert snippet_data["language"] == "python"
        assert snippet_data["description"] == "A test snippet"
        assert snippet_data["category"] == "testing"
        assert snippet_data["tags"] == ["test", "example"]

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_minimal(self, mock_file, mock_json_dump, mock_mkdir):
        """Test saving snippet with minimal parameters."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        result = manager.save_snippet(
            name="Minimal",
            code="print('hello')",
            language="python"
        )

        assert "Minimal" in result

        snippet_data = manager.index["snippets"]["minimal"]
        assert snippet_data["name"] == "Minimal"
        assert snippet_data["description"] == ""
        assert snippet_data["category"] == "general"
        assert snippet_data["tags"] == []

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_duplicate_id(self, mock_file, mock_json_dump, mock_mkdir):
        """Test saving snippet with duplicate ID."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "duplicate_id": {"name": "Existing snippet"}
            },
            "categories": {},
            "tags": {}
        }

        # Save with same ID (different case)
        result = manager.save_snippet(
            name="Duplicate ID",
            code="new code",
            language="python"
        )

        # Should overwrite existing
        assert manager.index["snippets"]["duplicate_id"]["name"] == "Duplicate ID"

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_creates_categories(self, mock_file, mock_json_dump, mock_mkdir):
        """Test that saving snippet creates categories."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        manager.save_snippet(
            name="Test",
            code="code",
            language="python",
            category="new_category"
        )

        assert "new_category" in manager.index["categories"]
        assert "test" in manager.index["categories"]["new_category"]

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_creates_tags(self, mock_file, mock_json_dump, mock_mkdir):
        """Test that saving snippet creates tags."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        manager.save_snippet(
            name="Test",
            code="code",
            language="python",
            tags=["tag1", "tag2", "tag3"]
        )

        assert "tag1" in manager.index["tags"]
        assert "tag2" in manager.index["tags"]
        assert "tag3" in manager.index["tags"]
        assert "test" in manager.index["tags"]["tag1"]
        assert "test" in manager.index["tags"]["tag2"]
        assert "test" in manager.index["tags"]["tag3"]

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_existing_tags(self, mock_file, mock_json_dump, mock_mkdir):
        """Test saving snippet with existing tags."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {},
            "categories": {},
            "tags": {"existing_tag": ["other_snippet"]}
        }

        manager.save_snippet(
            name="New",
            code="code",
            language="python",
            tags=["existing_tag", "new_tag"]
        )

        # Should add to existing tag
        assert len(manager.index["tags"]["existing_tag"]) == 2
        assert "new" in manager.index["tags"]["existing_tag"]

        # Should create new tag
        assert "new_tag" in manager.index["tags"]
        assert "new" in manager.index["tags"]["new_tag"]


class TestGetSnippet:
    """Test snippet retrieval."""

    @patch('builtins.open', new_callable=mock_open, read_data="test code")
    @patch('pathlib.Path.exists')
    def test_get_snippet_by_id(self, mock_exists, mock_file):
        """Test getting snippet by ID."""
        mock_exists.return_value = True

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_id": {
                    "name": "Test",
                    "language": "python",
                    "description": "Test snippet",
                    "category": "test",
                    "tags": ["test"],
                    "file": "/path/to/test.py",
                    "uses": 5
                }
            },
            "categories": {},
            "tags": {}
        }

        result = manager.get_snippet("test_id")

        assert result is not None
        assert result["name"] == "Test"
        assert result["code"] == "test code"
        assert result["uses"] == 6  # Should increment

    @patch('builtins.open', new_callable=mock_open, read_data="test code")
    @patch('pathlib.Path.exists')
    def test_get_snippet_by_name(self, mock_exists, mock_file):
        """Test getting snippet by name."""
        mock_exists.return_value = True

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_snippet": {
                    "name": "Test Snippet",
                    "language": "python",
                    "file": "/path/to/test.py",
                    "uses": 0
                }
            },
            "categories": {},
            "tags": {}
        }

        result = manager.get_snippet("test snippet")

        assert result is not None
        assert result["name"] == "Test Snippet"
        assert result["uses"] == 1

    @patch('builtins.open', new_callable=mock_open, read_data="test code")
    @patch('pathlib.Path.exists')
    def test_get_snippet_by_tag(self, mock_exists, mock_file):
        """Test getting snippets by tag."""
        mock_exists.return_value = True

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {"name": "Snippet 1"},
                "snippet2": {"name": "Snippet 2"},
                "snippet3": {"name": "Snippet 3"}
            },
            "categories": {},
            "tags": {
                "python": ["snippet1", "snippet3"]
            }
        }

        result = manager.get_snippet("python")

        assert result is not None
        assert result["type"] == "tag_list"
        assert set(result["snippets"]) == {"snippet1", "snippet3"}

    def test_get_snippet_not_found(self):
        """Test getting non-existent snippet."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        result = manager.get_snippet("nonexistent")

        assert result is None


class TestListSnippets:
    """Test snippet listing."""

    def test_list_snippets_all(self):
        """Test listing all snippets."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {
                    "name": "Snippet 1",
                    "language": "python",
                    "description": "First snippet",
                    "category": "test",
                    "tags": ["tag1"],
                    "created_at": "2024-01-01T00:00:00",
                    "uses": 10
                },
                "snippet2": {
                    "name": "Snippet 2",
                    "language": "javascript",
                    "description": "Second snippet",
                    "category": "example",
                    "tags": ["tag2"],
                    "created_at": "2024-01-02T00:00:00",
                    "uses": 5
                }
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets()

        assert len(results) == 2
        # Should be sorted by uses (descending)
        assert results[0]["name"] == "Snippet 1"
        assert results[0]["uses"] == 10
        assert results[1]["name"] == "Snippet 2"
        assert results[1]["uses"] == 5

    def test_list_snippets_by_category(self):
        """Test listing snippets by category."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {"name": "Snippet 1", "category": "test"},
                "snippet2": {"name": "Snippet 2", "category": "example"},
                "snippet3": {"name": "Snippet 3", "category": "test"}
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets(category="test")

        assert len(results) == 2
        assert all(s["category"] == "test" for s in results)

    def test_list_snippets_by_language(self):
        """Test listing snippets by language."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "py_snippet": {"name": "Python", "language": "python"},
                "js_snippet": {"name": "JavaScript", "language": "javascript"},
                "py_snippet2": {"name": "Python 2", "language": "python"}
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets(language="python")

        assert len(results) == 2
        assert all(s["language"] == "python" for s in results)

    def test_list_snippets_by_tag(self):
        """Test listing snippets by tag."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {"name": "Snippet 1", "tags": ["tag1", "common"]},
                "snippet2": {"name": "Snippet 2", "tags": ["tag2"]},
                "snippet3": {"name": "Snippet 3", "tags": ["common"]}
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets(tag="common")

        assert len(results) == 2
        assert all("common" in s["tags"] for s in results)

    def test_list_snippets_multiple_filters(self):
        """Test listing snippets with multiple filters."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "python_test": {
                    "name": "Python Test",
                    "language": "python",
                    "category": "test",
                    "tags": ["test"]
                },
                "python_example": {
                    "name": "Python Example",
                    "language": "python",
                    "category": "example",
                    "tags": ["test"]
                },
                "js_test": {
                    "name": "JS Test",
                    "language": "javascript",
                    "category": "test",
                    "tags": ["test"]
                }
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets(
            language="python",
            category="test",
            tag="test"
        )

        assert len(results) == 1
        assert results[0]["name"] == "Python Test"

    def test_list_snippets_no_results(self):
        """Test listing when no snippets match filters."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {"name": "Snippet 1", "category": "test"}
            },
            "categories": {},
            "tags": {}
        }

        results = manager.list_snippets(category="nonexistent")

        assert len(results) == 0


class TestSearchSnippets:
    """Test snippet searching."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_search_snippets_by_name(self, mock_exists, mock_file):
        """Test searching snippets by name."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "code content"

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "python_func": {
                    "name": "Python Function",
                    "description": "A function in Python",
                    "tags": ["python"],
                    "file": "/path/to/file.py"
                },
                "js_func": {
                    "name": "JavaScript Function",
                    "description": "A function in JavaScript",
                    "tags": ["javascript"],
                    "file": "/path/to/file2.js"
                }
            }
        }

        results = manager.search_snippets("python")

        assert len(results) == 1
        assert results[0]["name"] == "Python Function"
        assert results[0]["match_type"] == "metadata"

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_search_snippets_by_description(self, mock_exists, mock_file):
        """Test searching snippets by description."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "code content"

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {
                    "name": "Snippet 1",
                    "description": "This snippet sorts an array",
                    "tags": [],
                    "file": "/path/to/file.py"
                },
                "snippet2": {
                    "name": "Snippet 2",
                    "description": "This snippet filters data",
                    "tags": [],
                    "file": "/path/to/file2.py"
                }
            }
        }

        results = manager.search_snippets("sort")

        assert len(results) == 1
        assert "sort" in results[0]["description"]

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_search_snippets_by_tag(self, mock_exists, mock_file):
        """Test searching snippets by tag."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "code content"

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {
                    "name": "Snippet 1",
                    "description": "",
                    "tags": ["algorithm", "sorting"],
                    "file": "/path/to/file.py"
                },
                "snippet2": {
                    "name": "Snippet 2",
                    "description": "",
                    "tags": ["utility"],
                    "file": "/path/to/file2.py"
                }
            }
        }

        results = manager.search_snippets("algorithm")

        assert len(results) == 1
        assert results[0]["id"] == "snippet1"

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_search_snippets_by_code(self, mock_exists, mock_file):
        """Test searching snippets by code content."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "def bubble_sort(arr):\n    # Sorting implementation"

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "sort_snippet": {
                    "name": "Sort Function",
                    "description": "A sorting function",
                    "tags": [],
                    "file": "/path/to/file.py"
                }
            }
        }

        results = manager.search_snippets("bubble_sort")

        assert len(results) == 1
        assert results[0]["match_type"] == "code"

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_search_snippets_no_match(self, mock_exists, mock_file):
        """Test searching with no matches."""
        mock_exists.return_value = True

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {
                    "name": "Snippet 1",
                    "description": "Description",
                    "tags": ["tag1"],
                    "file": "/path/to/file.py"
                }
            }
        }

        results = manager.search_snippets("nonexistent")

        assert len(results) == 0

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_search_snippets_case_insensitive(self, mock_exists, mock_file):
        """Test that search is case insensitive."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "CODE CONTENT"

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test": {
                    "name": "Python Snippet",
                    "description": "A PYTHON example",
                    "tags": ["PYTHON"],
                    "file": "/path/to/file.py"
                }
            }
        }

        # Search with lowercase
        results = manager.search_snippets("python")

        assert len(results) == 1


class TestDeleteSnippet:
    """Test snippet deletion."""

    @patch('os.remove')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_delete_snippet_by_id(self, mock_file, mock_json_dump, mock_remove):
        """Test deleting snippet by ID."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_snippet": {
                    "name": "Test Snippet",
                    "language": "python",
                    "file": "/path/to/test.py",
                    "category": "test",
                    "tags": ["test", "example"]
                }
            },
            "categories": {"test": ["test_snippet"]},
            "tags": {"test": ["test_snippet"], "example": ["test_snippet"]}
        }

        result = manager.delete_snippet("test_snippet")

        assert "Test Snippet" in result
        assert "deleted" in result.lower()

        # Check snippet was removed from index
        assert "test_snippet" not in manager.index["snippets"]

        # Check file was removed
        mock_remove.assert_called_with("/path/to/test.py")

        # Check category was updated
        assert "test_snippet" not in manager.index["categories"]["test"]

        # Check tags were updated
        assert "test_snippet" not in manager.index["tags"]["test"]
        assert "test_snippet" not in manager.index["tags"]["example"]

    @patch('os.remove')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_delete_snippet_by_name(self, mock_file, mock_json_dump, mock_remove):
        """Test deleting snippet by name."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_snippet": {
                    "name": "Test Snippet",
                    "language": "python",
                    "file": "/path/to/test.py",
                    "category": "test",
                    "tags": []
                }
            },
            "categories": {"test": ["test_snippet"]},
            "tags": {}
        }

        result = manager.delete_snippet("Test Snippet")

        assert "Test Snippet" in result
        assert "test_snippet" not in manager.index["snippets"]

    def test_delete_snippet_not_found(self):
        """Test deleting non-existent snippet."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        result = manager.delete_snippet("nonexistent")

        assert "not found" in result
        assert "nonexistent" in result

    @patch('os.remove')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_delete_snippet_file_error(self, mock_file, mock_json_dump, mock_remove):
        """Test deleting snippet when file removal fails."""
        mock_remove.side_effect = OSError("Permission denied")

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_snippet": {
                    "name": "Test",
                    "file": "/path/to/test.py",
                    "category": "test",
                    "tags": []
                }
            },
            "categories": {"test": ["test_snippet"]},
            "tags": {}
        }

        result = manager.delete_snippet("test_snippet")

        # Should still delete from index even if file removal fails
        assert "deleted" in result.lower()
        assert "test_snippet" not in manager.index["snippets"]


class TestGetStats:
    """Test statistics generation."""

    def test_get_stats_empty(self):
        """Test getting stats with no snippets."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        stats = manager.get_stats()

        assert stats["total_snippets"] == 0
        assert stats["total_uses"] == 0
        assert stats["languages"] == {}
        assert stats["categories"] == {}
        assert stats["most_popular"] == []

    def test_get_stats_with_data(self):
        """Test getting stats with snippet data."""
        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "snippet1": {
                    "name": "Snippet 1",
                    "language": "python",
                    "category": "utility",
                    "uses": 10
                },
                "snippet2": {
                    "name": "Snippet 2",
                    "language": "javascript",
                    "category": "utility",
                    "uses": 5
                },
                "snippet3": {
                    "name": "Snippet 3",
                    "language": "python",
                    "category": "example",
                    "uses": 15
                }
            },
            "categories": {},
            "tags": {}
        }

        stats = manager.get_stats()

        assert stats["total_snippets"] == 3
        assert stats["total_uses"] == 30
        assert stats["languages"]["python"] == 2
        assert stats["languages"]["javascript"] == 1
        assert stats["categories"]["utility"] == 2
        assert stats["categories"]["example"] == 1

        # Check most popular
        assert len(stats["most_popular"]) == 3
        assert stats["most_popular"][0]["name"] == "Snippet 3"
        assert stats["most_popular"][0]["uses"] == 15
        assert stats["most_popular"][1]["name"] == "Snippet 1"
        assert stats["most_popular"][1]["uses"] == 10


class TestGetExtension:
    """Test file extension mapping."""

    def test_get_extension_common(self):
        """Test getting extensions for common languages."""
        manager = SnippetManager()

        assert manager._get_extension("python") == "py"
        assert manager._get_extension("javascript") == "js"
        assert manager._get_extension("typescript") == "ts"
        assert manager._get_extension("java") == "java"
        assert manager._get_extension("go") == "go"
        assert manager._get_extension("rust") == "rs"
        assert manager._get_extension("c") == "c"
        assert manager._get_extension("cpp") == "cpp"
        assert manager._get_extension("ruby") == "rb"

    def test_get_extension_case_insensitive(self):
        """Test that extension mapping is case insensitive."""
        manager = SnippetManager()

        assert manager._get_extension("PYTHON") == "py"
        assert manager._get_extension("JavaScript") == "js"
        assert manager._get_extension("TypeScript") == "ts"

    def test_get_extension_default(self):
        """Test default extension for unknown languages."""
        manager = SnippetManager()

        assert manager._get_extension("unknown") == "txt"
        assert manager._get_extension("madeup") == "txt"
        assert manager._get_extension("") == "txt"


class TestExportImport:
    """Test snippet export and import."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_export_snippets(self, mock_exists, mock_file):
        """Test exporting snippets to file."""
        mock_exists.return_value = True

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test_snippet": {
                    "name": "Test",
                    "language": "python",
                    "description": "Test snippet",
                    "category": "test",
                    "tags": ["test"],
                    "file": "/path/to/test.py",
                    "uses": 5
                }
            }
        }

        # Mock reading the actual file
        with patch('builtins.open', mock_open(read_data="test code")):
            result = manager.export_snippets("/path/to/export.json")

        assert "Exported 1 snippets" in result
        assert "/path/to/export.json" in result

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_import_snippets(self, mock_exists, mock_mkdir, mock_file, mock_json_dump):
        """Test importing snippets from file."""
        # First call (checking if import file exists)
        # Second call (for index save)
        mock_exists.side_effect = [True, False]

        # Mock the import file content
        import_data = {
            "snippets": {
                "imported_snippet": {
                    "name": "Imported Snippet",
                    "language": "javascript",
                    "description": "An imported snippet",
                    "category": "imported",
                    "tags": ["import"],
                    "code": "console.log('hello');"
                }
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(import_data))):
            manager = SnippetManager()
            result = manager.import_snippets("/path/to/import.json")

        assert "Imported 1 snippets" in result

    @patch('pathlib.Path.exists')
    def test_import_snippets_file_error(self, mock_exists):
        """Test importing with file error."""
        mock_exists.return_value = True

        manager = SnippetManager()

        with patch('builtins.open', side_effect=OSError("File not found")):
            result = manager.import_snippets("/nonexistent/file.json")

        assert "Error importing snippets" in result

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_import_snippets_skip_duplicates(self, mock_exists, mock_mkdir, mock_file, mock_json_dump):
        """Test that import skips duplicate snippets."""
        mock_exists.side_effect = [True, False]

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "existing_snippet": {
                    "name": "Existing",
                    "language": "python",
                    "file": "/path/to/existing.py"
                }
            }
        }

        import_data = {
            "snippets": {
                "existing_snippet": {
                    "name": "Existing Updated",
                    "language": "python",
                    "code": "updated code"
                },
                "new_snippet": {
                    "name": "New",
                    "language": "javascript",
                    "code": "new code"
                }
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(import_data))):
            result = manager.import_snippets("/path/to/import.json")

        # Should only import new snippet, skip duplicate
        assert "Imported 1 snippets" in result
        assert "existing_snippet" in manager.index["snippets"]
        assert manager.index["snippets"]["existing_snippet"]["name"] == "Existing"
        assert "new_snippet" in manager.index["snippets"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('pathlib.Path.mkdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_snippet_empty_code(self, mock_file, mock_json_dump, mock_mkdir):
        """Test saving snippet with empty code."""
        manager = SnippetManager()
        manager.index = {"snippets": {}, "categories": {}, "tags": {}}

        result = manager.save_snippet(
            name="Empty",
            code="",
            language="python"
        )

        assert "Empty" in result
        assert manager.index["snippets"]["empty"]["name"] == "Empty"

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_get_snippet_file_error(self, mock_exists, mock_file):
        """Test getting snippet when file read fails."""
        mock_exists.return_value = True
        mock_file.side_effect = OSError("Permission denied")

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test": {"name": "Test", "file": "/path/to/test.py", "uses": 0}
            }
        }

        result = manager.get_snippet("test")

        # Should handle file error gracefully
        assert result is None

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_search_snippets_file_error(self, mock_exists, mock_file):
        """Test searching when file read fails."""
        mock_exists.return_value = True
        mock_file.side_effect = OSError("Permission denied")

        manager = SnippetManager()
        manager.index = {
            "snippets": {
                "test": {
                    "name": "Test",
                    "description": "",
                    "tags": [],
                    "file": "/path/to/test.py"
                }
            }
        }

        results = manager.search_snippets("test")

        # Should handle file error gracefully
        assert len(results) == 0

    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": json}')
    @patch('pathlib.Path.exists')
    def test_load_index_invalid_json(self, mock_exists, mock_file):
        """Test loading index with invalid JSON."""
        mock_exists.return_value = True

        manager = SnippetManager()

        # Should create new index when JSON is invalid
        assert "snippets" in manager.index
        assert len(manager.index["snippets"]) == 0

    def test_save_index_timestamps(self):
        """Test that saving index updates timestamps."""
        manager = SnippetManager()
        original_updated = "2024-01-01T00:00:00"
        manager.index = {
            "snippets": {},
            "categories": {},
            "tags": {},
            "created_at": original_updated,
            "updated_at": original_updated
        }

        with patch('builtins.open', mock_open()), \
             patch('json.dump') as mock_json_dump:
            manager._save_index()

        # Should update updated_at timestamp
        assert manager.index["updated_at"] != original_updated
        assert manager.index["created_at"] == original_updated