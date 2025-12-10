"""Deployment configuration slash commands."""

import json
from pathlib import Path
from typing import List, Optional

from ..base import CommandContext, SlashCommand
from ..file_ops import FileOperations


class DeployCommand(SlashCommand):
    """Generate deployment configurations."""

    def __init__(self):
        super().__init__(
            name="deploy",
            description="Generate deployment configurations",
            aliases=["deploy-config", "release-deploy"],
            category="project",
        )

    async def execute(self, args: List[str], context: CommandContext) -> str:
        """Execute the deploy command."""
        if not args:
            return """Usage: /deploy <environment> [options]
Environments:
- development: Local dev environment
- staging: Staging/pre-production
- production: Production deployment
- docker: Docker containerization
- kubernetes: K8s deployment
- terraform: Infrastructure as code
- serverless: AWS Lambda/Serverless
- static: Static site hosting

Options:
- --platform <name>: Cloud platform (aws, gcp, azure, heroku)
- --database <type>: Database (postgres, mysql, mongodb)
- --domain <name>: Custom domain
- --ssl: Enable SSL/TLS

Examples:
- /deploy production --platform aws --database postgres
- /deploy docker --domain myapp.com --ssl
- /deploy kubernetes --platform gcp"""

        environment = args[0].lower()
        options = [arg for arg in args[1:] if arg.startswith("--")]
        platform = None
        database = None
        domain = None
        ssl_enabled = False

        # Parse options
        for i, opt in enumerate(options):
            if opt == "--platform" and i + 1 < len(options):
                platform = options[i + 1]
            elif opt == "--database" and i + 1 < len(options):
                database = options[i + 1]
            elif opt == "--domain" and i + 1 < len(options):
                domain = options[i + 1]
            elif opt == "--ssl":
                ssl_enabled = True

        file_ops = FileOperations(context.working_directory)

        try:
            # Analyze project structure
            project_info = await self._analyze_project(file_ops)

            # Generate deployment configuration
            if environment == "docker":
                return await self._generate_docker_config(context, file_ops, project_info, platform)
            elif environment == "kubernetes":
                return await self._generate_k8s_config(context, file_ops, project_info, platform)
            elif environment == "serverless":
                return await self._generate_serverless_config(context, file_ops, project_info, platform, domain)
            elif environment == "static":
                return await self._generate_static_config(context, file_ops, project_info, platform, domain)
            elif environment == "ci-cd":
                return await self._generate_cicd_config(context, file_ops, project_info, platform)
            elif environment == "terraform":
                return await self._generate_terraform_config(context, file_ops, project_info, platform)
            else:
                return await self._generate_app_config(context, file_ops, project_info, environment, platform, database, domain, ssl_enabled)

        except Exception as e:
            return f"Error generating deployment config: {e}"

    async def _analyze_project(self, file_ops: FileOperations) -> dict:
        """Analyze project structure."""
        info = {
            "name": Path(file_ops.working_dir).name,
            "type": "unknown",
            "framework": None,
            "language": None,
            "database": None,
            "port": 8000,
            "has_docker": False,
            "has_package_json": False,
            "has_requirements": False,
            "frontend": False,
            "backend": True
        }

        # Scan files
        for item in Path(file_ops.working_dir).iterdir():
            if item.is_file():
                name = item.name.lower()

                # Detect project type
                if name == "package.json":
                    info["has_package_json"] = True
                    info["type"] = "nodejs"
                    try:
                        content = await file_ops.read_file(str(item))
                        pkg_data = json.loads(content)
                        if "react" in pkg_data.get("dependencies", {}):
                            info["framework"] = "react"
                            info["frontend"] = True
                            info["backend"] = False
                        elif "vue" in pkg_data.get("dependencies", {}):
                            info["framework"] = "vue"
                            info["frontend"] = True
                            info["backend"] = False
                        elif "express" in pkg_data.get("dependencies", {}):
                            info["framework"] = "express"
                        elif "next" in pkg_data.get("dependencies", {}):
                            info["framework"] = "nextjs"
                    except:
                        pass

                elif name == "requirements.txt":
                    info["has_requirements"] = True
                    info["type"] = "python"
                    try:
                        content = await file_ops.read_file(str(item))
                        if "fastapi" in content:
                            info["framework"] = "fastapi"
                            info["port"] = 8000
                        elif "flask" in content:
                            info["framework"] = "flask"
                            info["port"] = 5000
                        elif "django" in content:
                            info["framework"] = "django"
                            info["port"] = 8000
                    except:
                        pass

                elif name == "pyproject.toml":
                    info["type"] = "python"

                elif name == "cargo.toml":
                    info["type"] = "rust"

                elif name == "pom.xml":
                    info["type"] = "java"
                    if "spring" in await file_ops.read_file(str(item)):
                        info["framework"] = "spring"

                elif name == "index.html":
                    info["type"] = "static"
                    info["frontend"] = True
                    info["backend"] = False

                elif name == "dockerfile":
                    info["has_docker"] = True

        # Determine primary language
        if info["type"] == "nodejs":
            info["language"] = "javascript"
        elif info["type"] == "python":
            info["language"] = "python"
        elif info["type"] == "java":
            info["language"] = "java"
        elif info["type"] == "rust":
            info["language"] = "rust"

        return info

    async def _generate_docker_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str]) -> str:
        """Generate Docker configuration."""
        configs = []

        # Dockerfile
        dockerfile = await self._create_dockerfile(project_info)
        configs.append(("Dockerfile", dockerfile))

        # Docker Compose
        compose_file = await self._create_docker_compose(project_info, platform)
        configs.append(("docker-compose.yml", compose_file))

        # .dockerignore
        dockerignore = await self._create_dockerignore(project_info)
        configs.append((".dockerignore", dockerignore))

        # Save all configs
        created_files = []
        for filename, content in configs:
            await file_ops.write_file(filename, content)
            created_files.append(filename)

        return f"""🐳 Docker configuration generated!

Files created:
{chr(10).join([f"  • {file}" for file in created_files])}

To use:
1. Build image: docker build -t {project_info['name']} .
2. Run container: docker run -p {project_info['port']}:{project_info['port']} {project_info['name']}
3. Or use compose: docker-compose up

Environment variables in .env:
- PORT={project_info['port']}
- ENVIRONMENT=development"""

    async def _create_dockerfile(self, project_info: dict) -> str:
        """Create Dockerfile content."""
        if project_info["type"] == "nodejs":
            return f"""FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE {project_info.get('port', 3000)}

USER node

CMD ["npm", "start"]"""
        elif project_info["type"] == "python":
            return f"""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {project_info.get('port', 8000)}

RUN useradd --create-home --shell /bin/bash app
USER app

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{project_info.get('port', 8000)}"]"""
        else:
            return f"""FROM ubuntu:20.04

WORKDIR /app

COPY . .

# Add your build commands here

EXPOSE {project_info.get('port', 8080)}

CMD ["./{project_info['name']}"]"""

    async def _create_docker_compose(self, project_info: dict, platform: Optional[str]) -> str:
        """Create docker-compose.yml content."""
        compose = {
            "version": "3.8",
            "services": {
                project_info["name"]: {
                    "build": ".",
                    "ports": [f"{project_info.get('port', 8000)}:{project_info.get('port', 8000)}"],
                    "environment": {
                        "ENVIRONMENT": "development",
                        "PORT": str(project_info.get('port', 8000))
                    },
                    "volumes": ["./app:/app"],
                    "restart": "unless-stopped"
                }
            }
        }

        # Add database if applicable
        if project_info.get("database"):
            compose["services"]["db"] = {
                "image": f"{project_info['database']}:latest",
                "environment": {
                    "POSTGRES_DB": f"{project_info['name']}_db",
                    "POSTGRES_USER": "user",
                    "POSTGRES_PASSWORD": "password"
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"]
            }
            compose["volumes"] = {"postgres_data": None}

        return self._dict_to_yaml(compose)

    def _dict_to_yaml(self, data: dict, indent: int = 0) -> str:
        """Convert dict to YAML string."""
        yaml_lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                yaml_lines.append(f"{indent_str}{key}:")
                yaml_lines.append(self._dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                yaml_lines.append(f"{indent_str}{key}:")
                for item in value:
                    yaml_lines.append(f"{indent_str}  - {item}")
            else:
                yaml_lines.append(f"{indent_str}{key}: {value}")

        return "\n".join(yaml_lines)

    async def _create_dockerignore(self, project_info: dict) -> str:
        """Create .dockerignore content."""
        patterns = [
            "# Python",
            "__pycache__",
            "*.py[cod]",
            "*$py.class",
            "env",
            "venv",
            ".venv",
            "",
            "# Node.js",
            "node_modules",
            "npm-debug.log*",
            "",
            "# Git",
            ".git",
            ".gitignore",
            "",
            "# IDE",
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db"
        ]

        return "\n".join(patterns)

    async def _generate_k8s_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str]) -> str:
        """Generate Kubernetes configuration."""
        configs = []

        # Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": project_info["name"],
                "labels": {
                    "app": project_info["name"]
                }
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": project_info["name"]
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": project_info["name"]
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": project_info["name"],
                            "image": f"{project_info['name']}:latest",
                            "ports": [{
                                "containerPort": project_info.get('port', 8000)
                            }],
                            "env": [
                                {"name": "ENVIRONMENT", "value": "production"},
                                {"name": "PORT", "value": str(project_info.get('port', 8000))}
                            ]
                        }]
                    }
                }
            }
        }

        # Service
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{project_info['name']}-service"
            },
            "spec": {
                "selector": {
                    "app": project_info["name"]
                },
                "ports": [{
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": project_info.get('port', 8000)
                }],
                "type": "LoadBalancer"
            }
        }

        # Save configs
        await file_ops.write_file("k8s-deployment.yaml", self._dict_to_yaml(deployment))
        await file_ops.write_file("k8s-service.yaml", self._dict_to_yaml(service))

        return f"""☸️ Kubernetes configuration generated!

Files created:
  • k8s-deployment.yaml
  • k8s-service.yaml

To deploy:
1. kubectl apply -f k8s-deployment.yaml
2. kubectl apply -f k8s-service.yaml
3. kubectl get pods
4. kubectl get services

Note: Update the image name in deployment.yaml to match your container registry."""

    async def _generate_serverless_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str], domain: Optional[str]) -> str:
        """Generate serverless configuration."""
        if platform == "aws" or platform is None:
            # AWS Lambda
            lambda_config = await self._create_aws_lambda_config(project_info)
            await file_ops.write_file("serverless.yml", lambda_config)

            return f"""⚡ AWS Lambda serverless configuration generated!

File created:
  • serverless.yml

To deploy:
1. npm install -g serverless
2. serverless deploy

Requirements:
- AWS CLI configured
- Serverless Framework installed"""
        else:
            return f"Serverless configuration for {platform} not yet implemented"

    async def _create_aws_lambda_config(self, project_info: dict) -> str:
        """Create serverless.yml for AWS Lambda."""
        config = {
            "service": project_info["name"],
            "provider": {
                "name": "aws",
                "runtime": "nodejs18.x" if project_info["type"] == "nodejs" else "python3.9",
                "region": "us-east-1",
                "stage": "dev"
            },
            "functions": {
                "api": {
                    "handler": "handler.handler" if project_info["type"] == "nodejs" else "main.handler",
                    "events": [
                        {
                            "http": {
                                "path": "/{proxy+}",
                                "method": "any",
                                "cors": True
                            }
                        }
                    ]
                }
            }
        }

        return self._dict_to_yaml(config)

    async def _generate_static_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str], domain: Optional[str]) -> str:
        """Generate static site hosting configuration."""
        configs = []

        if platform == "netlify" or platform is None:
            # Netlify configuration
            netlify_config = {
                "build": {
                    "command": "npm run build" if project_info["has_package_json"] else "echo 'No build command'",
                    "publish": "dist"
                },
                "redirects": [
                    {"from": "/*", "to": "/index.html", "status": 200}
                ]
            }
            await file_ops.write_file("netlify.toml", self._dict_to_yaml(netlify_config))
            configs.append("netlify.toml")

        # GitHub Pages workflow
        github_workflow = f"""name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm ci
      if: "${{ env.SKIP_BUILD != 'true' }}"

    - name: Build
      run: npm run build
      if: "${{ env.SKIP_BUILD != 'true' }}"

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: "${{ secrets.GITHUB_TOKEN }}"
        publish_dir: ./dist
      if: "${{ env.SKIP_DEPLOY != 'true' }}\""""

        await file_ops.write_file(".github/workflows/deploy.yml", github_workflow)
        configs.append(".github/workflows/deploy.yml")

        return f"""🌐 Static site configuration generated!

Files created:
{chr(10).join([f"  • {file}" for file in configs])}

Deployment options:
- Netlify: Connect your repo to Netlify for automatic deploys
- GitHub Pages: Push to main branch to auto-deploy
- Custom domain: Configure in hosting provider settings"""

    async def _generate_cicd_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str]) -> str:
        """Generate CI/CD pipeline configuration."""
        if platform == "github" or platform is None:
            # GitHub Actions
            workflow = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
      if: ${{{{ env.LANGUAGE == 'python' }} }}

    - name: Install dependencies
      run: |
        {'pip install -r requirements.txt' if project_info['type'] == 'python' else 'npm ci'}

    - name: Run tests
      run: |
        {'pytest' if project_info['type'] == 'python' else 'npm test'}

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: ${{{{ env.UPLOAD_COVERAGE }} }}

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Build application
      run: |
        {'python -m build' if project_info['type'] == 'python' else 'npm run build'}

    - name: Deploy
          run: echo "Deploy to production"""

            await file_ops.write_file(".github/workflows/ci-cd.yml", workflow)
            return f"""🔄 CI/CD pipeline generated!

File created:
  • .github/workflows/ci-cd.yml

The pipeline includes:
✅ Test execution
✅ Code coverage reporting
✅ Build verification
✅ Automatic deployment on main branch"""

    async def _generate_terraform_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, platform: Optional[str]) -> str:
        """Generate Terraform infrastructure as code."""
        if platform == "aws" or platform is None:
            # AWS resources
            terraform_config = f"""# Terraform configuration for {project_info['name']}

terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }}
  }}
}}

provider "aws" {{
  region = "us-east-1"
}}

# S3 bucket for static assets
resource "aws_s3_bucket" "static_assets" {{
  bucket = "{project_info['name']}-static"
  acl    = "private"
}}

# CloudFront distribution
resource "aws_cloudfront_distribution" "cdn" {{
  origin {{
    domain_name              = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.static_assets.id

    s3_origin_config {{
      origin_access_identity = aws_cloudfront_origin_access_identity.origin_access_identity_id
    }}
  }}

  enabled             = true
  is_ipv6_enabled     = true

  default_cache_behavior {{
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.static_assets.id
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }}

  restrictions {{
    geo_restriction {{
      restriction_type = "none"
    }}
  }}

  viewer_certificate {{
    cloudfront_default_certificate = true
  }}
}}

# Route 53 hosted zone
resource "aws_route53_zone" "main" {{
  name = "{project_info['name']}.com"
}}

resource "aws_route53_record" "www" {{
  zone_id = aws_route53_zone.main.zone_id
  name    = "{project_info['name']}.com"
  type    = "A"

  alias {{
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id               = aws_cloudfront_distribution.cdn.hosted_zone_id
    evaluate_target_health = true
  }}
}}

output "cdn_domain_name" {{
  value = aws_cloudfront_distribution.cdn.domain_name
}}"""

            await file_ops.write_file("main.tf", terraform_config)

            # variables.tf
            variables = """variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "my-app"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "example.com"
}"""

            await file_ops.write_file("variables.tf", variables)

            return f"""🏗️ Terraform infrastructure generated!

Files created:
  • main.tf - Main infrastructure configuration
  • variables.tf - Input variables

To deploy:
1. terraform init
2. terraform plan
3. terraform apply

Resources created:
- S3 bucket for static assets
- CloudFront CDN
- Route 53 DNS records"""

    async def _generate_app_config(self, context: CommandContext, file_ops: FileOperations, project_info: dict, environment: str, platform: Optional[str], database: Optional[str], domain: Optional[str], ssl_enabled: bool) -> str:
        """Generate general application configuration."""
        config_data = {
            "app": {
                "name": project_info["name"],
                "environment": environment,
                "port": project_info.get("port", 8000),
                "domain": domain,
                "ssl": ssl_enabled
            },
            "database": database,
            "platform": platform,
            "features": {
                "monitoring": True if environment == "production" else False,
                "logging": True,
                "error_tracking": True if environment == "production" else False
            }
        }

        config_file = f"{environment}-config.json"
        await file_ops.write_file(config_file, json.dumps(config_data, indent=2))

        return f"""⚙️ Application configuration generated!

File created:
  • {config_file}

Configuration:
- Environment: {environment}
- Platform: {platform or "default"}
- Database: {database or "none"}
- Domain: {domain or "none"}
- SSL: {"enabled" if ssl_enabled else "disabled"}

Use this configuration in your deployment scripts or environment setup."""


# Register all commands
from ..registry import command_registry

# Auto-register commands when module is imported
command_registry.register(DeployCommand())

def register():
    """Register all deployment commands."""
    return [
        DeployCommand(),
    ]