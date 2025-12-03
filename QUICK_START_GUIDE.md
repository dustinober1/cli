# Quick Start Guide for Developers

Welcome to the Vibe Coder development team! This guide will get you from zero to your first commit in under 2 hours.

---

## 🎯 Goal

By the end of this guide, you will:
1. Have the project running locally
2. Understand the codebase structure
3. Make your first code contribution
4. Run tests and see them pass
5. Be ready to pick up your first task

---

## ✅ Prerequisites

Before starting, ensure you have:

- [ ] **Node.js** version 14 or higher (`node --version`)
- [ ] **npm** or **yarn** (`npm --version`)
- [ ] **Git** installed (`git --version`)
- [ ] **TypeScript** knowledge (basic)
- [ ] A code editor (VS Code recommended)
- [ ] Terminal/command line familiarity

Optional but helpful:
- [ ] GitHub account
- [ ] Experience with Commander.js or similar CLI frameworks
- [ ] Experience with OpenAI or Anthropic APIs

---

## 🚀 Step 1: Clone and Setup (10 minutes)

### 1.1 Clone the Repository

```bash
# Clone the repo
git clone https://github.com/YOUR_ORG/vibe-coder.git
cd vibe-coder

# Create your feature branch
git checkout -b feature/your-name-setup
```

### 1.2 Install Dependencies

```bash
# Install all dependencies
npm install

# Verify installation
npm list --depth=0
```

You should see packages like:
- commander
- inquirer
- chalk
- axios
- conf
- ora
- typescript

### 1.3 Verify TypeScript Setup

```bash
# Check TypeScript version
npx tsc --version

# Try building (should fail if no files yet, that's OK)
npm run build
```

---

## 📁 Step 2: Understand the Structure (15 minutes)

### 2.1 Directory Layout

```
vibe-coder/
├── src/                    # Source code (TypeScript)
│   ├── commands/          # CLI command implementations
│   │   ├── chat.ts        # /chat command
│   │   ├── setup.ts       # /setup command
│   │   ├── config.ts      # /config command
│   │   └── slash/         # Slash command handlers
│   │       ├── core.ts    # /init, /clear, /reset, etc.
│   │       ├── files.ts   # /add, /drop, /ls, etc.
│   │       └── coding.ts  # /code, /fix, /test, etc.
│   │
│   ├── config/            # Configuration management
│   │   ├── ConfigManager.ts      # Main config class
│   │   ├── envHandler.ts         # .env file handling
│   │   └── validator.ts          # Config validation
│   │
│   ├── api/               # API client integrations
│   │   ├── BaseApiClient.ts      # Abstract base class
│   │   ├── OpenAIClient.ts       # OpenAI implementation
│   │   ├── AnthropicClient.ts    # Anthropic implementation
│   │   ├── GenericClient.ts      # Custom/generic APIs
│   │   └── ClientFactory.ts      # Creates appropriate client
│   │
│   ├── prompts/           # Interactive prompts (Inquirer)
│   │   ├── setupWizard.ts        # Initial setup flow
│   │   ├── selectProvider.ts     # Provider selection
│   │   ├── chatInterface.ts      # Main chat loop
│   │   └── manageConfig.ts       # Config management UI
│   │
│   ├── utils/             # Helper functions
│   │   ├── logger.ts             # Colored logging
│   │   ├── errorHandler.ts       # Error formatting
│   │   ├── tokenCounter.ts       # Token estimation
│   │   ├── codeFormatter.ts      # Code block parsing
│   │   ├── fileOps.ts            # File operations
│   │   ├── repoMapper.ts         # AST-based repo mapping
│   │   ├── applyEngine.ts        # Code application (diffs)
│   │   └── contextManager.ts     # Context window management
│   │
│   ├── types/             # TypeScript type definitions
│   │   ├── config.ts             # Config interfaces
│   │   ├── api.ts                # API interfaces
│   │   └── commands.ts           # Command interfaces
│   │
│   ├── rag/               # RAG and vector store
│   │   └── vectorStore.ts        # Local vector database
│   │
│   ├── integrations/      # External integrations
│   │   └── mcpClient.ts          # MCP client
│   │
│   ├── agents/            # Agentic features
│   │   └── autoHealer.ts         # Auto-healing loop
│   │
│   └── index.ts           # Main entry point (CLI)
│
├── tests/                 # Test files
│   ├── config/
│   ├── api/
│   ├── utils/
│   └── integration/
│
├── examples/              # Example configurations
│   ├── openai-config.json
│   ├── anthropic-config.json
│   └── .env.example
│
├── docs/                  # Documentation
│   ├── API.md
│   ├── USAGE.md
│   ├── SLASH_COMMANDS.md
│   └── PROVIDER_INDEPENDENCE.md
│
├── .vibe/                 # Local user data (gitignored)
│   ├── profiles/          # System prompt profiles
│   ├── vectors/           # Vector store data
│   └── map.json           # Repo map cache
│
├── dist/                  # Compiled JavaScript (gitignored)
├── node_modules/          # Dependencies (gitignored)
│
├── package.json           # Project metadata
├── tsconfig.json          # TypeScript config
├── jest.config.js         # Jest test config
├── .gitignore
├── .npmignore
├── README.md
├── IMPLEMENTATION_PLAN.md
├── ENHANCED_FEATURES_PLAN.md
├── ROADMAP.md
└── QUICK_START_GUIDE.md (this file)
```

