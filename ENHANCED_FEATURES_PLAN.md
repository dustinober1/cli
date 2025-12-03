# Enhanced Features Plan - Slash Commands & Provider Independence

This document extends the main IMPLEMENTATION_PLAN.md with advanced slash commands and provider independence features.

---

## Phase 12: Slash Commands System (40 Commands)

### Overview
Implement a comprehensive slash command system that allows users to interact with the AI coder through intuitive commands. Commands are parsed from user input and trigger specific behaviors.

---

### Task 12.1: Build Command Parser Infrastructure
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/commands/slashParser.ts`

**Steps:**
1. Create interface `SlashCommand`:
   ```typescript
   interface SlashCommand {
     name: string;
     aliases?: string[];
     description: string;
     usage: string;
     category: 'core' | 'file' | 'coding' | 'editor' | 'model' | 'git' | 'advanced';
     handler: (args: string[], context: CommandContext) => Promise<void>;
   }
   ```

2. Create `CommandContext` interface:
   ```typescript
   interface CommandContext {
     files: string[];        // Files in context
     conversationHistory: ApiMessage[];
     currentProvider: AIProvider;
     workingDirectory: string;
     config: AppConfig;
   }
   ```

3. Create `CommandRegistry` class:
   - Map to store all commands
   - Method `register(command: SlashCommand): void`
   - Method `parse(input: string): { command: string, args: string[] } | null`
   - Method `execute(input: string, context: CommandContext): Promise<void>`
   - Method `getCommand(name: string): SlashCommand | undefined`
   - Method `listCommands(category?: string): SlashCommand[]`

4. Create helper function `parseCommandLine(input: string)`:
   - Detect if input starts with `/`
   - Extract command name
   - Parse arguments (handle quotes, flags)
   - Return parsed structure

**Acceptance Criteria:**
- Parser correctly identifies slash commands
- Arguments are properly extracted
- Quoted strings are handled
- Command registry is extensible

---

### Task 12.2: Core & Session Management Commands (5 commands)
**Difficulty:** Junior-friendly to Medium
**Estimated Complexity:** Simple to Medium

**File:** `src/commands/slash/core.ts`

**Commands to implement:**

#### `/init`
- Initialize new session or configuration in current directory
- Create `.vibe/` directory structure
- Initialize config file if not exists
- Set up project-specific settings

#### `/clear`
- Clear current chat context/history
- Keep system messages if configured
- Show token savings
- Confirm before clearing if conversation is long

#### `/reset`
- Hard reset: clear context, dropped files, reload config
- Prompt for confirmation
- Reset all state to initial
- Reload configuration from disk

#### `/mode [mode]`
- Switch interaction modes: code, architect, ask, audit
- Update system prompt based on mode
- Modes:
  - `code`: Standard code generation
  - `architect`: High-level design and planning
  - `ask`: Q&A only, no code generation
  - `audit`: Code review and security analysis

#### `/exit`
- Save current state
- Optionally save conversation
- Clean up resources
- Graceful shutdown

**Acceptance Criteria:**
- All commands work independently
- State is properly managed
- Confirmations prevent accidental data loss
- Modes change AI behavior appropriately

---

### Task 12.3: File & Context Control Commands (8 commands)
**Difficulty:** Medium
**Estimated Complexity:** Medium to High

**File:** `src/commands/slash/files.ts`

**Commands to implement:**

#### `/add [file/glob]`
- Add files to LLM context window
- Support glob patterns (`src/**/*.ts`)
- Show files added and token count
- Warn if context limit approaching

#### `/drop [file/glob]`
- Remove files from context
- Support glob patterns
- Show tokens freed
- List remaining files

#### `/ls`
- List all files currently in context
- Show file paths and token usage per file
- Show total context usage
- Color code by file type

#### `/tree`
- Generate visual tree of project structure
- Respect `.gitignore` and `.videignore`
- Limit depth (configurable)
- Format for LLM understanding

#### `/read [url]`
- Scrape URL content (docs, references)
- Convert to markdown
- Add to context
- Handle authentication if needed
- Cache fetched content

#### `/ignore`
- Manage `.videignore` file
- Add/remove patterns
- Show current ignore list
- Similar to `.gitignore` syntax

#### `/map`
- Generate compressed repo map
- Extract class/function signatures
- Create high-level overview
- Update when files change

#### `/help [command]`
- Show help for specific command
- Or show general usage
- List all commands by category
- Include examples

**Acceptance Criteria:**
- File operations respect ignore patterns
- Context window limits are enforced
- Token counting is accurate
- URL fetching handles errors gracefully

---

### Task 12.4: AI Coding Action Commands (10 commands)
**Difficulty:** Medium to Advanced
**Estimated Complexity:** High

**File:** `src/commands/slash/coding.ts`

**Commands to implement:**

#### `/code [prompt]`
- Standard code generation
- Use files in context
- Apply best practices
- Return code blocks

#### `/ask [query]`
- Q&A mode without code generation
- Search codebase
- Explain functionality
- No file modifications

#### `/fix`
- Analyze last error
- Or fix highlighted code block
- Propose solution
- Optionally auto-apply

#### `/test`
- Generate unit tests
- For files in context
- Match existing test style
- Support multiple frameworks (Jest, Mocha, pytest, etc.)

#### `/doc`
- Generate documentation
- Create docstrings/JSDoc
- For selected file or function
- Match project doc style

#### `/refactor`
- Propose refactoring
- Focus on readability
- Reduce complexity
- Maintain functionality

#### `/plan`
- Generate implementation plan
- Break down into steps
- Don't write code yet
- Create task list

#### `/review`
- Code review
- Review git diff or staged changes
- Check for bugs, style, security
- Provide suggestions

#### `/optimize`
- Performance optimization suggestions
- Identify bottlenecks
- Suggest improvements
- Profile-guided if data available

#### `/explain [file/function]`
- Explain code functionality
- Break down complex logic
- Add inline comments
- Create flowcharts (ASCII)

**Acceptance Criteria:**
- Each command produces relevant output
- Code generation follows project conventions
- Tests actually work
- Reviews are constructive

---

### Task 12.5: Editor & Shell Integration Commands (7 commands)
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `src/commands/slash/editor.ts`

**Commands to implement:**

#### `/edit`
- Open in $EDITOR
- Edit current prompt or last response
- Apply changes on save
- Support vim, nano, emacs, vscode

#### `/run [cmd]`
- Execute shell command
- Capture output
- Add to context
- Stream output in real-time

#### `/shell`
- Drop into sub-shell
- Exit to return
- Maintain state
- Show prompt indicator

#### `/apply`
- Force-apply code block
- From chat history
- To file system
- Create backups
- Handle conflicts

#### `/diff`
- Show diff
- Between original and AI proposed
- Use git diff format
- Colorized output

#### `/undo`
- Revert last file modification
- Support multiple undo levels
- Show what was undone
- Restore from backup

#### `/save [filename]`
- Save conversation
- Or specific code block
- To file
- Multiple formats

**Acceptance Criteria:**
- Editor integration works across platforms
- Shell commands execute safely
- File operations are reversible
- Diffs are accurate

---

### Task 12.6: Model & Provider Commands (5 commands)
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/commands/slash/model.ts`

