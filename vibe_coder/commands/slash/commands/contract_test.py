"""API contract testing slash command."""

import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class ContractTestCommand(SlashCommand):
    """Generate contract tests for APIs."""

    def __init__(self):
        super().__init__(
            name="contract-test",
            description="Generate contract tests for APIs",
            aliases=["pact", "api-contract"],
            category="test",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the contract-test command."""
        if not args:
            return """Usage: /contract-test <api_spec> [options]
Options:
- --framework <tool>: Contract testing framework (pact, spring-cloud-contract, newman)
- --consumer <name>: Consumer application name
- --provider <name>: Provider service name
- --tests <dir>: Output directory for tests
- --mocks: Generate mock server definitions

Examples:
- /contract-test api.yaml
- /contract-test openapi.json --framework pact --consumer web-app
- /contract-test postman.json --framework newman --tests contract_tests/"""

        api_spec = args[0]
        options = {arg[2:]: arg[4:] if arg.startswith("--") and "=" in arg else True
                  for arg in args[1:] if arg.startswith("--")}

        framework = options.get("framework", "pact")
        consumer = options.get("consumer", "consumer")
        provider = options.get("provider", "provider")
        tests_dir = options.get("tests", "contract_tests")
        generate_mocks = options.get("mocks", False)

        file_ops = FileOperations(context.working_directory)

        try:
            # Parse API specification
            api_content = await file_ops.read_file(api_spec)
            api_spec_type = await self._detect_spec_type(api_spec, api_content)

            # Extract contracts from spec
            contracts = await self._extract_contracts(api_content, api_spec_type, context)

            if not contracts:
                return f"✅ No contracts found in {api_spec}"

            # Generate contract tests
            test_files = await self._generate_contract_tests(
                contracts, framework, consumer, provider, context
            )

            # Create output directory
            Path(tests_dir).mkdir(exist_ok=True)

            # Save test files
            saved_files = []
            for filename, content in test_files.items():
                file_path = Path(tests_dir) / filename
                await file_ops.write_file(str(file_path), content)
                saved_files.append(filename)

            # Generate mocks if requested
            mock_files = []
            if generate_mocks:
                mocks = await self._generate_mocks(contracts, framework, context)
                for filename, content in mocks.items():
                    file_path = Path(tests_dir) / filename
                    await file_ops.write_file(str(file_path), content)
                    mock_files.append(filename)

            output = [f"📋 Contract Tests Generated"]
            output.append(f"API Spec: {api_spec} ({api_spec_type})")
            output.append(f"Framework: {framework}")
            output.append(f"Consumer: {consumer}")
            output.append(f"Provider: {provider}")
            output.append(f"Directory: {tests_dir}")
            output.append(f"\nTest files created: {len(saved_files)}")
            for file in saved_files:
                output.append(f"  • {file}")

            if mock_files:
                output.append(f"\nMock files created: {len(mock_files)}")
                for file in mock_files:
                    output.append(f"  • {file}")

            output.append("\nTo run tests:")
            if framework == "pact":
                output.append("  pip install pact-python")
                output.append("  pytest contract_tests/")
            elif framework == "newman":
                output.append("  npm install -g newman")
                output.append(f"  newman run {tests_dir}/collection.json")
            elif framework == "spring-cloud-contract":
                output.append("  ./gradlew contractTest")

            return '\n'.join(output)

        except Exception as e:
            return f"Error generating contract tests: {e}"

    async def _detect_spec_type(self, filename: str, content: str) -> str:
        """Detect the API specification type."""
        # Check file extension
        ext = Path(filename).suffix.lower()

        if ext == '.json':
            try:
                data = json.loads(content)
                if 'openapi' in data or 'swagger' in data:
                    return 'openapi'
                elif 'info' in data and 'paths' in data:
                    return 'openapi'
                elif 'item' in data or 'info' in data:
                    return 'postman'
            except:
                pass
        elif ext in ['.yaml', '.yml']:
            if 'openapi:' in content.lower() or 'swagger:' in content.lower():
                return 'openapi'

        # Default assumption
        return 'openapi'

    async def _extract_contracts(self, content: str, spec_type: str, context: CommandContext) -> List[Dict]:
        """Extract contract definitions from API spec."""
        prompt = f"""Extract API contracts from this {spec_type} specification:

Content:
{content[:3000]}...

Requirements:
1. Extract all endpoints with methods, paths, and schemas
2. Identify request/response structures
3. Extract status codes and error responses
4. Document authentication requirements
5. Include query parameters and headers
6. Group by resource/collection

Return a structured list of contracts with:
- Method and path
- Request schema
- Response schema(s)
- Status codes
- Headers
- Authentication"""

        response = await context.provider.client.send_request([
            {"role": "system", "content": "You are an API contract specialist. Extract clear, structured contracts from API specifications.",
             "name": "ContractExtractor"},
            {"role": "user", "content": prompt}
        ])

        # Try to parse the response as JSON
        try:
            return json.loads(response.content.strip())
        except:
            # Fallback: return empty list if parsing fails
            return []

    async def _generate_contract_tests(self, contracts: List[Dict], framework: str,
                                    consumer: str, provider: str, context: CommandContext) -> Dict[str, str]:
        """Generate contract test files."""

        prompt = f"""Generate {framework} contract tests for these API contracts:

Contracts:
{contracts}

Requirements:
1. Framework: {framework}
2. Consumer: {consumer}
3. Provider: {provider}
4. Generate positive and negative test cases
5. Include request/response validations
6. Handle authentication
7. Generate proper assertions
8. Follow {framework} best practices

Generate complete test files that can be run directly."""

        response = await context.provider.client.send_request([
            {"role": "system", "content": f"You are a contract testing expert using {framework}. Generate comprehensive, runnable contract tests.",
             "name": "ContractTestGenerator"},
            {"role": "user", "content": prompt}
        ])

        # Parse response to extract files
        content = response.content.strip()

        # Simple file extraction - look for code blocks with filenames
        files = {}
        file_pattern = r'```(\w+)?\n?(?:#? ?(.+?)\n)?((?:.|\n)*?)```'

        for match in re.finditer(file_pattern, content):
            lang = match.group(1) or ''
            filename = match.group(2) or f'test.{lang}'
            code = match.group(3)

            if filename and code:
                # Add proper extension if missing
                if not Path(filename).suffix:
                    if 'python' in lang or 'pytest' in code:
                        filename += '.py'
                    elif 'javascript' in lang or 'newman' in code:
                        filename += '.js'
                    elif 'java' in lang:
                        filename += '.java'
                    elif 'groovy' in lang:
                        filename += '.groovy'

                files[filename] = code

        # Fallback: return single file
        if not files:
            files = {'contract_tests.py': content}

        return files

    async def _generate_mocks(self, contracts: List[Dict], framework: str, context: CommandContext) -> Dict[str, str]:
        """Generate mock server definitions."""

        prompt = f"""Generate mock server definitions for these API contracts:

Contracts:
{contracts}

Requirements:
1. Framework: {framework}
2. Generate mock server setup
3. Include request/response matching
4. Add state management if needed
5. Generate sample data
6. Include error scenarios

Create complete mock server configuration."""

        response = await context.provider.client.send_request([
            {"role": "system", "content": f"You are a mock server expert. Generate realistic mock servers based on API contracts.",
             "name": "MockGenerator"},
            {"role": "user", "content": prompt}
        ])

        content = response.content.strip()

        # Extract files similar to test generation
        files = {}
        if 'pact' in framework.lower():
            # Pact might generate provider states
            files['provider_states.js'] = content
        else:
            files['mock_server.js'] = content

        return files


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(ContractTestCommand())

def register():
    """Register all contract test commands."""
    return [
        ContractTestCommand(),
    ]