### 2.2 Key Files to Know

**Start here:**
- `src/index.ts` - CLI entry point, command registration
- `src/types/config.ts` - Core type definitions
- `src/config/ConfigManager.ts` - How configuration works
- `package.json` - Scripts and dependencies

**Read these next:**
- `IMPLEMENTATION_PLAN.md` - All tasks broken down
- `ENHANCED_FEATURES_PLAN.md` - Slash commands and advanced features
- `ROADMAP.md` - Timeline and milestones

---

## 🏗️ Step 3: Your First Task (30 minutes)

Let's build something simple to get familiar with the codebase.

### Task: Create the Logger Utility (Task 6.1)

This is a junior-friendly task that teaches the codebase structure.

#### 3.1 Create the File

```bash
# Create the utils directory if it doesn't exist
mkdir -p src/utils

# Create the logger file
touch src/utils/logger.ts
```

#### 3.2 Write the Code

Open `src/utils/logger.ts` and add:

```typescript
import chalk from 'chalk';

/**
 * Log levels configuration
 */
const DEBUG_MODE = process.env.DEBUG === 'true';

/**
 * Log a success message with a green checkmark
 * @param message - The message to log
 *
 * @example
 * logSuccess('Configuration saved successfully');
 */
export function logSuccess(message: string): void {
  console.log(chalk.green('✓'), message);
}

/**
 * Log an error message with a red X
 * @param message - The error message to log
 *
 * @example
 * logError('Failed to connect to API');
 */
export function logError(message: string): void {
  console.error(chalk.red('✗'), message);
}

/**
 * Log a warning message with a yellow warning symbol
 * @param message - The warning message to log
 *
 * @example
 * logWarning('API key is not set, using default');
 */
export function logWarning(message: string): void {
  console.warn(chalk.yellow('⚠'), message);
}

/**
 * Log an info message with a blue info symbol
 * @param message - The info message to log
 *
 * @example
 * logInfo('Loading configuration from ~/.vibe/config.json');
 */
export function logInfo(message: string): void {
  console.log(chalk.blue('ℹ'), message);
}

/**
 * Log a debug message (only shown when DEBUG=true)
 * @param message - The debug message to log
 *
 * @example
 * logDebug('Token count: 1234');
 */
export function logDebug(message: string): void {
  if (DEBUG_MODE) {
    console.log(chalk.gray('[DEBUG]'), message);
  }
}

/**
 * Check if debug mode is enabled
 * @returns true if DEBUG environment variable is set to 'true'
 */
export function isDebugMode(): boolean {
  return DEBUG_MODE;
}
```