**Commands to implement:**

#### `/model [name]`
- Hot-swap model
- Within same provider
- Update config
- Show new model info

#### `/provider [name]`
- Switch backend provider
- E.g., ollama → openai
- Maintain conversation context
- Update API client

#### `/tokens`
- Show current token usage
- Remaining context window
- Per-file breakdown
- Cost estimate

#### `/cost`
- Estimate session cost
- For paid APIs
- Show per-message cost
- Total session cost

#### `/params`
- Tweak parameters on-the-fly
- Temperature, top_p, max_tokens
- Show current values
- Validate ranges

**Acceptance Criteria:**
- Model switching is seamless
- Token counting is accurate
- Cost calculations are correct
- Parameters update immediately

---

### Task 12.7: Git & Workflow Commands (4 commands)
**Difficulty:** Medium to Advanced
**Estimated Complexity:** Medium to High

**File:** `src/commands/slash/git.ts`

**Commands to implement:**

#### `/commit`
- Generate commit message
- Based on git diff
- Follow conventional commits
- Execute commit
- Optional GPG signing

#### `/push`
- Push changes to remote
- Safety check before force push
- Show what will be pushed
- Confirmation required

#### `/pr`
- Generate PR title and description
- Based on recent commits
- Include checklist
- Open in browser (optional)

