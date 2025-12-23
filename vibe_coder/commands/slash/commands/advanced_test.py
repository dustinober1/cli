"""Advanced testing and quality assurance slash commands."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class TestSmartCommand(SlashCommand):
    """Intelligent test generation using AI."""

    def __init__(self):
        super().__init__(
            name="test-smart",
            description="Generate intelligent unit tests for code",
            aliases=["smart-test", "ai-test"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the test-smart command."""
        if not args:
            return "Usage: /test-smart <filename>. Generate intelligent unit tests for the specified file."

        file_path = args[0]
        file_ops = FileOperations(context.working_directory)

        try:
            # Read the source file
            content = await file_ops.read_file(file_path)
            language = file_ops.detect_language(file_path)

            # Determine test file path
            test_file = self._get_test_file_path(file_path)

            # Build test generation prompt
            prompt = f"""Generate comprehensive unit tests for the following {language} code.

Requirements:
1. Test all public methods and functions
2. Include edge cases and error conditions
3. Use appropriate testing framework (pytest for Python, Jest for JavaScript, etc.)
4. Include setup and teardown if needed
5. Mock external dependencies
6. Add docstrings explaining what each test covers
7. Include parametrized tests for multiple inputs
8. Test both success and failure scenarios

Code to test:
```{language}
{content}
```

Provide only the complete test file content without explanations."""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": f"You are an expert in {language} testing. Generate comprehensive, production-ready unit tests using best practices.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            test_content = response.content.strip()

            # Extract test code from response
            if "```" in test_content:
                start = test_content.find("```") + 3
                end = test_content.find("```", start)
                if end != -1:
                    # Remove language identifier if present
                    code_start = start
                    if "\n" in test_content[start:end]:
                        code_start = test_content.find("\n", start) + 1
                    test_content = test_content[code_start:end]

            # Write test file
            await file_ops.write_file(test_file, test_content)

            # Count tests generated
            test_count = (
                test_content.count("def test_")
                if language == "python"
                else test_content.count("it(")
            )

            return f"""Generated {test_count} tests for {file_path}
- Test file: {test_file}
- Language: {language}

Generated tests cover:
✓ Public methods and functions
✓ Edge cases and error conditions
✓ Mocked dependencies
✓ Parametrized test cases
✓ Success and failure scenarios

Run tests with:
- Python: pytest {test_file}
- JavaScript: npm test {test_file}
"""

        except Exception as e:
            return f"Error generating tests: {e}"

    def _get_test_file_path(self, source_file: str) -> str:
        """Determine appropriate test file path."""
        path = Path(source_file)

        # Create test file name
        if path.name.startswith("test_"):
            return source_file

        # Python convention
        if path.suffix == ".py":
            return str(path.parent / f"test_{path.name}")

        # JavaScript/TypeScript convention
        if path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
            return str(path.parent / f"{path.stem}.test{path.suffix}")

        # Java convention
        if path.suffix == ".java":
            # Move to test directory structure
            parts = list(path.parts)
            if "src" in parts:
                test_parts = []
                for part in parts:
                    if part == "src":
                        test_parts.append("src")
                        test_parts.append("test")
                    elif part == "main":
                        test_parts.append("test")
                    else:
                        test_parts.append(part)
                return str(Path(*test_parts))

        # Default
        return str(path.parent / f"{path.stem}_test{path.suffix}")

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