#### 3.3 Create a Test

Create `tests/utils/logger.test.ts`:

```typescript
import { logSuccess, logError, logWarning, logInfo, logDebug, isDebugMode } from '../../src/utils/logger';

// Mock console methods
const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;

describe('Logger Utility', () => {
  let logSpy: jest.SpyInstance;
  let errorSpy: jest.SpyInstance;
  let warnSpy: jest.SpyInstance;

  beforeEach(() => {
    logSpy = jest.spyOn(console, 'log').mockImplementation();
    errorSpy = jest.spyOn(console, 'error').mockImplementation();
    warnSpy = jest.spyOn(console, 'warn').mockImplementation();
  });

  afterEach(() => {
    logSpy.mockRestore();
    errorSpy.mockRestore();
    warnSpy.mockRestore();
  });

  test('logSuccess calls console.log with message', () => {
    logSuccess('Test success');
    expect(logSpy).toHaveBeenCalledWith(expect.any(String), 'Test success');
  });

  test('logError calls console.error with message', () => {
    logError('Test error');
    expect(errorSpy).toHaveBeenCalledWith(expect.any(String), 'Test error');
  });

  test('logWarning calls console.warn with message', () => {
    logWarning('Test warning');
    expect(warnSpy).toHaveBeenCalledWith(expect.any(String), 'Test warning');
  });

  test('logInfo calls console.log with message', () => {
    logInfo('Test info');
    expect(logSpy).toHaveBeenCalledWith(expect.any(String), 'Test info');
  });

  test('logDebug only logs when DEBUG is true', () => {
    const originalDebug = process.env.DEBUG;

    // Test with DEBUG=false
    process.env.DEBUG = 'false';
    logDebug('Should not appear');
    expect(logSpy).not.toHaveBeenCalled();

    // Test with DEBUG=true
    process.env.DEBUG = 'true';
    // Need to reload module to pick up new env var
    jest.resetModules();
    const { logDebug: debugTrue } = require('../../src/utils/logger');
    debugTrue('Should appear');
    expect(logSpy).toHaveBeenCalled();

    process.env.DEBUG = originalDebug;
  });

  test('isDebugMode returns correct value', () => {
    const originalDebug = process.env.DEBUG;

    process.env.DEBUG = 'true';
    jest.resetModules();
    const { isDebugMode: isDebugTrue } = require('../../src/utils/logger');
    expect(isDebugTrue()).toBe(true);

    process.env.DEBUG = 'false';
    jest.resetModules();
    const { isDebugMode: isDebugFalse } = require('../../src/utils/logger');
    expect(isDebugFalse()).toBe(false);

    process.env.DEBUG = originalDebug;
  });
});
```

#### 3.4 Run the Tests

```bash
# Run Jest
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode (for development)
npm test -- --watch
```

#### 3.5 Try It Out

Create a quick test file `test-logger.ts`:

```typescript
import { logSuccess, logError, logWarning, logInfo, logDebug } from './src/utils/logger';

console.log('\nTesting logger utility:\n');

logSuccess('This is a success message');
logError('This is an error message');
logWarning('This is a warning message');
logInfo('This is an info message');
logDebug('This is a debug message (set DEBUG=true to see)');

console.log('\nDone!\n');
```

Run it:

```bash
# Compile TypeScript
npm run build

# Run the test
node dist/test-logger.js

# Run with debug mode
DEBUG=true node dist/test-logger.js
```

#### 3.6 Commit Your Work

```bash
# Stage your changes
git add src/utils/logger.ts
git add tests/utils/logger.test.ts

# Commit with a good message
git commit -m "feat: implement logger utility (Task 6.1)

- Add logSuccess, logError, logWarning, logInfo, logDebug functions
- Add color coding with chalk
- Add debug mode support via DEBUG env var
- Add comprehensive unit tests
- All tests passing"

# Push to your branch
git push origin feature/your-name-setup
```