#### `/branch [name]`
- Create new branch
- Switch to it
- Based on current state
- Naming convention support

**Acceptance Criteria:**
- Git operations are safe
- Commit messages are meaningful
- PR descriptions are comprehensive
- Branch management works

---

### Task 12.8: Advanced/Meta Commands (6 commands)
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `src/commands/slash/advanced.ts`

**Commands to implement:**

#### `/role [persona]`
- Change system prompt
- Personas: senior engineer, code reviewer, architect, etc.
- Custom persona support
- Load from `.vibe/personas/`

#### `/memory`
- Search long-term memory
- If vector storage implemented
- Retrieve relevant context
- Semantic search

#### `/voice`
- Toggle voice input mode
- Use Whisper integration
- Real-time transcription
- Push-to-talk or continuous

#### `/export`
- Export conversation
- To Markdown, HTML, PDF
- Include metadata
- Specify filename

#### `/search [query]`
- Search codebase
- Semantic or literal
- Show results with context
- Add to context window

#### `/benchmark`
- Run performance benchmarks
- On generated code
- Compare alternatives
- Show metrics

**Acceptance Criteria:**
- Personas change AI behavior
- Memory search is relevant
- Voice mode works reliably
- Exports are well-formatted

---

### Task 12.9: Create Command Help System
**Difficulty:** Junior-friendly
**Estimated Complexity:** Medium

**File:** `src/commands/slash/helpSystem.ts`

**Steps:**
1. Create function `generateHelp(command?: string)`:
   - If no command, list all by category
   - If command specified, show detailed help
   - Include usage examples
   - Show related commands

2. Create formatted output:
   ```
   CORE & SESSION MANAGEMENT
     /init              Initialize new session
     /clear             Clear chat context
     /reset             Hard reset
     /mode [mode]       Switch interaction mode
     /exit              Save and quit

   FILE & CONTEXT CONTROL
     /add [file/glob]   Add files to context
     /drop [file/glob]  Remove files from context
     ...
   ```

3. Add examples section:
   - Common workflows
   - Chained commands
   - Tips and tricks

4. Make help searchable

**Acceptance Criteria:**
- Help is comprehensive
- Examples are clear
- Categories make sense
- Searchable help works

---

## Phase 13: Provider Independence Features (10 Features)

### Overview
Implement features that make the tool truly provider-independent and robust across any AI API backend.

---

### Task 13.1: Universal "BYO" Endpoint Support
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/api/UniversalClient.ts`

**Steps:**
1. Extend `AIProvider` interface:
   ```typescript
   interface AIProvider {
     name: string;
     baseUrl: string;        // Any OpenAI-compatible endpoint
     apiKey: string;
     model?: string;
     headers?: Record<string, string>;  // Custom headers
     requestTransform?: string;  // Optional JS function to transform requests
     responseTransform?: string; // Optional JS function to parse responses
   }
   ```

2. Create `UniversalClient` class:
   - Accept any base URL
   - Auto-detect API format (OpenAI, Anthropic, custom)
   - Apply custom transforms if provided
   - Handle authentication variations

3. Support common local endpoints:
   - LM Studio: `http://localhost:1234/v1`
   - Ollama: `http://localhost:11434/api`
   - vLLM: `http://localhost:8000/v1`
   - LocalAI: `http://localhost:8080/v1`
   - Text Generation WebUI: `http://localhost:5000/api/v1`