class TestE2ECommand(SlashCommand):
    """Generate end-to-end tests."""

    def __init__(self):
        super().__init__(
            name="test-e2e",
            description="Generate end-to-end integration tests",
            aliases=["e2e", "integration"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the test-e2e command."""
        if not args:
            return """Usage: /test-e2e <feature_or_endpoint>
Examples:
- /test-e2e user-authentication
- /test-e2e /api/users
- /test-e2e shopping-cart-flow"""

        feature = args[0]
        additional_info = " ".join(args[1:]) if len(args) > 1 else ""

        try:
            # Determine the type of E2E test needed
            if feature.startswith("/"):
                test_type = "api"
            elif any(keyword in feature.lower() for keyword in ["ui", "page", "flow", "journey"]):
                test_type = "ui"
            else:
                test_type = "feature"

            # Build E2E test prompt
            if test_type == "api":
                prompt = f"""Generate comprehensive end-to-end API tests for the endpoint: {feature}

Additional context: {additional_info}

Requirements:
1. Test all HTTP methods (GET, POST, PUT, DELETE)
2. Include request/response validation
3. Test authentication/authorization
4. Include error scenarios (400, 401, 403, 404, 500)
5. Test request/response headers
6. Include rate limiting tests
7. Use appropriate testing framework (pytest + requests for Python)

Generate complete test file with setup, teardown, and test cases."""

            elif test_type == "ui":
                prompt = f"""Generate end-to-end UI tests for: {feature}

Additional context: {additional_info}

Requirements:
1. Test complete user flows/journeys
2. Include form submissions and validations
3. Test responsive design (mobile, tablet, desktop)
4. Include accessibility checks
5. Test navigation between pages
6. Include error handling scenarios
7. Use Playwright or Selenium
8. Include page object model pattern

Generate complete test file with page objects and test cases."""

            else:
                prompt = f"""Generate end-to-end integration tests for the feature: {feature}

Additional context: {additional_info}

Requirements:
1. Test complete feature workflow
2. Include integration with external services
3. Test database operations
4. Include message queue/pubsub tests if applicable
5. Test caching behavior
6. Include performance benchmarks
7. Test rollback scenarios
8. Use appropriate testing framework

Generate complete test file with fixtures and test cases."""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": "You are an expert in end-to-end testing. Generate comprehensive integration tests that cover real-world scenarios.",
                        "name": "E2ETestGenerator",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            test_content = response.content.strip()

            # Determine test file path
            test_dir = Path(context.working_directory) / "tests" / "e2e"
            test_dir.mkdir(parents=True, exist_ok=True)

            test_file = test_dir / f"test_{feature.replace('/', '_').replace(' ', '_').lower()}.py"

            # Extract and save test code
            if "```" in test_content:
                start = test_content.find("```") + 3
                end = test_content.find("```", start)
                if end != -1:
                    test_content = test_content[start:end]

            file_ops = FileOperations(context.working_directory)
            await file_ops.write_file(str(test_file), test_content)

            return f"""Generated end-to-end tests for '{feature}'
- Test file: {test_file}
- Test type: {test_type}

Generated tests include:
✓ Complete workflow coverage
✓ Error scenario handling
✓ Integration with dependencies
✓ Performance considerations

To run E2E tests:
- Ensure test environment is set up
- Install additional dependencies if needed
- Run: pytest {test_file}
"""

        except Exception as e:
            return f"Error generating E2E tests: {e}"

    def get_min_args(self) -> int:
        return 1


class BenchmarkCommand(SlashCommand):
    """Generate performance benchmarks."""

    def __init__(self):
        super().__init__(
            name="benchmark",
            description="Generate performance benchmarks for code",
            aliases=["bench", "perf-test"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the benchmark command."""
        if not args:
            return """Usage: /benchmark <filename> [options]
Options:
- --compare: Generate comparative benchmarks
- --memory: Include memory profiling
- --concurrent: Test concurrent performance

Example: /benchmark app.py --compare --memory"""

        file_path = args[0]
        options = args[1:] if len(args) > 1 else []
        file_ops = FileOperations(context.working_directory)

        try:
            # Read the source file
            content = await file_ops.read_file(file_path)
            language = file_ops.detect_language(file_path)

            # Determine benchmark requirements
            include_compare = "--compare" in options
            include_memory = "--memory" in options
            include_concurrent = "--concurrent" in options

            # Build benchmark generation prompt
            prompt = f"""Generate performance benchmarks for the following {language} code:

Options:
- Comparative benchmarking: {include_compare}
- Memory profiling: {include_memory}
- Concurrent performance: {include_concurrent}

Requirements:
1. Benchmark all public functions/methods
2. Measure execution time, memory usage, and throughput
3. Include parameterized benchmarks for different input sizes
4. Add statistical analysis (mean, median, std dev)
5. Include before/after comparisons if --compare specified
6. Generate performance regression tests
7. Include warm-up periods for accurate measurement
8. Use appropriate benchmarking library:

Python: pytest-benchmark or timeit
JavaScript: benchmark.js or console.time
Java: JMH
Go: testing/benchmark

Code to benchmark:
```{language}
{content}
```

Generate complete benchmark file with setup, teardown, and benchmark functions."""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": "You are a performance testing expert. Generate comprehensive benchmarks using industry best practices.",
                        "name": "BenchmarkGenerator",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            benchmark_content = response.content.strip()

            # Determine benchmark file path
            benchmark_dir = Path(context.working_directory) / "benchmarks"
            benchmark_dir.mkdir(parents=True, exist_ok=True)

            benchmark_file = benchmark_dir / f"bench_{Path(file_path).stem}.py"

            # Extract and save benchmark code
            if "```" in benchmark_content:
                start = benchmark_content.find("```") + 3
                end = benchmark_content.find("```", start)
                if end != -1:
                    benchmark_content = benchmark_content[start:end]

            await file_ops.write_file(str(benchmark_file), benchmark_content)

            # Generate requirements file if needed
            if language == "python":
                requirements = "pytest-benchmark>=4.0.0\nmemory-profiler>=0.60.0\n"
                if include_concurrent:
                    requirements += "concurrent-futures>=3.1.1\n"

                req_file = benchmark_dir / "requirements.txt"
                if not req_file.exists():
                    await file_ops.write_file(str(req_file), requirements)

            return f"""Generated performance benchmarks
- Benchmark file: {benchmark_file}
- Options: {', '.join(options) if options else 'default'}

Benchmark features:
✓ Execution time measurement
✓ Memory usage profiling ({'enabled' if include_memory else 'disabled'})
✓ Comparative analysis ({'enabled' if include_compare else 'disabled'})
✓ Concurrent performance ({'enabled' if include_concurrent else 'disabled'})
✓ Statistical analysis
✓ Performance regression tests

To run benchmarks:
- Python: pytest {benchmark_file} --benchmark-only
- Generate HTML report: pytest {benchmark_file} --benchmark-html=report.html
- Compare with baseline: pytest {benchmark_file} --benchmark-compare=baseline.json
"""

        except Exception as e:
            return f"Error generating benchmarks: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


class TestPropertyCommand(SlashCommand):
    """Generate property-based tests."""

    def __init__(self):
        super().__init__(
            name="test-property",
            description="Generate property-based tests",
            aliases=["property-test", "hypothesis"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the test-property command."""
        if not args:
            return "Usage: /test-property <filename>. Generate property-based tests for the specified file."

        file_path = args[0]
        file_ops = FileOperations(context.working_directory)

        try:
            # Read the source file
            content = await file_ops.read_file(file_path)
            language = file_ops.detect_language(file_path)

            # Build property-based test prompt
            prompt = f"""Generate property-based tests for the following {language} code:

Requirements:
1. Identify mathematical properties and invariants
2. Generate appropriate test data generators
3. Test edge cases with random inputs
4. Include state machine tests if applicable
5. Test commutativity, associativity, idempotency where relevant
6. Include serialization/deserialization property tests
7. Use Hypothesis (Python) or equivalent framework
8. Include strategies for complex data types

Code to test:
```{language}
{content}
```

For each function/method, identify and test:
- Idempotent properties
- Commutative properties
- Associative properties
- Round-trip properties
- Monotonic properties
- Conservation properties

Generate complete property-based test file."""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": "You are an expert in property-based testing. Identify invariants and properties that should always hold true.",
                        "name": "PropertyTestGenerator",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            test_content = response.content.strip()

            # Determine test file path
            test_dir = Path(context.working_directory) / "tests" / "properties"
            test_dir.mkdir(parents=True, exist_ok=True)

            test_file = test_dir / f"properties_{Path(file_path).stem}.py"

            # Extract and save test code
            if "```" in test_content:
                start = test_content.find("```") + 3
                end = test_content.find("```", start)
                if end != -1:
                    test_content = test_content[start:end]

            await file_ops.write_file(str(test_file), test_content)

            # Count properties found
            property_count = test_content.count("@given") if language == "python" else 0

            return f"""Generated property-based tests
- Test file: {test_file}
- Properties tested: {property_count}

Property types identified and tested:
✓ Idempotent operations
✓ Commutative operations
✓ Associative operations
✓ Round-trip serialization
✓ Mathematical invariants
✓ State machine transitions

To run property tests:
- Python: pytest {test_file}
- Run with many examples: pytest {test_file} --hypothesis-examples=1000
- Generate failing examples: pytest {test_file} --hypothesis-seed=123
"""

        except Exception as e:
            return f"Error generating property tests: {e}"

    def get_min_args(self) -> int:
        return 1

    def requires_file(self) -> bool:
        return True


class TestFuzzCommand(SlashCommand):
    """Generate fuzz testing setup."""

    def __init__(self):
        super().__init__(
            name="test-fuzz",
            description="Generate fuzz testing setup",
            aliases=["fuzz", "fuzzer"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the test-fuzz command."""
        if not args:
            return "Usage: /test-fuzz <function_name>. Generate fuzz testing for the specified function."

        target_function = args[0]
        file_path = args[1] if len(args) > 1 else None

        try:
            # If file provided, read its content
            file_content = ""
            if file_path and Path(file_path).exists():
                file_ops = FileOperations(context.working_directory)
                file_content = await file_ops.read_file(file_path)

            # Build fuzz test prompt
            prompt = f"""Generate a comprehensive fuzz testing setup for function: {target_function}

File context: {file_path or "Current working directory"}

Requirements:
1. Create fuzz harness that generates random inputs
2. Include input validation and sanitization tests
3. Test boundary conditions and overflow scenarios
4. Include mutation-based fuzzing
5. Add corpus management for interesting inputs
6. Include crash detection and reporting
7. Set up continuous fuzzing integration
8. Use AFL (Python), libFuzzer (C/C++), or Go-fuzz

File content if available:
{file_content}

Generate complete fuzz testing setup including:
- Fuzz harness implementation
- Build configuration
- Dictionary for structured inputs
- Corpus management scripts
- Integration with CI/CD"""

            # Get AI response
            response = await context.provider.client.send_request(
                [
                    {
                        "role": "system",
                        "content": "You are a fuzz testing expert. Create comprehensive fuzzing setups that find security vulnerabilities and crashes.",
                        "name": "FuzzTestGenerator",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            fuzz_content = response.content.strip()

            # Create fuzz directory
            fuzz_dir = Path(context.working_directory) / "fuzz"
            fuzz_dir.mkdir(parents=True, exist_ok=True)

            # Save multiple files if present
            files = {}
            if "```" in fuzz_content:
                # Extract all code blocks
                import re

                pattern = r"```(\w+)?\n(.*?)```"
                matches = re.findall(pattern, fuzz_content, re.DOTALL)

                for lang, code in matches:
                    if lang:
                        ext = self._get_extension_for_lang(lang)
                        filename = f"fuzz_{target_function}.{ext}"
                        files[filename] = code.strip()
                    else:
                        # Default to Python if no language specified
                        files[f"fuzz_{target_function}.py"] = code.strip()

            # Save files
            file_ops = FileOperations(context.working_directory)
            for filename, content in files.items():
                await file_ops.write_file(str(fuzz_dir / filename), content)

            return f"""Generated fuzz testing setup
- Directory: {fuzz_dir}
- Target function: {target_function}
- Files created: {list(files.keys())}

Fuzz testing features:
✓ Random input generation
✓ Mutation-based fuzzing
✓ Crash detection
✓ Corpus management
✓ CI/CD integration

To run fuzz tests:
- Python: python -m afl {fuzz_dir}/fuzz_{target_function}.py
- Set duration: python -m afl -t 60 {fuzz_dir}/fuzz_{target_function}.py
- View corpus: ls -la {fuzz_dir}/corpus/
- Review crashes: ls -la {fuzz_dir}/crashes/
"""

        except Exception as e:
            return f"Error generating fuzz tests: {e}"

    def _get_extension_for_lang(self, lang: str) -> str:
        """Get file extension for language."""
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "c++": "cpp",
            "go": "go",
            "rust": "rs",
        }
        return extensions.get(lang.lower(), "py")

    def get_min_args(self) -> int:
        return 1


class CoverageMergeCommand(SlashCommand):
    """Merge coverage reports from multiple sources."""

    def __init__(self):
        super().__init__(
            name="coverage-merge",
            description="Merge multiple coverage reports",
            aliases=["merge-cov", "combine-coverage"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the coverage-merge command."""
        if not args:
            return """Usage: /coverage-merge <report_paths> [output_format]
Arguments:
- report_paths: Glob patterns or paths to coverage files
- output_format: html, xml, json, lcov (default: html)

Examples:
- /coverage-merge coverage_*.xml
- /coverage-merge **/coverage.json xml
- /coverage-merge test1/.coverage test2/.coverage html"""

        report_paths = args
        output_format = "html"

        # Check if last argument is a format
        if args and args[-1].lower() in ["html", "xml", "json", "lcov"]:
            output_format = args[-1].lower()
            report_paths = args[:-1]

        try:
            # Build merge script
            merge_script = f'''"""Coverage report merger."""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any

def merge_coverage_reports(report_paths: List[str], output_format: str = "html"):
    """Merge coverage reports from multiple sources."""
    merged_data = {{
        "files": {{}},
        "summary": {{
            "covered_lines": 0,
            "total_lines": 0,
            "coverage": 0.0
        }}
    }}

    total_files = set()

    for path_pattern in report_paths:
        # Find matching files
        import glob
        for report_file in glob.glob(path_pattern):
            print("Processing: {{report_file}}")

            if report_file.endswith('.json'):
                data = _load_json_coverage(report_file)
            elif report_file.endswith('.xml'):
                data = _load_xml_coverage(report_file)
            elif report_file.endswith('.lcov'):
                data = _load_lcov_coverage(report_file)
            else:
                print("Skipping unsupported format: {{report_file}}")
                continue

            # Merge data
            _merge_data(merged_data, data)

    # Calculate final coverage
    if merged_data["summary"]["total_lines"] > 0:
        merged_data["summary"]["coverage"] = (
            merged_data["summary"]["covered_lines"] /
            merged_data["summary"]["total_lines"] * 100
        )

    # Output merged report
    _output_report(merged_data, output_format)

    return merged_data

def _load_json_coverage(file_path: str) -> Dict:
    """Load JSON coverage report."""
    with open(file_path, 'r') as f:
        return json.load(f)

def _load_xml_coverage(file_path: str) -> Dict:
    """Load XML coverage report (Cobertura format)."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Convert XML to internal format
    data = {{
        "files": {{}},
        "summary": {{
            "covered_lines": int(root.get("lines-covered", 0)),
            "total_lines": int(root.get("lines-valid", 0))
        }}
    }}

    for classes in root.findall(".//classes"):
        for cls in classes.findall("class"):
            filename = cls.get("filename", "")
            if filename not in data["files"]:
                data["files"][filename] = {{
                    "lines": {{}},
                    "covered_lines": 0,
                    "total_lines": 0
                }}

            for line in cls.findall(".//line"):
                line_num = int(line.get("number", 0))
                hits = int(line.get("hits", 0))
                data["files"][filename]["lines"][line_num] = hits

                if hits > 0:
                    data["files"][filename]["covered_lines"] += 1
                data["files"][filename]["total_lines"] += 1

    return data

def _load_lcov_coverage(file_path: str) -> Dict:
    """Load LCOV coverage report."""
    data = {{
        "files": {{}},
        "summary": {{
            "covered_lines": 0,
            "total_lines": 0
        }}
    }}

    current_file = None

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("SF:"):
                current_file = line[3:].strip()
                data["files"][current_file] = {{
                    "lines": {{}},
                    "covered_lines": 0,
                    "total_lines": 0
                }}
            elif line.startswith("DA:") and current_file:
                parts = line[3:].strip().split(",")
                line_num = int(parts[0])
                hits = int(parts[1])
                data["files"][current_file]["lines"][line_num] = hits

                if hits > 0:
                    data["files"][current_file]["covered_lines"] += 1
                data["files"][current_file]["total_lines"] += 1

    # Update summary
    for file_data in data["files"].values():
        data["summary"]["covered_lines"] += file_data["covered_lines"]
        data["summary"]["total_lines"] += file_data["total_lines"]

    return data

def _merge_data(merged: Dict, new_data: Dict):
    """Merge new coverage data into merged data."""
    for filename, file_data in new_data.get("files", {{}}).items():
        if filename not in merged["files"]:
            merged["files"][filename] = {{
                "lines": {{}},
                "covered_lines": 0,
                "total_lines": 0
            }}

        # Merge line coverage
        for line_num, hits in file_data.get("lines", {{}}).items():
            if line_num in merged["files"][filename]["lines"]:
                # Take max coverage for merged reports
                merged["files"][filename]["lines"][line_num] = max(
                    merged["files"][filename]["lines"][line_num],
                    hits
                )
            else:
                merged["files"][filename]["lines"][line_num] = hits

        # Recalculate file coverage
        file_lines = merged["files"][filename]["lines"]
        merged["files"][filename]["covered_lines"] = sum(1 for h in file_lines.values() if h > 0)
        merged["files"][filename]["total_lines"] = len(file_lines)

    # Update summary
    merged["summary"]["covered_lines"] = sum(
        f["covered_lines"] for f in merged["files"].values()
    )
    merged["summary"]["total_lines"] = sum(
        f["total_lines"] for f in merged["files"].values()
    )

def _output_report(data: Dict, format: str):
    """Output merged coverage report."""
    output_dir = Path("coverage_merged")
    output_dir.mkdir(exist_ok=True)

    if format == "json":
        output_file = output_dir / "coverage.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print("JSON report saved to: {{output_file}}")

    elif format == "xml":
        # Convert to Cobertura XML
        root = ET.Element("coverage")
        root.set("lines-covered", str(data["summary"]["covered_lines"]))
        root.set("lines-valid", str(data["summary"]["total_lines"]))
        root.set("line-rate", "data['summary']['coverage']/100:.4f")

        sources = ET.SubElement(root, "sources")
        ET.SubElement(sources, "source").text = "."

        packages = ET.SubElement(root, "packages")
        package = ET.SubElement(packages, "package")
        package.set("name", "merged")
        package.set("line-rate", "data['summary']['coverage']/100:.4f")

        classes = ET.SubElement(package, "classes")
        for filename, file_data in data["files"].items():
            cls = ET.SubElement(classes, "class")
            cls.set("filename", filename)
            cls.set("line-rate", "file_data['covered_lines']/file_data['total_lines'] if file_data['total_lines'] > 0 else 0:.4f")

            methods = ET.SubElement(cls, "methods")
            lines = ET.SubElement(cls, "lines")

            for line_num, hits in file_data["lines"].items():
                line = ET.SubElement(lines, "line")
                line.set("number", str(line_num))
                line.set("hits", str(hits))

        tree = ET.ElementTree(root)
        output_file = output_dir / "coverage.xml"
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print("XML report saved to: {{output_file}}")

    elif format == "html":
        # Generate HTML report
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '    <title>Merged Coverage Report</title>',
            '    <style>',
            '        body {{ font-family: Arial, sans-serif; margin: 20px; }}',
            '        table {{ border-collapse: collapse; width: 100%; }}',
            '        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}',
            '        th {{ background-color: #f2f2f2; }}',
            '        .low {{ background-color: #ffcccc; }}',
            '        .medium {{ background-color: #ffffcc; }}',
            '        .high {{ background-color: #ccffcc; }}',
            '    </style>',
            '</head>',
            '<body>',
            '    <h1>Merged Coverage Report</h1>',
            '    <h2>Summary</h2>',
            '    <p>Total Lines: {{data["summary"]["total_lines"]}}</p>',
            '    <p>Covered Lines: {{data["summary"]["covered_lines"]}}</p>',
            '    <p>Coverage: {{data["summary"]["coverage"]:.2f}}%</p>',
            '    <h2>File Coverage</h2>',
            '    <table>',
            '        <tr>',
            '            <th>File</th>',
            '            <th>Coverage</th>',
            '            <th>Covered / Total</th>',
            '        </tr>'
        ]

        for filename, file_data in data["files"].items():
            coverage = (
                file_data["covered_lines"] / file_data["total_lines"] * 100
                if file_data["total_lines"] > 0 else 0
            )
            css_class = "high" if coverage >= 80 else "medium" if coverage >= 60 else "low"

            html_parts.extend([
                '        <tr class="{{css_class}}">',
                '            <td>{{filename}}</td>',
                '            <td>{{coverage:.2f}}%</td>',
                '            <td>{{file_data["covered_lines"]}} / {{file_data["total_lines"]}}</td>',
                '        </tr>'
            ])

        html_parts.extend([
            '    </table>',
            '</body>',
            '</html>'
        ])

        html_content = '\n'.join(html_parts)

        output_file = output_dir / "index.html"
        with open(output_file, 'w') as f:
            f.write(html_content)
        print("HTML report saved to: {{output_file}}")

    elif format == "lcov":
        # Generate LCOV format
        output_file = output_dir / "coverage.lcov"
        with open(output_file, 'w') as f:
            f.write("TN:\\n")
            for filename, file_data in data["files"].items():
                f.write(f"SF:{{filename}}\\n")
                for line_num, hits in file_data["lines"].items():
                    f.write(f"DA:{{line_num}},{{hits}}\\n")
                f.write("end_of_record\\n")
        print("LCOV report saved to: {{output_file}}")

if __name__ == "__main__":
    import sys
    report_paths = {report_paths!r}
    output_format = "{output_format}"

    result = merge_coverage_reports(report_paths, output_format)
    print("\\nMerged coverage: {{result['summary']['coverage']:.2f}}%")
'''

            # Save merge script
            merge_file = Path(context.working_directory) / "merge_coverage.py"
            file_ops = FileOperations(context.working_directory)
            await file_ops.write_file(str(merge_file), merge_script)

            # Run the merge script
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, str(merge_file)],
                capture_output=True,
                text=True,
                cwd=context.working_directory,
            )

            return f"""Coverage merge completed successfully!
- Report format: {output_format}
- Input patterns: {', '.join(report_paths)}
- Merge script: {merge_file}

{result.stdout if result.returncode == 0 else result.stderr}

Output directory: coverage_merged/
- Open the report: open coverage_merged/index.html (if HTML format)
"""

        except Exception as e:
            return f"Error merging coverage: {e}"

    def get_min_args(self) -> int:
        return 1


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(TestSmartCommand())
command_registry.register(TestE2ECommand())
command_registry.register(BenchmarkCommand())
command_registry.register(TestPropertyCommand())
command_registry.register(TestFuzzCommand())
command_registry.register(CoverageMergeCommand())


def register():
    """Register all advanced test commands."""
    return [
        TestSmartCommand(),
        TestE2ECommand(),
        BenchmarkCommand(),
        TestPropertyCommand(),
        TestFuzzCommand(),
        CoverageMergeCommand(),
    ]