---

## 🎓 Step 4: Learn the Workflow (15 minutes)

### 4.1 Branch Naming Convention

```bash
# Features
git checkout -b feature/add-openai-client
git checkout -b feature/slash-commands

# Bug fixes
git checkout -b fix/token-counter-overflow
git checkout -b fix/config-validation

# Documentation
git checkout -b docs/update-readme
git checkout -b docs/api-reference

# Refactoring
git checkout -b refactor/simplify-api-client
```

### 4.2 Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**

```bash
git commit -m "feat(api): add Anthropic API client

- Implement AnthropicClient class extending BaseApiClient
- Handle Anthropic-specific headers and format
- Add connection validation
- Add error handling

Closes #42"
```

```bash
git commit -m "fix(config): prevent crash on missing config file

- Add existence check before reading config
- Create default config if missing
- Add helpful error message

Fixes #56"
```

### 4.3 Pull Request Process

1. **Create PR** on GitHub
2. **Fill out template:**
   - What does this PR do?
   - Which task(s) does it complete?
   - How to test it?
   - Screenshots (if UI changes)
3. **Request review** from team
4. **Address feedback**
5. **Merge** when approved

### 4.4 Code Review Checklist

Before submitting a PR, check:

- [ ] Code follows TypeScript best practices
- [ ] All functions have JSDoc comments
- [ ] Tests are written and passing
- [ ] No console.logs (use logger instead)
- [ ] Error handling is in place
- [ ] Types are properly defined (no `any`)
- [ ] Code is formatted (run `npm run format` if available)
- [ ] README updated if needed

---

## 🧪 Step 5: Running Tests (10 minutes)

### 5.1 Test Commands

```bash
# Run all tests
npm test

# Run specific test file
npm test logger.test.ts

# Run tests in watch mode
npm test -- --watch

# Run with coverage report
npm run test:coverage

# Update snapshots
npm test -- -u
```

### 5.2 Writing Tests

**Unit Test Example:**

```typescript
import { functionToTest } from '../src/utils/helper';

describe('Helper Function', () => {
  test('should return expected value', () => {
    const result = functionToTest('input');
    expect(result).toBe('expected output');
  });

  test('should handle edge case', () => {
    expect(() => functionToTest(null)).toThrow();
  });
});
```

**Integration Test Example:**

```typescript
import { ConfigManager } from '../src/config/ConfigManager';

describe('ConfigManager Integration', () => {
  let configManager: ConfigManager;

  beforeEach(() => {
    configManager = new ConfigManager();
  });

  test('should save and retrieve provider', () => {
    const provider = {
      name: 'test-provider',
      apiKey: 'test-key',
      endpoint: 'https://api.test.com'
    };

    configManager.setProvider('test', provider);
    const retrieved = configManager.getProvider('test');

    expect(retrieved).toEqual(provider);
  });
});
```

---

## 🛠️ Step 6: Development Tools (15 minutes)

### 6.1 VS Code Setup

**Recommended Extensions:**

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "orta.vscode-jest",
    "usernamehw.errorlens"
  ]
}
```

**Settings (`.vscode/settings.json`):**

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "typescript.tsdk": "node_modules/typescript/lib",
  "jest.autoRun": "off",
  "files.exclude": {
    "**/.git": true,
    "**/.DS_Store": true,
    "**/node_modules": true,
    "**/dist": true
  }
}
```

### 6.2 Debugging