4. Add endpoint validator:
   - Test connection
   - Detect API format
   - Suggest configuration

**Acceptance Criteria:**
- Works with any OpenAI-compatible endpoint
- Custom headers are applied
- Transforms allow format adaptation
- Local endpoints are auto-detected

---

### Task 13.2: Local-First Repo Map (AST-based)
**Difficulty:** Advanced
**Estimated Complexity:** Very High

**File:** `src/utils/repoMapper.ts`

**Steps:**
1. Install AST parsers:
   - `@babel/parser` for JavaScript/TypeScript
   - `tree-sitter` for multi-language support
   - Language-specific parsers

2. Create `RepoMapper` class:
   - Method `generateMap(directory: string): RepoMap`
   - Parse files locally
   - Extract structure (no implementation details):
     - Class names and inheritance
     - Function signatures
     - Import/export statements
     - Type definitions
   - Create compressed representation

3. Implement `RepoMap` structure:
   ```typescript
   interface RepoMap {
     files: {
       path: string;
       classes: ClassSignature[];
       functions: FunctionSignature[];
       imports: string[];
       exports: string[];
     }[];
     structure: string;  // Visual tree
     summary: string;    // LLM-friendly description
   }
   ```

4. Optimize for token efficiency:
   - Remove comments from skeleton
   - Compress whitespace
   - Use abbreviations for common patterns

5. Cache and update strategy:
   - Hash-based change detection
   - Incremental updates
   - Store in `.vibe/map.json`

**Acceptance Criteria:**
- Repo map is under 10% of full codebase tokens
- Contains all structural information
- Updates incrementally
- Works for multiple languages

---

### Task 13.3: Unified Diff Strategy (Apply Engine)
**Difficulty:** Advanced
**Estimated Complexity:** Very High

**File:** `src/utils/applyEngine.ts`

**Steps:**
1. Create `PatchParser` class:
   - Parse multiple diff formats:
     - UDIFF (unified diff)
     - Search/replace blocks
     - Full file replacement
     - Line-based edits
     - Anthropic's XML format
   - Auto-detect format from AI response

2. Implement `ApplyEngine`:
   ```typescript
   class ApplyEngine {
     parsePatch(content: string): Patch[];
     validatePatch(patch: Patch, file: string): ValidationResult;
     applyPatch(patch: Patch, file: string, options?: ApplyOptions): ApplyResult;
     createBackup(file: string): string;
     rollback(backupId: string): void;
   }
   ```

3. Handle edge cases:
   - Fuzzy matching for slight differences
   - Context-aware application
   - Conflict detection
   - Partial application

4. Add safeguards:
   - Dry-run mode
   - Always create backups
   - Show preview before applying
   - Confirmation for destructive changes

5. Support multiple formats:
   - OpenAI code blocks: ` ```language\ncode\n``` `
   - Anthropic search/replace
   - GitHub-style diffs
   - Custom formats via plugins

**Acceptance Criteria:**
- Handles 95%+ of AI code responses
- Fuzzy matching works for minor differences
- Backups are automatic
- Conflicts are detected

---

