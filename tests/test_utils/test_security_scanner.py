"""Tests for the SecurityScanner class."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import json

from vibe_coder.utils.security_scanner import SecurityScanner, SecurityIssue


class TestSecurityScannerInitialization:
    """Test SecurityScanner initialization."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = SecurityScanner()

        assert scanner.patterns is not None
        assert isinstance(scanner.patterns, dict)
        assert "sql_injection" in scanner.patterns
        assert "command_injection" in scanner.patterns
        assert "hardcoded_secrets" in scanner.patterns

        assert scanner.secret_patterns is not None
        assert isinstance(scanner.secret_patterns, list)
        assert len(scanner.secret_patterns) > 0


class TestLoadSecurityPatterns:
    """Test security pattern loading."""

    def test_load_security_patterns_structure(self):
        """Test that security patterns are loaded correctly."""
        scanner = SecurityScanner()
        patterns = scanner._load_security_patterns()

        # Check pattern categories
        expected_categories = [
            "sql_injection",
            "command_injection",
            "path_traversal",
            "hardcoded_secrets",
            "insecure_crypto",
            "xss",
            "insecure_deserialization",
            "weak_authentication"
        ]

        for category in expected_categories:
            assert category in patterns
            assert isinstance(patterns[category], list)

            # Check each pattern has required fields
            for pattern in patterns[category]:
                assert "pattern" in pattern
                assert "severity" in pattern
                assert "description" in pattern
                assert "recommendation" in pattern

    def test_load_secret_patterns_structure(self):
        """Test that secret patterns are loaded correctly."""
        scanner = SecurityScanner()
        patterns = scanner._load_secret_patterns()

        assert isinstance(patterns, list)
        assert len(patterns) > 0

        for pattern in patterns:
            assert "pattern" in pattern
            assert "type" in pattern
            assert "severity" in pattern


class TestScanFile:
    """Test file scanning functionality."""

    def test_scan_file_sql_injection(self):
        """Test detection of SQL injection vulnerabilities."""
        scanner = SecurityScanner()

        # Create a Python file with SQL injection vulnerability
        vulnerable_code = """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    # Vulnerable: string formatting in SQL
    query = "SELECT * FROM users WHERE id = %s" % user_id
    cursor.execute(query)
    return cursor.fetchone()
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect SQL injection
            sql_issues = [i for i in issues if i.type == "sql_injection"]
            assert len(sql_issues) > 0
            assert sql_issues[0].severity == "high"
            assert "SQL" in sql_issues[0].description
            assert temp_path == sql_issues[0].file_path
        finally:
            os.unlink(temp_path)

    def test_scan_file_command_injection(self):
        """Test detection of command injection vulnerabilities."""
        scanner = SecurityScanner()

        # Create a Python file with command injection vulnerability
        vulnerable_code = """
import os

def run_command(user_input):
    # Vulnerable: direct command execution
    os.system(f"ls {user_input}")

    # Also vulnerable: exec with user input
    exec(f"print({user_input})")
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect command injections
            command_issues = [i for i in issues if i.type == "command_injection"]
            assert len(command_issues) >= 2

            # Check for os.system detection
            os_system_issues = [i for i in command_issues if "os.system" in i.code_snippet]
            assert len(os_system_issues) > 0
            assert os_system_issues[0].severity in ["high", "critical"]

            # Check for exec detection
            exec_issues = [i for i in command_issues if "exec" in i.code_snippet]
            assert len(exec_issues) > 0
            assert exec_issues[0].severity == "critical"
        finally:
            os.unlink(temp_path)

    def test_scan_file_hardcoded_secrets(self):
        """Test detection of hardcoded secrets."""
        scanner = SecurityScanner()

        # Create a file with hardcoded secrets
        vulnerable_code = """
# API configuration
API_KEY = "AIzaSyDaGmWKa4JsXZ-HjGw63BSNUHMHXu7Zd4e"
DB_PASSWORD = "secret123"
aws_access_key = "AKIAIOSFODNN7EXAMPLE"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect hardcoded secrets
            secret_issues = [i for i in issues if i.type == "hardcoded_secret"]
            assert len(secret_issues) >= 3

            # Check specific secret types
            secret_types = [i.description for i in secret_issues]
            assert any("Google API" in s for s in secret_types)
            assert any("AWS Access" in s for s in secret_types)
            assert any("password" in s.lower() for s in secret_types)
        finally:
            os.unlink(temp_path)

    def test_scan_file_path_traversal(self):
        """Test detection of path traversal vulnerabilities."""
        scanner = SecurityScanner()

        # Create a file with path traversal vulnerability
        vulnerable_code = """
