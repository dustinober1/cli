# Vibe Coder 🐍✨

A powerful, provider-independent CLI coding assistant built with Python. Chat with any AI model (OpenAI, Anthropic, local LLMs) through a beautiful terminal interface.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🌟 Features

- **🔌 Provider Independent**: Works with OpenAI, Anthropic, Ollama, LM Studio, vLLM, LocalAI, or any custom endpoint
- **💬 40+ Slash Commands**: `/code`, `/fix`, `/test`, `/review`, `/refactor`, `/commit`, `/pr`, and more
- **🎨 Beautiful CLI**: Rich terminal output with syntax highlighting, tables, and progress bars
- **🛠️ Developer Tools**: AST-based repo mapping, auto-healing, smart code application
- **🔒 Privacy First**: Offline mode, local embeddings, no cloud dependencies
- **💰 Cost Tracking**: Real-time token counting and budget management

---

## 🚀 Quick Start

### Installation

```bash
# Using pipx (recommended)
pipx install vibe-coder

# Using pip
pip install vibe-coder

# From source
git clone https://github.com/dustinober1/cli.git
cd cli
poetry install
```

### First Run

```bash
# Configure a provider
vibe-coder setup

# Start chatting
vibe-coder chat

# Get help
vibe-coder --help
```

---

## 📖 Usage

### Configure Providers

```bash
# Interactive wizard
vibe-coder setup

# OpenAI Example
Endpoint: https://api.openai.com/v1
API Key: sk-...
Model: gpt-4

# Anthropic Example  
Endpoint: https://api.anthropic.com/v1
API Key: sk-ant-...
Model: claude-3-5-sonnet-20241022

# Local Ollama Example
Endpoint: http://localhost:11434/v1
API Key: (not needed)
Model: llama2
```

### Chat with AI

```bash
# Use default provider
vibe-coder chat

# Use specific provider
vibe-coder chat --provider my-openai

# Override model
vibe-coder chat --model gpt-4-turbo
```

---

## 💡 Slash Commands

### Core Commands
- `/help` - Show all commands
- `/clear` - Clear conversation history
- `/exit` - Save and quit
- `/mode [mode]` - Switch to code/architect/ask/audit mode

### File & Context
- `/add [file/glob]` - Add files to context (`/add src/**/*.py`)
- `/drop [file]` - Remove files from context
- `/ls` - List files in context
- `/tree` - Show project structure
- `/map` - Generate AST-based repo map

### AI Coding
- `/code [prompt]` - Generate code
- `/fix` - Fix the last error or highlighted code
- `/test` - Generate unit tests
- `/doc` - Generate documentation
- `/refactor` - Suggest refactoring
- `/review` - Code review git diff
- `/explain [code]` - Explain code functionality

### Git Integration
- `/commit` - Generate commit message and commit
- `/push` - Push with safety checks
- `/pr` - Generate pull request description
- `/branch [name]` - Create and switch branch

### Model Management
- `/model [name]` - Switch model
- `/provider [name]` - Switch provider
- `/tokens` - Show token usage
- `/cost` - Estimate cost

---

## 🎯 Examples

### Generate Code

```
You: /code write a Python function to parse JSON with error handling