### Task 13.4: Cost & Token Budgeting (Fuel Gauge)
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/utils/budgetTracker.ts`

**Steps:**
1. Create `BudgetTracker` class:
   ```typescript
   class BudgetTracker {
     trackUsage(tokens: TokenUsage, model: string): void;
     estimateCost(tokens: number, model: string): number;
     getSessionStats(): SessionStats;
     checkBudget(): BudgetStatus;
     setLimit(limit: BudgetLimit): void;
   }
   ```

2. Implement pricing database:
   - Store per-model pricing
   - Input vs output token costs
   - Update periodically
   - Support custom pricing for local models (electricity cost estimate)

3. Create visual fuel gauge:
   ```
   Context: [████████░░] 80% (8K/10K tokens)
   Cost:    $0.0234 this session
   Budget:  [███░░░░░░░] 30% of daily limit
   ```

4. Add budget limits:
   - Per-session limit
   - Daily/weekly/monthly limits
   - Warnings at thresholds (50%, 75%, 90%)
   - Hard stops at 100%

5. Track metrics:
   - Tokens per message
   - Cost per message
   - Average response time
   - Model usage statistics

**Acceptance Criteria:**
- Fuel gauge is always visible
- Costs are accurate (±5%)
- Warnings prevent overspending
- Works for free local models

---

### Task 13.5: Offline Mode (Air-Gapped)
**Difficulty:** Medium
**Estimated Complexity:** Simple

**File:** `src/config/offlineMode.ts`

**Steps:**
1. Add offline mode flag to config:
   ```typescript
   interface AppConfig {
     offlineMode: boolean;
     allowedHosts: string[];  // Whitelist for offline mode
   }
   ```

2. Create network guard:
   ```typescript
   function checkNetworkAllowed(url: string): void {
     if (config.offlineMode && !isLocalhost(url)) {
       throw new OfflineViolationError(
         `Network call to ${url} blocked in offline mode`
       );
     }
   }
   ```

3. Integrate checks:
   - Before all HTTP requests
   - Before URL fetching
   - Before model API calls

4. Offline mode requirements:
   - Only allow localhost URLs
   - Or whitelisted hosts
   - Error clearly when blocked
   - Document offline setup (Ollama, LocalAI)

5. Add offline mode indicator:
   ```
   [OFFLINE MODE] Using local model: ollama/llama2
   ```

**Acceptance Criteria:**
- All network calls are blocked
- localhost is always allowed
- Clear error messages
- Easy to enable/disable

---

### Task 13.6: Custom System Prompt Profiles
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/prompts/profileManager.ts`

**Steps:**
1. Create profile directory structure:
   ```
   .vibe/
     profiles/
       senior-engineer.md
       code-reviewer.md
       react-frontend.md
       python-backend.md
       custom-profile.md
   ```

2. Create `ProfileManager` class:
   ```typescript
   class ProfileManager {
     listProfiles(): string[];
     loadProfile(name: string): string;
     saveProfile(name: string, content: string): void;
     deleteProfile(name: string): void;
     getActiveProfile(): string | null;
     setActiveProfile(name: string): void;
   }
   ```

3. Profile format (Markdown with frontmatter):
   ```markdown
   ---
   name: Senior React Engineer
   temperature: 0.7
   model: gpt-4
   ---

   You are a senior React engineer with 10+ years of experience.
   You follow these principles:
   - Use functional components and hooks
   - Prefer TypeScript for type safety
   - Write comprehensive tests
   ...
   ```

4. Add profile commands:
   - `/role list` - list available profiles
   - `/role [name]` - activate profile
   - `/role create [name]` - create new profile
   - `/role edit [name]` - edit profile

5. Include default profiles:
   - Senior Engineer
   - Code Reviewer
   - Architect
   - Debugger
   - Documentation Writer

**Acceptance Criteria:**
- Profiles change AI behavior
- Easy to create custom profiles
- Profiles persist
- Can include model preferences

---

### Task 13.7: Model Context Protocol (MCP) Client
**Difficulty:** Advanced
**Estimated Complexity:** Very High

**File:** `src/integrations/mcpClient.ts`

**Steps:**
1. Study MCP specification:
   - Review Anthropic's MCP documentation
   - Understand resource, tool, prompt schemas
   - Review reference implementations

2. Install MCP SDK:
   ```bash
   npm install @anthropic-ai/model-context-protocol
   ```