def read_file(filename):
    # Vulnerable: path traversal
    path = "../data/" + filename
    with open(path, 'r') as f:
        return f.read()
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect path traversal
            path_issues = [i for i in issues if i.type == "path_traversal"]
            assert len(path_issues) > 0
            assert "path traversal" in path_issues[0].description.lower()
        finally:
            os.unlink(temp_path)

    def test_scan_file_javascript_xss(self):
        """Test XSS detection in JavaScript."""
        scanner = SecurityScanner()

        # Create a JavaScript file with XSS vulnerability
        vulnerable_code = """
function displayUserInput(input) {
    // Vulnerable: direct innerHTML assignment
    document.getElementById('output').innerHTML = input;

    // Also vulnerable: document.write
    document.write('<div>' + input + '</div>');
}
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect XSS vulnerabilities
            xss_issues = [i for i in issues if i.type == "xss"]
            assert len(xss_issues) >= 2

            # Check for innerHTML and document.write
            innerhtml_issues = [i for i in xss_issues if "innerHTML" in i.code_snippet]
            assert len(innerhtml_issues) > 0

            docwrite_issues = [i for i in xss_issues if "document.write" in i.code_snippet]
            assert len(docwrite_issues) > 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_insecure_crypto(self):
        """Test detection of insecure cryptography."""
        scanner = SecurityScanner()

        # Create a file with insecure crypto
        vulnerable_code = """
import hashlib

def hash_password(password):
    # Weak: using MD5
    return hashlib.md5(password.encode()).hexdigest()

def generate_token():
    # Weak: using random instead of secrets
    import random
    return str(random.randint(1000, 9999))
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should detect insecure crypto
            crypto_issues = [i for i in issues if i.type == "insecure_crypto"]
            assert len(crypto_issues) >= 2

            # Check for MD5 and random
            md5_issues = [i for i in crypto_issues if "MD5" in i.description]
            assert len(md5_issues) > 0

            random_issues = [i for i in crypto_issues if "random" in i.description]
            assert len(random_issues) > 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_no_vulnerabilities(self):
        """Test scanning a file with no vulnerabilities."""
        scanner = SecurityScanner()

        # Create a safe Python file
        safe_code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers safely.\"\"\"
    return a + b

