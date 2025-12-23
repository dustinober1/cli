"""Snippet manager for saving and reusing code snippets."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SnippetManager:
    """Manages code snippets for reuse across projects."""

    def __init__(self, workspace_dir: Optional[str] = None):
        """Initialize snippet manager."""
        self.workspace_dir = workspace_dir or os.getcwd()
        self.snippets_dir = Path.home() / ".vibe" / "snippets"
        self.snippets_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.snippets_dir / "index.json"

        # Load or create index
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load snippet index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        # Create new index
        return {
            "snippets": {},
            "categories": {},
            "tags": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _save_index(self):
        """Save snippet index to file."""
        self.index["updated_at"] = datetime.now().isoformat()
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def save_snippet(
        self,
        name: str,
        code: str,
        language: str,
        description: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
    ) -> str:
        """Save a code snippet."""
        # Create snippet metadata
        snippet_id = name.lower().replace(" ", "_")
        metadata = {
            "name": name,
            "language": language,
            "description": description,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "uses": 0,
        }

        # Save code to file
        snippet_file = self.snippets_dir / f"{snippet_id}.{self._get_extension(language)}"
        with open(snippet_file, "w") as f:
            f.write(code)

        # Update index
        self.index["snippets"][snippet_id] = {**metadata, "file": str(snippet_file)}

        # Update categories
        if category not in self.index["categories"]:
            self.index["categories"][category] = []
        if snippet_id not in self.index["categories"][category]:
            self.index["categories"][category].append(snippet_id)

        # Update tags
        for tag in tags or []:
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            if snippet_id not in self.index["tags"][tag]:
                self.index["tags"][tag].append(snippet_id)

        # Save index
        self._save_index()

        return f"Snippet saved: {name} (ID: {snippet_id})"

    def get_snippet(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get a snippet by ID, name, or tag."""
        # Try to find by ID
        if identifier in self.index["snippets"]:
            snippet_data = self.index["snippets"][identifier].copy()
            with open(snippet_data["file"], "r") as f:
                snippet_data["code"] = f.read()

            # Increment uses
            snippet_data["uses"] += 1
            self.index["snippets"][identifier]["uses"] += 1
            self._save_index()

            return snippet_data

        # Try to find by name
        for snippet_id, data in self.index["snippets"].items():
            if data["name"].lower() == identifier.lower():
                return self.get_snippet(snippet_id)

        # Try to find by tag
        if identifier in self.index["tags"]:
            # Return list of snippets with this tag
            return {"type": "tag_list", "snippets": self.index["tags"][identifier]}

        return None

    def list_snippets(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List snippets with optional filters."""
        snippets = []

        for snippet_id, data in self.index["snippets"].items():
            # Apply filters
            if category and data["category"] != category:
                continue
            if language and data["language"] != language:
                continue
            if tag and tag not in data["tags"]:
                continue

            snippets.append(
                {
                    "id": snippet_id,
                    "name": data["name"],
                    "language": data["language"],
                    "description": data["description"],
                    "category": data["category"],
                    "tags": data["tags"],
                    "created_at": data["created_at"],
                    "uses": data["uses"],
                }
            )

        # Sort by most used
        snippets.sort(key=lambda x: x["uses"], reverse=True)
        return snippets

    def search_snippets(self, query: str) -> List[Dict[str, Any]]:
        """Search snippets by text query."""
        results = []
        query_lower = query.lower()

        for snippet_id, data in self.index["snippets"].items():
            # Search in name, description, and tags
            searchable_text = " ".join(
                [data["name"], data["description"], " ".join(data["tags"])]
            ).lower()

            if query_lower in searchable_text:
                # Also search in code if needed
                code_match = False
                if query_lower not in searchable_text:
                    try:
                        with open(data["file"], "r") as f:
                            code_content = f.read().lower()
                            if query_lower in code_content:
                                code_match = True
                    except Exception:
                        pass

                if code_match or query_lower in searchable_text:
                    results.append(
                        {
                            "id": snippet_id,
                            "name": data["name"],
                            "language": data["language"],
                            "description": data["description"],
                            "category": data["category"],
                            "match_type": "code" if code_match else "metadata",
                        }
                    )

        return results

    def delete_snippet(self, identifier: str) -> str:
        """Delete a snippet."""
        # Find the snippet
        snippet_data = None
        snippet_id = None

        if identifier in self.index["snippets"]:
            snippet_id = identifier
        else:
            # Search by name
            for sid, data in self.index["snippets"].items():
                if data["name"].lower() == identifier.lower():
                    snippet_id = sid
                    break

        if not snippet_id:
            return f"Snippet not found: {identifier}"

        snippet_data = self.index["snippets"][snippet_id]

        # Remove file
        try:
            os.remove(snippet_data["file"])
        except Exception:
            pass

        # Remove from categories
        category = snippet_data["category"]
        if category in self.index["categories"]:
            if snippet_id in self.index["categories"][category]:
                self.index["categories"][category].remove(snippet_id)

        # Remove from tags
        for tag in snippet_data["tags"]:
            if tag in self.index["tags"]:
                if snippet_id in self.index["tags"][tag]:
                    self.index["tags"][tag].remove(snippet_id)

        # Remove from index
        del self.index["snippets"][snippet_id]

        # Save index
        self._save_index()

        return f"Snippet deleted: {snippet_data['name']}"

    def get_stats(self) -> Dict[str, Any]:
        """Get snippet statistics."""
        total_snippets = len(self.index["snippets"])
        total_uses = sum(data["uses"] for data in self.index["snippets"].values())
        language_counts = {}
        category_counts = {}

        for data in self.index["snippets"].values():
            # Language counts
            lang = data["language"]
            language_counts[lang] = language_counts.get(lang, 0) + 1

            # Category counts
            cat = data["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Most popular snippets
        popular = sorted(self.index["snippets"].items(), key=lambda x: x[1]["uses"], reverse=True)[
            :5
        ]

        return {
            "total_snippets": total_snippets,
            "total_uses": total_uses,
            "languages": language_counts,
            "categories": category_counts,
            "most_popular": [{"name": data["name"], "uses": data["uses"]} for _, data in popular],
        }

    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "go": "go",
            "rust": "rs",
            "c": "c",
            "cpp": "cpp",
            "csharp": "cs",
            "ruby": "rb",
            "php": "php",
            "swift": "swift",
            "kotlin": "kt",
            "scala": "scala",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "less": "less",
            "sql": "sql",
            "json": "json",
            "yaml": "yaml",
            "xml": "xml",
            "markdown": "md",
            "shell": "sh",
            "bash": "sh",
            "powershell": "ps1",
            "dockerfile": "dockerfile",
        }
        return extensions.get(language.lower(), "txt")

    def export_snippets(self, file_path: str) -> str:
        """Export all snippets to a JSON file."""
        export_data = {"exported_at": datetime.now().isoformat(), "version": "1.0", "snippets": {}}

        for snippet_id, data in self.index["snippets"].items():
            try:
                with open(data["file"], "r") as f:
                    code = f.read()
                export_data["snippets"][snippet_id] = {**data, "code": code}
            except Exception:
                continue

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return f"Exported {len(export_data['snippets'])} snippets to {file_path}"

    def import_snippets(self, file_path: str) -> str:
        """Import snippets from a JSON file."""
        try:
            with open(file_path, "r") as f:
                import_data = json.load(f)

            count = 0
            for snippet_id, data in import_data.get("snippets", {}).items():
                # Check if already exists
                if snippet_id in self.index["snippets"]:
                    continue

                # Save code file
                snippet_file = (
                    self.snippets_dir / f"{snippet_id}.{self._get_extension(data['language'])}"
                )
                with open(snippet_file, "w") as f:
                    f.write(data["code"])

                # Update index
                self.index["snippets"][snippet_id] = {
                    "name": data["name"],
                    "language": data["language"],
                    "description": data.get("description", ""),
                    "category": data.get("category", "general"),
                    "tags": data.get("tags", []),
                    "created_at": data.get("created_at", datetime.now().isoformat()),
                    "updated_at": datetime.now().isoformat(),
                    "uses": 0,
                    "file": str(snippet_file),
                }

                count += 1

            # Save index
            self._save_index()

            return f"Imported {count} snippets from {file_path}"

        except Exception as e:
            return f"Error importing snippets: {e}"