3. Create `MCPClient` class:
   ```typescript
   class MCPClient {
     connect(server: MCPServer): Promise<void>;
     listResources(): Promise<Resource[]>;
     readResource(uri: string): Promise<ResourceContent>;
     callTool(name: string, args: any): Promise<ToolResult>;
     disconnect(): void;
   }
   ```

4. Support MCP servers:
   - Filesystem server (read local files)
   - Database server (Postgres, SQLite)
   - API server (GitHub, Linear, Jira)
   - Custom servers

5. Integrate with commands:
   - `/mcp list` - list available resources
   - `/mcp connect [server]` - connect to MCP server
   - `/mcp get [uri]` - fetch resource
   - `/mcp tool [name] [args]` - call tool

6. Configuration:
   ```json
   {
     "mcpServers": {
       "postgres": {
         "command": "npx",
         "args": ["-y", "@anthropic-ai/mcp-server-postgres"],
         "env": {
           "DATABASE_URL": "postgresql://..."
         }
       }
     }
   }
   ```

**Acceptance Criteria:**
- Connects to MCP servers
- Resources are accessible
- Tools can be called
- Configuration is flexible

---

### Task 13.8: Auto-Healing (Agentic Loop)
**Difficulty:** Advanced
**Estimated Complexity:** Very High

**File:** `src/agents/autoHealer.ts`

**Steps:**
1. Create `AutoHealer` class:
   ```typescript
   class AutoHealer {
     maxRetries: number;
     enabled: boolean;

     async runWithHealing(
       command: string,
       validator: (output: string) => ValidationResult
     ): Promise<HealingResult>;
   }
   ```

2. Implement healing loop:
   ```typescript
   async runWithHealing(command, validator) {
     for (let i = 0; i < maxRetries; i++) {
       const output = await executeCommand(command);
       const result = validator(output);

       if (result.success) return { success: true, output };

       // Healing step
       const fix = await askAIToFix(result.error);
       await applyFix(fix);
     }

     return { success: false, error: "Max retries exceeded" };
   }
   ```

3. Add validators:
   - Test validator (checks if tests pass)
   - Build validator (checks if build succeeds)
   - Lint validator (checks if linting passes)
   - Type validator (TypeScript type checking)

4. Implement safety limits:
   - Max retry count (default: 3)
   - Timeout per attempt
   - Cost limit (stop if too expensive)
   - Require confirmation for file changes

5. Add configuration:
   ```json
   {
     "autoHealing": {
       "enabled": true,
       "maxRetries": 3,
       "requireConfirmation": true,
       "validators": ["test", "build", "lint"]
     }
   }
   ```

6. Usage examples:
   - `/run npm test --heal` - auto-fix failing tests
   - `/run npm build --heal` - auto-fix build errors
   - `/fix --auto` - auto-apply and verify fix

**Acceptance Criteria:**
- Loop runs up to max retries
- AI fixes are applied correctly
- Validation catches failures
- Safety limits prevent runaway

---

### Task 13.9: Privacy-Centric Local Vector Store
**Difficulty:** Advanced
**Estimated Complexity:** Very High

**File:** `src/rag/vectorStore.ts`

**Steps:**
1. Choose vector store:
   - ChromaDB (local Python server)
   - FAISS (pure in-memory)
   - LanceDB (local file-based)
   - Custom implementation

2. Install dependencies:
   ```bash
   npm install chromadb  # or alternative
   npm install @xenova/transformers  # For local embeddings
   ```

3. Create `VectorStore` class:
   ```typescript
   class VectorStore {
     initialize(path: string): Promise<void>;
     addDocuments(docs: Document[]): Promise<void>;
     search(query: string, limit: number): Promise<SearchResult[]>;
     delete(ids: string[]): Promise<void>;
     clear(): Promise<void>;
   }
   ```

4. Implement local embedding:
   - Use @xenova/transformers for browser/node embeddings
   - Model: all-MiniLM-L6-v2 (lightweight)
   - No data leaves machine
   - Cache embeddings

