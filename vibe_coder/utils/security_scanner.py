"""Security scanner utility for vulnerability detection."""

import re
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class SecurityIssue:
    """Represents a security vulnerability."""
    severity: str  # critical, high, medium, low
    type: str  # sql_injection, xss, hardcoded_secret, etc.
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str


class SecurityScanner:
    """Scans code for security vulnerabilities."""

    def __init__(self):
        """Initialize the security scanner."""
        self.patterns = self._load_security_patterns()
        self.secret_patterns = self._load_secret_patterns()

    def _load_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load security vulnerability patterns."""
        return {
            "sql_injection": [
                {
                    "pattern": r'execute\s*\(\s*["\'].*%.*["\']',
                    "languages": ["python"],
                    "severity": "high",
                    "description": "Potential SQL injection vulnerability",
                    "recommendation": "Use parameterized queries or prepared statements"
                },
                {
                    "pattern": r'query\s*\(\s*["\'].*\+.*["\']',
                    "languages": ["python", "javascript"],
                    "severity": "high",
                    "description": "SQL query built with string concatenation",
                    "recommendation": "Use parameterized queries"
                },
                {
                    "pattern": r'\$\{.*\}',
                    "languages": ["javascript", "java"],
                    "severity": "medium",
                    "description": "Template literal injection risk",
                    "recommendation": "Validate and sanitize inputs"
                }
            ],
            "command_injection": [
                {
                    "pattern": r'eval\s*\(',
                    "languages": ["python", "javascript", "php"],
                    "severity": "critical",
                    "description": "Use of eval() function",
                    "recommendation": "Avoid eval(). Use safer alternatives"
                },
                {
                    "pattern": r'exec\s*\(',
                    "languages": ["python"],
                    "severity": "critical",
                    "description": "Use of exec() function",
                    "recommendation": "Avoid exec(). Use safer alternatives"
                },
                {
                    "pattern": r'os\.system\s*\(',
                    "languages": ["python"],
                    "severity": "high",
                    "description": "Direct command execution",
                    "recommendation": "Use subprocess with proper sanitization"
                },
                {
                    "pattern": r'subprocess\.call\s*.*shell=True',
                    "languages": ["python"],
                    "severity": "high",
                    "description": "Shell injection risk with shell=True",
                    "recommendation": "Avoid shell=True or sanitize input"
                },
                {
                    "pattern": r'child_process\.exec\s*\(',
                    "languages": ["javascript"],
                    "severity": "high",
                    "description": "Command execution in Node.js",
                    "recommendation": "Use execSync or spawn with proper sanitization"
                }
            ],
            "path_traversal": [
                {
                    "pattern": r'\.\./',
                    "languages": ["python", "javascript", "java", "php"],
                    "severity": "medium",
                    "description": "Potential path traversal",
                    "recommendation": "Validate and sanitize file paths"
                },
                {
                    "pattern": r'open\s*\(\s*.*\+.*',
                    "languages": ["python"],
                    "severity": "medium",
                    "description": "File path constructed from variables",
                    "recommendation": "Use os.path.join and validate paths"
                }
            ],
            "hardcoded_secrets": [
                {
                    "pattern": r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']',
                    "languages": ["python", "javascript", "java", "php"],
                    "severity": "high",
                    "description": "Hardcoded password",
                    "recommendation": "Use environment variables or secure vault"
                },
                {
                    "pattern": r'(secret|key)\s*[=:]\s*["\'][^"\']+["\']',
                    "languages": ["python", "javascript", "java", "php"],
                    "severity": "high",
                    "description": "Hardcoded secret or API key",
                    "recommendation": "Use environment variables or secure vault"
                },
                {
                    "pattern": r'(token|auth)\s*[=:]\s*["\'][^"\']+["\']',
                    "languages": ["python", "javascript", "java", "php"],
                    "severity": "medium",
                    "description": "Hardcoded authentication token",
                    "recommendation": "Use environment variables or secure vault"
                }
            ],
            "insecure_crypto": [
                {
                    "pattern": r'md5\s*\(',
                    "languages": ["python", "javascript", "php"],
                    "severity": "medium",
                    "description": "Use of MD5 hash algorithm",
                    "recommendation": "Use SHA-256 or stronger hash algorithms"
                },
                {
                    "pattern": r'sha1\s*\(',
                    "languages": ["python", "javascript", "php"],
                    "severity": "medium",
                    "description": "Use of SHA-1 hash algorithm",
                    "recommendation": "Use SHA-256 or stronger hash algorithms"
                },
                {
                    "pattern": r'random\s*\(',
                    "languages": ["python"],
                    "severity": "medium",
                    "description": "Use of insecure random number generator",
                    "recommendation": "Use secrets module for cryptographic random"
                }
            ],
            "xss": [
                {
                    "pattern": r'innerHTML\s*=',
                    "languages": ["javascript", "typescript"],
                    "severity": "high",
                    "description": "Potential XSS vulnerability with innerHTML",
                    "recommendation": "Sanitize input before setting innerHTML"
                },
                {
                    "pattern": r'document\.write\s*\(',
                    "languages": ["javascript", "typescript"],
                    "severity": "high",
                    "description": "Potential XSS with document.write",
                    "recommendation": "Avoid document.write, use safer DOM methods"
                },
                {
                    "pattern": r'eval\s*\(',
                    "languages": ["javascript", "typescript"],
                    "severity": "critical",
                    "description": "XSS risk with eval",
                    "recommendation": "Avoid eval, use JSON.parse or alternatives"
                }
            ],
            "insecure_deserialization": [
                {
                    "pattern": r'pickle\.loads?\s*\(',
                    "languages": ["python"],
                    "severity": "critical",
                    "description": "Insecure pickle deserialization",
                    "recommendation": "Use safe serialization formats like JSON"
                },
                {
                    "pattern": r'yaml\.load\s*\(',
                    "languages": ["python"],
                    "severity": "high",
                    "description": "Unsafe YAML loading",
                    "recommendation": "Use yaml.safe_load instead"
                }
            ],
            "weak_authentication": [
                {
                    "pattern": r'==\s*["\'].*password["\']',
                    "languages": ["python", "javascript", "java", "php"],
                    "severity": "high",
                    "description": "Plain text password comparison",
                    "recommendation": "Use proper password hashing (bcrypt, scrypt, argon2)"
                }
            ]
        }

    def _load_secret_patterns(self) -> List[Dict[str, str]]:
        """Load patterns for detecting secrets."""
        return [
            {
                "pattern": r'AIza[0-9A-Za-z_-]{35}',
                "type": "Google API Key",
                "severity": "critical"
            },
            {
                "pattern": r'AKIA[0-9A-Z]{16}',
                "type": "AWS Access Key",
                "severity": "critical"
            },
            {
                "pattern": r'ghp_[a-zA-Z0-9]{36}',
                "type": "GitHub Personal Access Token",
                "severity": "critical"
            },
            {
                "pattern": r'glpat-[a-zA-Z0-9_-]{20}',
                "type": "GitLab Personal Access Token",
                "severity": "critical"
            },
            {
                "pattern": r'sk_[a-zA-Z0-9]{24,}',
                "type": "Stripe API Key",
                "severity": "critical"
            },
            {
                "pattern": r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{32}',
                "type": "Slack Token",
                "severity": "critical"
            }
        ]

    def scan_file(self, file_path: str) -> List[SecurityIssue]:
        """Scan a single file for security issues."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Detect language
            language = self._detect_language(file_path)

            # Scan for security patterns
            for vuln_type, patterns in self.patterns.items():
                for pattern_info in patterns:
                    # Check if pattern applies to this language
                    if language and pattern_info.get("languages") and language not in pattern_info["languages"]:
                        continue

                    # Search for pattern
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                            # Extract code snippet (context)
                            start_line = max(0, line_num - 2)
                            end_line = min(len(lines), line_num + 2)
                            code_snippet = '\n'.join(lines[start_line:end_line])
                            # Highlight the matching line
                            code_snippet = code_snippet.replace(
                                lines[line_num - 1],
                                f">>> {lines[line_num - 1]}"
                            )

                            issues.append(SecurityIssue(
                                severity=pattern_info["severity"],
                                type=vuln_type,
                                description=pattern_info["description"],
                                file_path=file_path,
                                line_number=line_num,
                                code_snippet=code_snippet,
                                recommendation=pattern_info["recommendation"]
                            ))

            # Scan for hardcoded secrets
            for secret_pattern in self.secret_patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(secret_pattern["pattern"], line):
                        # Mask the secret in the snippet
                        masked_line = re.sub(
                            secret_pattern["pattern"],
                            lambda m: m.group(0)[:8] + "***" + m.group(0)[-4:],
                            line
                        )

                        start_line = max(0, line_num - 1)
                        end_line = min(len(lines), line_num + 1)
                        code_snippet = '\n'.join(lines[start_line:end_line])
                        code_snippet = code_snippet.replace(
                            lines[line_num - 1],
                            f">>> {masked_line}"
                        )

                        issues.append(SecurityIssue(
                            severity=secret_pattern["severity"],
                            type="hardcoded_secret",
                            description=f"Detected {secret_pattern['type']}",
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=code_snippet,
                            recommendation="Remove hardcoded secret and use environment variables or secret management"
                        ))

        except Exception as e:
            issues.append(SecurityIssue(
                severity="low",
                type="scan_error",
                description=f"Error scanning file: {str(e)}",
                file_path=file_path,
                line_number=0,
                code_snippet="",
                recommendation="Check file encoding and permissions"
            ))

        return issues

    def scan_directory(self, directory: str, max_files: int = 100) -> List[SecurityIssue]:
        """Scan directory for security issues."""
        issues = []
        scanned_files = 0

        # Find code files
        code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb',
            '.php', '.cs', '.cpp', '.c', '.h', '.hpp', '.rs', '.swift',
            '.kt', '.scala', '.html', '.htm', '.css', '.scss', '.less',
            '.xml', '.json', '.yaml', '.yml', '.sh', '.bash', '.zsh',
            '.ps1', '.bat', '.cmd', '.sql', '.pl', '.r', '.m', '.vue',
            '.svelte', '.astro', '.erb', '.ejs', '.hbs', '.mustache'
        ]

        for root, dirs, files in os.walk(directory):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if scanned_files >= max_files:
                    break

                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    file_issues = self.scan_file(file_path)
                    issues.extend(file_issues)
                    scanned_files += 1

            if scanned_files >= max_files:
                break

        return issues

    def generate_report(self, issues: List[SecurityIssue]) -> str:
        """Generate a security report from issues."""
        # Group issues by severity
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for issue in issues:
            by_severity[issue.severity].append(issue)

        # Generate report
        report = []
        report.append("🔒 Security Scan Report")
        report.append("=" * 50)
        report.append(f"Total issues found: {len(issues)}")

        # Summary by severity
        report.append("\n📊 Summary by Severity:")
        for severity in ["critical", "high", "medium", "low"]:
            count = len(by_severity[severity])
            if count > 0:
                emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}[severity]
                report.append(f"  {emoji} {severity.title()}: {count}")

        # Detailed issues (only show critical and high by default)
        report.append("\n🔍 Critical & High Issues:")
        critical_and_high = by_severity["critical"] + by_severity["high"]

        if not critical_and_high:
            report.append("  ✅ No critical or high issues found!")
        else:
            for i, issue in enumerate(critical_and_high, 1):
                report.append(f"\n{i}. {issue.description}")
                report.append(f"   📁 File: {issue.file_path}:{issue.line_number}")
                report.append(f"   🏷️  Type: {issue.type.replace('_', ' ').title()}")
                report.append(f"   💡 Recommendation: {issue.recommendation}")

                if issue.code_snippet:
                    report.append("   📝 Code:")
                    for line in issue.code_snippet.split('\n'):
                        if line.strip():
                            report.append(f"     {line}")

        # Recommendations summary
        report.append("\n💡 Security Recommendations:")
        if len(by_severity["critical"]) > 0:
            report.append("  🚨 Address critical vulnerabilities immediately")
        if len(by_severity["high"]) > 0:
            report.append("  ⚠️ Prioritize high-severity issues")
        if len(by_severity["medium"]) > 0:
            report.append("  ⚡ Review medium-severity issues")
        report.append("  🔧 Run automated security tools in CI/CD")
        report.append("  🔐 Use secret management for credentials")
        report.append("  🛡️  Enable security headers in web applications")

        return '\n'.join(report)

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.sql': 'sql',
            '.pl': 'perl',
            '.r': 'r',
            '.m': 'objective-c',
            '.vue': 'vue',
            '.svelte': 'svelte',
            '.astro': 'astro',
            '.erb': 'ruby',
            '.ejs': 'javascript',
            '.hbs': 'javascript',
            '.mustache': 'javascript'
        }
        return language_map.get(ext)

    def run_tool_scan(self, directory: str, tool: str = "auto") -> Dict[str, Any]:
        """Run external security scanning tools."""
        results = {"tool": tool, "output": "", "issues": []}

        if tool == "auto" or tool == "bandit":
            # Try bandit for Python
            if any(Path(directory).rglob("*.py")):
                try:
                    result = subprocess.run(
                        ["bandit", "-r", directory, "-f", "json"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0 or result.returncode == 1:  # 1 means issues found
                        results["output"] = result.stdout
                        if result.stdout:
                            import json
                            bandit_results = json.loads(result.stdout)
                            results["issues"] = bandit_results.get("results", [])
                        results["tool"] = "bandit"
                except Exception:
                    pass

        if tool == "auto" or tool == "semgrep":
            # Try semgrep
            try:
                result = subprocess.run(
                    ["semgrep", "--config=auto", "--json", directory],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    results["output"] = result.stdout
                    if result.stdout:
                        semgrep_results = json.loads(result.stdout)
                        results["issues"] = semgrep_results.get("results", [])
                    results["tool"] = "semgrep"
            except Exception:
                pass

        if tool == "auto" or tool == "npm-audit":
            # Try npm audit
            package_json = Path(directory) / "package.json"
            if package_json.exists():
                try:
                    result = subprocess.run(
                        ["npm", "audit", "--json"],
                        capture_output=True,
                        text=True,
                        cwd=directory
                    )
                    if result.stdout:
                        results["output"] = result.stdout
                        npm_results = json.loads(result.stdout)
                        results["issues"] = npm_results.get("vulnerabilities", {}).values()
                    results["tool"] = "npm-audit"
                except Exception:
                    pass

        return results