**Launch Configuration (`.vscode/launch.json`):**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug CLI",
      "skipFiles": ["<node_internals>/**"],
      "program": "${workspaceFolder}/src/index.ts",
      "preLaunchTask": "npm: build",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"],
      "args": ["chat"],
      "console": "integratedTerminal"
    },
    {
      "type": "node",
      "request": "launch",
      "name": "Jest Current File",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["${fileBasenameNoExtension}", "--runInBand"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
```

### 6.3 Useful Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "dev": "tsc --watch",
    "build": "tsc",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "clean": "rm -rf dist",
    "cli": "node dist/index.js"
  }
}
```

---

## 📚 Step 7: Learning Resources (10 minutes)

### 7.1 Project Documentation

Read in this order:
1. `README.md` - Project overview
2. `IMPLEMENTATION_PLAN.md` - All tasks (Phases 1-11)
3. `ENHANCED_FEATURES_PLAN.md` - Advanced features (Phases 12-15)
4. `ROADMAP.md` - Timeline and milestones
5. `docs/API.md` - API documentation (once it exists)

### 7.2 External Resources

**TypeScript:**
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)

**Commander.js (CLI framework):**
- [Official Docs](https://github.com/tj/commander.js)
- [Examples](https://github.com/tj/commander.js/tree/master/examples)

**Inquirer.js (prompts):**
- [Official Docs](https://github.com/SBoudrias/Inquirer.js)

**API Integrations:**
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/claude/reference)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

**Testing:**
- [Jest Documentation](https://jestjs.io/docs/getting-started)

### 7.3 Ask for Help

**Before asking:**
1. Search existing issues on GitHub
2. Check documentation
3. Try debugging yourself (use console.log or debugger)
4. Search Google/Stack Overflow

**When asking:**
1. Describe what you're trying to do
2. What you've tried
3. The error message (full stack trace)
4. Relevant code snippet
5. Environment (OS, Node version, etc.)

**Where to ask:**
- GitHub Issues (for bugs)
- Discord/Slack (for quick questions)
- Pull Request comments (for code review)
- Email (for sensitive topics)

---

## 🎯 Step 8: Pick Your First Real Task (10 minutes)

### 8.1 Junior-Friendly Tasks (Start Here)

These are good first tasks for junior developers:

**Phase 1 (Foundation):**
- ✅ Task 1.1: Initialize Node.js Project (DONE - you're in it!)
- [ ] Task 1.4: Install Core Dependencies
- [ ] Task 1.5: Set Up Build Scripts

**Phase 2 (Configuration):**
- [ ] Task 2.1: Define TypeScript Types
- [ ] Task 2.3: Create Environment Variable Handler

**Phase 6 (Utilities):**
- ✅ Task 6.1: Create Logger Utility (DONE - you just did this!)
- [ ] Task 6.5: Create File Operations Utility

**Phase 7 (Documentation):**
- [ ] Task 7.2: Create Configuration Examples
- [ ] Task 7.5: Write Contributing Guide

### 8.2 How to Claim a Task

1. **Check the project board** - See what's available
2. **Assign yourself** - Comment on the issue or update the board
3. **Create a branch** - `git checkout -b feature/task-name`
4. **Read the task details** - In IMPLEMENTATION_PLAN.md
5. **Start coding!**

### 8.3 Task Checklist Template

Copy this for each task you work on:

```markdown
## Task X.Y: [Task Name]

**Status:** In Progress
**Assignee:** Your Name
**Branch:** feature/task-name
**Started:** YYYY-MM-DD

### Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Progress Notes:
- 2024-01-15: Started implementation
- 2024-01-16: Completed core functionality
- 2024-01-17: Added tests, ready for review

### Questions/Blockers:
- None

### Related:
- Issue #42
- PR #43
```

---

## 🎉 Step 9: You're Ready!

Congratulations! You've:
- ✅ Set up the development environment
- ✅ Understood the project structure
- ✅ Completed your first task (logger utility)
- ✅ Learned the workflow and tools
- ✅ Made your first commit

### Next Steps:

1. **Join the team communication** (Discord/Slack)
2. **Attend the next standup/sync**
3. **Pick your next task** from the project board
4. **Start contributing!**

### Remember:

- 🙋 Ask questions early and often
- 🧪 Write tests for your code
- 📝 Document as you go
- 🔄 Commit frequently
- 👥 Review others' code
- 🎉 Celebrate progress!

---

## 📞 Getting Help

### Common Issues

**Problem: `npm install` fails**
- Solution: Delete `node_modules` and `package-lock.json`, then run `npm install` again
- Or try: `npm cache clean --force` then `npm install`

**Problem: TypeScript errors**
- Solution: Run `npm run build` to see all errors
- Check `tsconfig.json` settings
- Ensure all dependencies are installed

**Problem: Tests failing**
- Solution: Run `npm test -- --verbose` for more details
- Check if test database/fixtures are set up
- Clear Jest cache: `npm test -- --clearCache`

**Problem: "Module not found"**
- Solution: Check import paths are correct
- Ensure file exists
- Rebuild: `npm run build`

### Contact Info

- **Project Lead:** [Name] - [Email/Discord]
- **Tech Lead:** [Name] - [Email/Discord]
- **Discord:** [Invite Link]
- **GitHub Issues:** [Repo URL]/issues
- **Documentation:** [Link to docs site]

---

## 🚀 Advanced Quick Start (For Experienced Devs)

If you're already familiar with TypeScript, CLI tools, and testing:

```bash
# Clone and setup
git clone <repo-url> && cd vibe-coder
npm install

# Read the key docs
cat IMPLEMENTATION_PLAN.md | grep "Phase 1"
cat ROADMAP.md | grep "v0.1.0"

# Pick a task from Phase 2-3 (more challenging)
# See IMPLEMENTATION_PLAN.md for details

# Set up your environment
cp examples/.env.example .env
# Edit .env with your API keys

# Start building
npm run dev  # Watch mode

# In another terminal
npm test -- --watch

# When done
git add .
git commit -m "feat: implement [feature]"
git push origin feature/[feature-name]
# Create PR
```

---

## 📝 Appendix: Code Style Guide

### TypeScript Best Practices

```typescript
// ✅ Good: Explicit types
function calculateTokens(text: string): number {
  return text.split(' ').length;
}

// ❌ Bad: Implicit any
function calculateTokens(text) {
  return text.split(' ').length;
}

// ✅ Good: Interface for objects
interface Config {
  apiKey: string;
  endpoint: string;
  model?: string;
}

// ❌ Bad: Inline object types
function loadConfig(): { apiKey: string; endpoint: string } {
  // ...
}

// ✅ Good: Error handling
async function fetchData(): Promise<Data> {
  try {
    const response = await api.get('/data');
    return response.data;
  } catch (error) {
    throw new ApiError('Failed to fetch data', error);
  }
}

// ❌ Bad: No error handling
async function fetchData() {
  const response = await api.get('/data');
  return response.data;
}
```

### Naming Conventions

```typescript
// Classes: PascalCase
class ConfigManager {}
class OpenAIClient {}

// Functions: camelCase
function loadConfig() {}
function parseArguments() {}

// Constants: UPPER_SNAKE_CASE
const DEFAULT_TIMEOUT = 5000;
const API_VERSION = '1.0.0';

// Interfaces: PascalCase with I prefix (optional)
interface IProvider {}
// Or without prefix
interface Provider {}

// Types: PascalCase
type ApiResponse = {...};

// Enums: PascalCase
enum LogLevel {
  Debug,
  Info,
  Warning,
  Error
}
```

### File Organization

```typescript
// 1. Imports (external, then internal)
import axios from 'axios';
import chalk from 'chalk';

import { Config } from '../types/config';
import { logger } from '../utils/logger';

// 2. Constants
const DEFAULT_MODEL = 'gpt-4';

// 3. Types/Interfaces
interface ClientOptions {
  apiKey: string;
  model?: string;
}

// 4. Main code
export class ApiClient {
  // ...
}

// 5. Helper functions (private)
function formatRequest(data: any): any {
  // ...
}

// 6. Exports (if needed)
export { formatRequest };
```

---

Good luck and happy coding! 🚀