5. Document structure:
   ```typescript
   interface Document {
     id: string;
     content: string;
     metadata: {
       file: string;
       line?: number;
       type: 'code' | 'comment' | 'doc';
     };
     embedding?: number[];
   }
   ```

6. Integrate with commands:
   - `/index` - index current codebase
   - `/search [query]` - semantic search
   - `/similar [file]` - find similar code

7. Storage location:
   - `.vibe/vectors/` - local storage
   - Never uploaded to cloud
   - Add to `.gitignore`

**Acceptance Criteria:**
- Embeddings generated locally
- Search is fast (<1s for 10k docs)
- No data sent to external services
- Incremental indexing works

---

### Task 13.10: Standard Input/Output (UNIX Philosophy)
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `src/io/pipeHandler.ts`

**Steps:**
1. Detect piped input:
   ```typescript
   function hasPipedInput(): boolean {
     return !process.stdin.isTTY;
   }
   ```

2. Read from stdin:
   ```typescript
   async function readStdin(): Promise<string> {
     return new Promise((resolve) => {
       const chunks: Buffer[] = [];
       process.stdin.on('data', chunk => chunks.push(chunk));
       process.stdin.on('end', () => {
         resolve(Buffer.concat(chunks).toString());
       });
     });
   }
   ```

3. Support piped input:
   ```bash
   # Pipe file content
   cat error.log | vibe-coder /fix

   # Pipe command output
   npm test 2>&1 | vibe-coder /fix

   # Chain commands
   git diff | vibe-coder /review | less
   ```

4. Support piped output:
   ```bash
   # Save code to file
   vibe-coder /code "fibonacci function" > fib.js

   # Pipe to another command
   vibe-coder /doc file.js | prettier --parser markdown
   ```

5. Add flags for pipe behavior:
   - `--stdin` - force read from stdin
   - `--stdout` - force output to stdout only
   - `--quiet` - suppress interactive prompts
   - `--json` - output in JSON format

6. Handle interactive vs non-interactive:
   ```typescript
   if (process.stdin.isTTY) {
     // Interactive mode: show prompts, colors, spinners
   } else {
     // Pipe mode: plain output, no prompts
   }
   ```

**Acceptance Criteria:**
- Stdin detection works
- Piped input is processed
- Output can be piped
- Scriptable (no interactive prompts in pipe mode)

---

## Phase 14: Integration & Testing

### Task 14.1: Integration Testing for Slash Commands
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `tests/integration/slashCommands.test.ts`

**Steps:**
1. Test each command category:
   - Core commands
   - File commands
   - Coding commands
   - Editor commands
   - Model commands
   - Git commands
   - Advanced commands

2. Test command parsing:
   - Arguments extraction
   - Flag handling
   - Quoted strings
   - Edge cases

3. Test command chaining:
   - Multiple commands in sequence
   - State preservation between commands
   - Error handling

4. Mock external dependencies:
   - File system
   - Git operations
   - API calls
   - Shell execution

**Acceptance Criteria:**
- All commands have tests
- Edge cases are covered
- Mocks prevent external calls
- Tests run in <30s

---

### Task 14.2: Provider Independence Testing
**Difficulty:** Advanced
**Estimated Complexity:** High

**File:** `tests/integration/providerIndependence.test.ts`

**Steps:**
1. Test with multiple providers:
   - OpenAI (mocked)
   - Anthropic (mocked)
   - Local Ollama (if available)
   - Custom endpoint (test server)

2. Test universal client:
   - Auto-detection
   - Custom transforms
   - Error handling
   - Fallback behavior

3. Test offline mode:
   - Network blocking
   - Localhost allowlist
   - Error messages

4. Test budget tracking:
   - Token counting
   - Cost calculation
   - Limit enforcement

**Acceptance Criteria:**
- Works with 3+ providers
- Offline mode blocks network
- Budget limits work
- All tests pass