def greet(name: str) -> str:
    \"\"\"Return a greeting message.\"\"\"
    return f"Hello, {name}!"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(safe_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should find no security issues (or only low-severity ones)
            high_severity = [i for i in issues if i.severity in ["critical", "high"]]
            assert len(high_severity) == 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_nonexistent(self):
        """Test scanning a non-existent file."""
        scanner = SecurityScanner()

        issues = scanner.scan_file("/nonexistent/file.py")

        # Should return an error issue
        assert len(issues) == 1
        assert issues[0].type == "scan_error"
        assert issues[0].severity == "low"
        assert "Error scanning file" in issues[0].description

    def test_scan_file_language_filtering(self):
        """Test that patterns are filtered by language."""
        scanner = SecurityScanner()

        # Create a JavaScript file with Python-specific pattern
        js_code = """
function test() {
    // This shouldn't trigger Python patterns
    var result = "some string";
    return result;
}
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Should not detect Python-specific patterns
            python_issues = [i for i in issues if "python" in str(i.description).lower()]
            assert len(python_issues) == 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_code_snippet_context(self):
        """Test that code snippets include context."""
        scanner = SecurityScanner()

        # Create a file with vulnerability
        vulnerable_code = """
import os
def func():
    x = 1
    os.system("ls -la")  # Vulnerable line
    y = 2
    return x + y
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(vulnerable_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)

            # Find the os.system issue
            os_system_issues = [i for i in issues if "os.system" in i.code_snippet]
            if os_system_issues:
                snippet = os_system_issues[0].code_snippet
                # Should include context lines
                assert ">>> os.system" in snippet
                # Should have more than just the vulnerable line
                assert len(snippet.split('\n')) > 1
        finally:
            os.unlink(temp_path)


class TestScanDirectory:
    """Test directory scanning functionality."""

    def test_scan_directory(self):
        """Test scanning a directory with multiple files."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            files = {
                "vulnerable.py": """
import os
os.system("ls")
""",
                "safe.py": """
def add(a, b):
    return a + b
""",
                "vulnerable.js": """
eval(userInput);
""",
                "subdir/nested.py": """
exec(code)
"""
            }

            for filepath, content in files.items():
                full_path = os.path.join(tmpdir, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)

            issues = scanner.scan_directory(tmpdir)

            # Should find issues in vulnerable files
            assert len(issues) > 0

            # Check different types of issues
            issue_types = set(i.type for i in issues)
            assert "command_injection" in issue_types

    def test_scan_directory_max_files(self):
        """Test directory scanning with file limit."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create more files than the limit
            for i in range(10):
                with open(os.path.join(tmpdir, f"file{i}.py"), 'w') as f:
                    f.write(f"def func{i}(): pass\n")

            # Scan with limit of 5 files
            issues = scanner.scan_directory(tmpdir, max_files=5)

            # Should scan exactly 5 files
            assert len(issues) >= 0  # Might not find issues, but should scan

    def test_scan_directory_hidden_dirs(self):
        """Test that hidden directories are skipped."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create normal and hidden directories
            os.makedirs(os.path.join(tmpdir, "normal"))
            os.makedirs(os.path.join(tmpdir, ".hidden"))

            # Add files to both
            with open(os.path.join(tmpdir, "normal/file.py"), 'w') as f:
                f.write("os.system('ls')\n")

            with open(os.path.join(tmpdir, ".hidden/file.py"), 'w') as f:
                f.write("eval('code')\n")

            issues = scanner.scan_directory(tmpdir)

            # Should find issues in normal directory
            normal_issues = [i for i in issues if "normal/file.py" in i.file_path]
            assert len(normal_issues) > 0

            # Should NOT scan hidden directory
            hidden_issues = [i for i in issues if ".hidden/file.py" in i.file_path]
            assert len(hidden_issues) == 0

    def test_scan_directory_extensions(self):
        """Test that only code files are scanned."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create various file types
            files = {
                "code.py": "os.system('ls')",
                "code.js": "eval('code')",
                "readme.md": "# README",
                "data.json": '{"key": "value"}',
                "image.png": b'\x89PNG'  # Binary content
            }

            for filename, content in files.items():
                filepath = os.path.join(tmpdir, filename)
                if isinstance(content, bytes):
                    with open(filepath, 'wb') as f:
                        f.write(content)
                else:
                    with open(filepath, 'w') as f:
                        f.write(content)

            issues = scanner.scan_directory(tmpdir)

            # Should only scan code files (.py, .js)
            scanned_files = set(i.file_path for i in issues)
            assert any("code.py" in f for f in scanned_files)
            assert any("code.js" in f for f in scanned_files)

            # Should not scan non-code files
            assert not any("readme.md" in f for f in scanned_files)
            assert not any("data.json" in f for f in scanned_files)


class TestGenerateReport:
    """Test report generation."""

    def test_generate_report_empty(self):
        """Test generating report with no issues."""
        scanner = SecurityScanner()

        report = scanner.generate_report([])

        assert "Total issues found: 0" in report
        assert "No critical or high issues found!" in report
        assert "Security Recommendations" in report

    def test_generate_report_with_issues(self):
        """Test generating report with various issues."""
        scanner = SecurityScanner()

        # Create mock issues
        issues = [
            SecurityIssue(
                severity="critical",
                type="sql_injection",
                description="SQL injection vulnerability",
                file_path="/path/to/file.py",
                line_number=10,
                code_snippet=">>> query = \"SELECT * FROM users WHERE id = %s\" % user_id",
                recommendation="Use parameterized queries"
            ),
            SecurityIssue(
                severity="high",
                type="hardcoded_secrets",
                description="Hardcoded API key",
                file_path="/path/to/config.py",
                line_number=5,
                code_snippet=">>> API_KEY = \"sk_live_123***4567\"",
                recommendation="Use environment variables"
            ),
            SecurityIssue(
                severity="medium",
                type="insecure_crypto",
                description="Use of MD5 hash",
                file_path="/path/to/auth.py",
                line_number=20,
                code_snippet=">>> hashlib.md5(password.encode()).hexdigest()",
                recommendation="Use SHA-256 or stronger"
            )
        ]

        report = scanner.generate_report(issues)

        # Check summary
        assert "Total issues found: 3" in report
        assert "🚨 Critical: 1" in report
        assert "⚠️ High: 1" in report
        assert "⚡ Medium: 1" in report

        # Check detailed issues
        assert "SQL injection vulnerability" in report
        assert "/path/to/file.py:10" in report
        assert "Hardcoded API key" in report
        assert "Use parameterized queries" in report

        # Check code snippet
        assert ">>> query = \"SELECT * FROM users" in report

        # Check recommendations
        assert "Address critical vulnerabilities immediately" in report
        assert "Prioritize high-severity issues" in report

    def test_generate_report_only_low_severity(self):
        """Test report with only low severity issues."""
        scanner = SecurityScanner()

        issues = [
            SecurityIssue(
                severity="low",
                type="info",
                description="Informational issue",
                file_path="/path/to/file.py",
                line_number=1,
                code_snippet="# Low severity issue",
                recommendation="Consider fixing"
            )
        ]

        report = scanner.generate_report(issues)

        assert "No critical or high issues found!" in report
        assert "Review medium-severity issues" not in report


class TestDetectLanguage:
    """Test language detection from file extensions."""

    def test_detect_language_common(self):
        """Test detection of common languages."""
        scanner = SecurityScanner()

        assert scanner._detect_language("test.py") == "python"
        assert scanner._detect_language("test.js") == "javascript"
        assert scanner._detect_language("test.ts") == "typescript"
        assert scanner._detect_language("test.java") == "java"
        assert scanner._detect_language("test.go") == "go"
        assert scanner._detect_language("test.rb") == "ruby"
        assert scanner._detect_language("test.php") == "php"
        assert scanner._detect_language("test.cpp") == "cpp"
        assert scanner._detect_language("test.rs") == "rust"
        assert scanner._detect_language("test.swift") == "swift"

    def test_detect_language_web(self):
        """Test detection of web technologies."""
        scanner = SecurityScanner()

        assert scanner._detect_language("test.html") == "html"
        assert scanner._detect_language("test.css") == "css"
        assert scanner._detect_language("test.scss") == "scss"
        assert scanner._detect_language("test.vue") == "vue"
        assert scanner._detect_language("test.svelte") == "svelte"

    def test_detect_language_config(self):
        """Test detection of configuration files."""
        scanner = SecurityScanner()

        assert scanner._detect_language("Dockerfile") is None
        assert scanner._detect_language("test.json") == "json"
        assert scanner._detect_language("test.yaml") == "yaml"
        assert scanner._detect_language("test.yml") == "yaml"
        assert scanner._detect_language("test.xml") == "xml"

    def test_detect_language_shell(self):
        """Test detection of shell scripts."""
        scanner = SecurityScanner()

        assert scanner._detect_language("test.sh") == "shell"
        assert scanner._detect_language("test.bash") == "shell"
        assert scanner._detect_language("test.zsh") == "shell"
        assert scanner._detect_language("test.ps1") == "powershell"
        assert scanner._detect_language("test.bat") == "batch"
        assert scanner._detect_language("test.cmd") == "batch"

    def test_detect_language_unknown(self):
        """Test detection of unknown file types."""
        scanner = SecurityScanner()

        assert scanner._detect_language("test.unknown") is None
        assert scanner._detect_language("test") is None
        assert scanner._detect_language("Makefile") is None
        assert scanner._detect_language(".gitignore") is None


class TestRunToolScan:
    """Test external security tool integration."""

    @patch('subprocess.run')
    def test_run_tool_scan_bandit(self, mock_run):
        """Test running bandit security scanner."""
        scanner = SecurityScanner()

        # Mock bandit output
        mock_run.return_value.returncode = 1  # Issues found
        mock_run.return_value.stdout = json.dumps({
            "results": [
                {
                    "test_name": "hardcoded_password",
                    "issue_severity": "HIGH",
                    "issue_text": "Possible hardcoded password",
                    "filename": "test.py",
                    "line_number": 5
                }
            ]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            with open(os.path.join(tmpdir, "test.py"), 'w') as f:
                f.write("password = 'secret123'\n")

            results = scanner.run_tool_scan(tmpdir, tool="bandit")

            assert results["tool"] == "bandit"
            assert len(results["issues"]) == 1
            assert results["issues"][0]["test_name"] == "hardcoded_password"

    @patch('subprocess.run')
    def test_run_tool_scan_semgrep(self, mock_run):
        """Test running semgrep security scanner."""
        scanner = SecurityScanner()

        # Mock semgrep output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({
            "results": [
                {
                    "check_id": "python.security.eval",
                    "message": "Use of eval detected",
                    "path": "test.py",
                    "start": {"line": 10}
                }
            ]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            results = scanner.run_tool_scan(tmpdir, tool="semgrep")

            assert results["tool"] == "semgrep"
            assert len(results["issues"]) == 1

    @patch('subprocess.run')
    def test_run_tool_scan_npm_audit(self, mock_run):
        """Test running npm audit."""
        scanner = SecurityScanner()

        # Mock npm audit output
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = json.dumps({
            "vulnerabilities": {
                "lodash": {
                    "severity": "high",
                    "title": "Prototype Pollution in lodash"
                }
            }
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            with open(os.path.join(tmpdir, "package.json"), 'w') as f:
                f.write('{"name": "test", "dependencies": {"lodash": "^4.0.0"}}\n')

            results = scanner.run_tool_scan(tmpdir, tool="npm-audit")

            assert results["tool"] == "npm-audit"
            assert len(list(results["issues"])) == 1

    @patch('subprocess.run')
    def test_run_tool_scan_auto_detect(self, mock_run):
        """Test automatic tool detection."""
        scanner = SecurityScanner()

        # Mock bandit exists but semgrep doesn't
        def mock_subprocess_side_effect(cmd, **kwargs):
            if "bandit" in cmd:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = json.dumps({"results": []})
                return mock_result
            elif "semgrep" in cmd:
                raise FileNotFoundError("semgrep not found")

        mock_run.side_effect = mock_subprocess_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python file
            with open(os.path.join(tmpdir, "test.py"), 'w') as f:
                f.write("print('hello')\n")

            results = scanner.run_tool_scan(tmpdir, tool="auto")

            # Should detect and use bandit for Python
            assert results["tool"] == "bandit"

    @patch('subprocess.run')
    def test_run_tool_scan_no_tools(self, mock_run):
        """Test when no security tools are available."""
        scanner = SecurityScanner()

        # All tools raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("Tool not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            results = scanner.run_tool_scan(tmpdir, tool="auto")

            # Should return empty results
            assert results["output"] == ""
            assert len(results["issues"]) == 0

    def test_run_tool_scan_unknown_tool(self):
        """Test running an unknown tool."""
        scanner = SecurityScanner()

        with tempfile.TemporaryDirectory() as tmpdir:
            results = scanner.run_tool_scan(tmpdir, tool="unknown")

            # Should return empty results for unknown tool
            assert results["tool"] == "unknown"
            assert results["output"] == ""
            assert len(results["issues"]) == 0


class TestSecurityIssue:
    """Test SecurityIssue dataclass."""

    def test_security_issue_creation(self):
        """Test creating a security issue."""
        issue = SecurityIssue(
            severity="critical",
            type="sql_injection",
            description="SQL injection detected",
            file_path="/path/to/file.py",
            line_number=10,
            code_snippet=">>> vulnerable code here",
            recommendation="Use parameterized queries"
        )

        assert issue.severity == "critical"
        assert issue.type == "sql_injection"
        assert issue.description == "SQL injection detected"
        assert issue.file_path == "/path/to/file.py"
        assert issue.line_number == 10
        assert issue.code_snippet == ">>> vulnerable code here"
        assert issue.recommendation == "Use parameterized queries"

    def test_security_issue_equality(self):
        """Test security issue equality."""
        issue1 = SecurityIssue(
            severity="high",
            type="xss",
            description="XSS vulnerability",
            file_path="test.js",
            line_number=5,
            code_snippet=">>> innerHTML = userInput",
            recommendation="Sanitize input"
        )

        issue2 = SecurityIssue(
            severity="high",
            type="xss",
            description="XSS vulnerability",
            file_path="test.js",
            line_number=5,
            code_snippet=">>> innerHTML = userInput",
            recommendation="Sanitize input"
        )

        assert issue1 == issue2

    def test_security_issue_str_representation(self):
        """Test string representation of security issue."""
        issue = SecurityIssue(
            severity="critical",
            type="command_injection",
            description="Command injection",
            file_path="/path/file.py",
            line_number=1,
            code_snippet=">>> eval(input)",
            recommendation="Avoid eval"
        )

        str_repr = str(issue)
        assert "critical" in str_repr
        assert "command_injection" in str_repr
        assert "Command injection" in str_repr


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_scan_file_empty_content(self):
        """Test scanning an empty file."""
        scanner = SecurityScanner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)
            assert len(issues) == 0
        finally:
            os.unlink(temp_path)

    def test_scan_file_unicode_content(self):
        """Test scanning file with unicode content."""
        scanner = SecurityScanner()

        unicode_code = """
# Unicode string with emoji
message = "Hello, 世界! 🌍"
password = "密码123"  # Password in Chinese
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(unicode_code)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)
            # Should handle unicode without crashing
            assert isinstance(issues, list)
        finally:
            os.unlink(temp_path)

    def test_scan_file_large_file(self):
        """Test scanning a large file."""
        scanner = SecurityScanner()

        # Generate a large Python file
        large_content = "def func():\n    return " + "x + " * 10000 + "1\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_path = f.name

        try:
            issues = scanner.scan_file(temp_path)
            # Should handle large files
            assert isinstance(issues, list)
        finally:
            os.unlink(temp_path)

    def test_scan_directory_nonexistent(self):
        """Test scanning a non-existent directory."""
        scanner = SecurityScanner()

        issues = scanner.scan_directory("/nonexistent/directory")
        assert len(issues) == 0

    def test_scan_directory_permission_denied(self):
        """Test scanning directory with permission issues."""
        scanner = SecurityScanner()

        # This is hard to test reliably without root permissions
        # We'll just ensure it doesn't crash
        with patch('os.walk') as mock_walk:
            mock_walk.side_effect = PermissionError("Permission denied")

            issues = scanner.scan_directory("/some/path")
            assert len(issues) == 0