---

## Phase 15: Documentation for Enhanced Features

### Task 15.1: Slash Commands Reference
**Difficulty:** Junior-friendly
**Estimated Complexity:** Medium

**File:** `docs/SLASH_COMMANDS.md`

**Sections:**
1. Overview of slash commands
2. Command categories
3. Each command with:
   - Description
   - Usage
   - Examples
   - Options/flags
   - Related commands
4. Common workflows
5. Tips and tricks

**Acceptance Criteria:**
- All 40 commands documented
- Examples are tested
- Workflows are practical
- Searchable

---

### Task 15.2: Provider Independence Guide
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `docs/PROVIDER_INDEPENDENCE.md`

**Sections:**
1. Overview of provider independence
2. Setting up different providers:
   - OpenAI
   - Anthropic
   - Ollama (local)
   - LM Studio (local)
   - vLLM (local)
   - Custom endpoints
3. Offline mode setup
4. Budget and cost management
5. Advanced features:
   - MCP integration
   - Custom profiles
   - Auto-healing
6. Troubleshooting

**Acceptance Criteria:**
- Setup guides for all major providers
- Offline mode documented
- Advanced features explained
- Troubleshooting section complete

---

### Task 15.3: Advanced Usage Guide
**Difficulty:** Medium
**Estimated Complexity:** Medium

**File:** `docs/ADVANCED_USAGE.md`

**Sections:**
1. Repo mapping and AST
2. Agentic workflows with auto-healing
3. Vector search and RAG
4. Custom system prompts
5. Piping and scripting
6. MCP server integration
7. Plugin development
8. Performance optimization

**Acceptance Criteria:**
- Advanced topics covered
- Examples for each topic
- Best practices included
- Links to relevant docs

---

## Updated Summary

### New Task Count:
- **Phase 12:** Slash Commands (9 tasks)
- **Phase 13:** Provider Independence (10 tasks)
- **Phase 14:** Integration Testing (2 tasks)
- **Phase 15:** Documentation (3 tasks)

**New Total: 24 additional tasks**

**Grand Total:**
- **Core tasks:** 43 (original) + 24 (enhanced) = **67 tasks**
- **Optional tasks:** 8 (original) = **8 tasks**
- **All tasks:** **75 tasks**

### Updated Success Metrics:
- [ ] All 40 slash commands implemented and working
- [ ] Provider independence: works with 5+ providers
- [ ] Offline mode functions correctly
- [ ] Budget tracking accurate within 5%
- [ ] Auto-healing successfully fixes 70%+ of common errors
- [ ] Local vector search working
- [ ] MCP integration functional
- [ ] Piping works in UNIX-style
- [ ] Comprehensive documentation for all features
- [ ] Test coverage > 80% including new features

### Technologies Added:
- **Vector Store:** ChromaDB, FAISS, or LanceDB
- **Embeddings:** @xenova/transformers
- **AST Parsing:** @babel/parser, tree-sitter
- **MCP:** @anthropic-ai/model-context-protocol
- **Shell Integration:** Node.js child_process, pty

### Development Priority:
1. **High Priority** (MVP):
   - Core slash commands (/init, /clear, /help, /add, /code, /fix)
   - Universal endpoint support
   - Budget tracking
   - Offline mode

2. **Medium Priority** (v1.0):
   - All slash commands
   - Repo mapper (AST-based)
   - Apply engine (unified diff)
   - System prompt profiles

3. **Lower Priority** (v1.1+):
   - Auto-healing
   - Vector store / RAG
   - MCP integration
   - Advanced features

### Recommended Implementation Approach:
1. Start with Phase 12.1-12.2 (command infrastructure + core commands)
2. Implement Phase 13.1 (universal endpoint) immediately after
3. Build out remaining slash commands by category
4. Add provider independence features incrementally
5. Test thoroughly at each stage
6. Document as you go
