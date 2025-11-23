# CLI Interface Documentation

## Overview

Hugging Tree provides a command-line interface built with Typer, offering an intuitive and powerful way to interact with the codebase analysis system. The CLI shares the same business logic as the REST API, ensuring consistent behavior across interfaces.

## Architecture

The CLI is built using **Typer**, a modern CLI framework built on top of Click. It follows a clean architecture pattern:

1. **Business Logic Functions**: Core functionality in reusable functions (`logic_scan`, `logic_query`, `logic_analyze`, `logic_plan`)
2. **CLI Commands**: Typer commands that wrap business logic with user-friendly output formatting
3. **Shared Logic**: Same business logic used by both CLI and API ensures consistency

## Installation & Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for Neo4j)
- Google API Key (for embeddings and analysis)

### Running via Docker (Recommended)

```bash
# Start services
docker compose up -d --build

# Run CLI commands
docker compose exec app python main.py <command> [options]
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Neo4j is running (via Docker)
docker compose up -d neo4j

# Run CLI commands
python main.py <command> [options]
```

## Available Commands

### `scan`

Scans a repository and syncs code structure to Neo4j graph database and ChromaDB vector database.

**Usage**:
```bash
python main.py scan --path /path/to/repository
```

**Options**:
- `--path` (required): Path to the repository to scan

**Example**:
```bash
docker compose exec app python main.py scan --path /projects/my-repo
```

**Output**:
```
Scanning repository at: /projects/my-repo
Found 42 files in git index.
Parsing, syncing graph, and generating embeddings...
Parsing and syncing definitions & dependencies...
  Processed src/auth.ts: 5 defs, 3 imports, 12 calls
  Processed src/routes.ts: 8 defs, 5 imports, 15 calls
  ...
Sync complete. Total files in graph: 42
```

**What it does**:
1. Scans repository using git hashes (incremental sync)
2. Parses code structure (definitions, imports, calls)
3. Syncs to Neo4j graph database
4. Generates embeddings and stores in ChromaDB

### `query`

Searches the codebase using semantic search, optionally enhanced with graph traversal.

**Usage**:
```bash
python main.py query \
    --text "your search query" \
    --path /path/to/repository \
    [--n 5] \
    [--with-graph / --no-with-graph] \
    [--xml]
```

**Options**:
- `--text` (required): Natural language query to search for
- `--path` (required): Path to the repository (for loading embeddings)
- `--n` (optional, default: 5): Number of results to return
- `--with-graph` / `--no-with-graph` (optional, default: true): Include graph context (dependencies, callers, callees)
- `--xml` (optional, default: false): Output as XML context packet for LLMs

**Example**:
```bash
docker compose exec app python main.py query \
    --text "find authentication logic" \
    --path /projects/my-repo \
    --n 5 \
    --with-graph
```

**Output** (with graph context):
```
🔍 Semantic Search Results for: 'find authentication logic'

================================================================================

[1] authenticateUser (function)
    📄 File: src/auth.ts:42
    🎯 Semantic Score: 0.9542
    📝 Code snippet:
    function authenticateUser(username: string, password: string): Promise<User> {
      // Authentication logic...
    }...

    🔗 Graph Context:
       ⬇️  Called by: loginHandler, validateSession
       ⬆️  Calls: hashPassword, validateCredentials
       📦 Used by files: 3 file(s)
          - src/routes.ts
          - src/middleware.ts
          - src/api.ts
       📥 Depends on: 2 file(s)
          - src/utils.ts
          - src/db.ts

[2] loginHandler (function)
    ...
```

**Output** (XML mode):
```xml
<context>
  <file path="src/auth.ts">
    <function name="authenticateUser" line="42">
      <code>...</code>
      <callers>...</callers>
      <callees>...</callees>
    </function>
  </file>
</context>
```

### `analyze`

Analyzes a query/task and generates actionable context including files to modify, blast radius, and step-by-step actions.

**Usage**:
```bash
python main.py analyze \
    --task "your task description" \
    --path /path/to/repository \
    [--n 10] \
    [--model MODEL_NAME] \
    [--prompt-template /path/to/template.txt]
```

**Options**:
- `--task` (required): Any query, task description, or question about the codebase
- `--path` (required): Path to the repository
- `--n` (optional, default: 10): Number of semantic matches to consider
- `--model` (optional): Gemini model to use (e.g., `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`). Defaults to `GEMINI_MODEL` env var or `gemini-3-pro-preview`
- `--prompt-template` (optional): Path to custom prompt template file. Can also be set via `ANALYZE_PROMPT_TEMPLATE` environment variable.

**Example**:
```bash
docker compose exec app python main.py analyze \
    --task "add user authentication" \
    --path /projects/my-repo \
    --n 10 \
    --model gemini-3-pro-preview
```

**Output**:
```
🔍 Analyzing task: 'add user authentication'

🤖 Using model: gemini-3-pro-preview

================================================================================

================================================================================

📋 ANALYSIS RESULTS

================================================================================

📝 FILES TO MODIFY:
--------------------------------------------------------------------------------
  1. src/auth.ts
  2. src/routes.ts
  3. src/middleware.ts

💥 BLAST RADIUS (Affected Files):
--------------------------------------------------------------------------------
  1. src/auth.ts
  2. src/routes.ts
  3. src/middleware.ts
  4. src/api.ts
  5. src/utils.ts

✅ STEP-BY-STEP ACTIONS:
--------------------------------------------------------------------------------
  1. Create authentication service in src/auth.ts
  2. Add route handlers for login/logout
  3. Update middleware to validate tokens
  4. Add password hashing utilities

🔗 DEPENDENCIES TO CONSIDER:
--------------------------------------------------------------------------------
  1. bcrypt for password hashing
  2. jwt for token generation
  3. express-session for session management

⚠️  RISKS & BREAKING CHANGES:
--------------------------------------------------------------------------------
  1. Existing auth flow may break
  2. Database schema changes required

================================================================================

📄 FULL ANALYSIS:
================================================================================
[Full LLM-generated analysis text...]

================================================================================

📊 SUMMARY:
   • Semantic matches found: 10
   • Related files in graph: 15
   • Files to modify: 3
   • Blast radius files: 5
```

### `plan`

Generates an executable, step-by-step plan in XML format for AI coding tools.

**Usage**:
```bash
python main.py plan \
    --task "your task description" \
    --path /path/to/repository \
    [--n 10] \
    [--model MODEL_NAME] \
    [--prompt-template /path/to/template.txt]
```

**Options**:
- `--task` (required): The task description or feature request
- `--path` (required): Path to the repository
- `--n` (optional, default: 10): Number of semantic matches to consider
- `--model` (optional): Gemini model to use for planning
- `--prompt-template` (optional): Path to custom prompt template file. Can also be set via `PLAN_PROMPT_TEMPLATE` environment variable.

**Example**:
```bash
docker compose exec app python main.py plan \
    --task "implement user authentication" \
    --path /projects/my-repo \
    --n 10
```

**Output**:
```
📋 Generating plan for: 'implement user authentication'

🤖 Using model: gemini-3-pro-preview

================================================================================

<plan>
  <step number="1">
    <action>Create authentication service</action>
    <files>
      <file path="src/auth.ts" action="create"/>
    </files>
    <dependencies>
      <dependency>bcrypt</dependency>
      <dependency>jsonwebtoken</dependency>
    </dependencies>
  </step>
  <step number="2">
    <action>Add route handlers</action>
    <files>
      <file path="src/routes.ts" action="modify"/>
    </files>
  </step>
  ...
</plan>
```

### `projects`

Lists all available projects in PROJECTS_ROOT directory.

**Usage**:
```bash
python main.py projects
```

**Options**: None (reads PROJECTS_ROOT from environment)

**Example**:
```bash
docker compose exec app python main.py projects
```

**Output**:
```
📁 Projects in: /projects

================================================================================

[1] my-repo
    📦 Path: /projects/my-repo
    ✅ Status: Scanned
    🔷 Git Repository: Yes
    📊 Files in graph: 42

[2] another-project
    📦 Path: /projects/another-project
    ⏳ Status: Not scanned
    🔷 Git Repository: Yes

================================================================================

📊 Summary:
   • Total projects: 2
   • Scanned: 1
   • Not scanned: 1
```

**What it shows**:
- All directories in PROJECTS_ROOT
- Whether each is a git repository
- Whether each has been scanned (has `.tree_roots` directory or exists in Neo4j)
- File count for scanned projects

### `parse`

**Status**: TODO - Not yet implemented

This command will parse changed files (planned for future release).

## Environment Variables

The CLI respects the following environment variables:

- `GOOGLE_API_KEY`: Google API key for Gemini API (required)
- `GEMINI_MODEL`: Default Gemini model for analysis (optional, default: `gemini-3-pro-preview`)
- `ANALYZE_PROMPT_TEMPLATE`: Path to custom prompt template for analyze command
- `PLAN_PROMPT_TEMPLATE`: Path to custom prompt template for plan command
- `NEO4J_URI`: Neo4j connection URI (default: `bolt://neo4j:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (required)

## Custom Prompt Templates

Both `analyze` and `plan` commands support custom prompt templates:

**Via Command Line**:
```bash
python main.py analyze \
    --task "add feature" \
    --path /projects/my-repo \
    --prompt-template /path/to/custom-template.txt
```

**Via Environment Variable**:
```bash
export ANALYZE_PROMPT_TEMPLATE=/path/to/custom-template.txt
python main.py analyze --task "add feature" --path /projects/my-repo
```

**CLI flag takes precedence** over environment variable if both are provided.

## Help & Documentation

Get help for any command:

```bash
# General help
python main.py --help

# Command-specific help
python main.py scan --help
python main.py query --help
python main.py analyze --help
python main.py plan --help
```

## Common Workflows

### Initial Setup

```bash
# 1. Start services
docker compose up -d --build

# 2. List available projects
docker compose exec app python main.py projects

# 3. Scan repository
docker compose exec app python main.py scan --path /projects/my-repo

# 4. Query the codebase
docker compose exec app python main.py query \
    --text "authentication" \
    --path /projects/my-repo
```

### Analyzing a Feature Request

```bash
# 1. Analyze the task
docker compose exec app python main.py analyze \
    --task "add user authentication" \
    --path /projects/my-repo \
    --n 15

# 2. Generate a plan
docker compose exec app python main.py plan \
    --task "add user authentication" \
    --path /projects/my-repo \
    --n 15
```

### Using Custom Prompts

```bash
# Create custom prompt template
cat > /tmp/my-analyze-prompt.txt << EOF
You are a senior developer analyzing code changes.
Focus on security implications and performance.
EOF

# Use custom template
docker compose exec app python main.py analyze \
    --task "add feature" \
    --path /projects/my-repo \
    --prompt-template /tmp/my-analyze-prompt.txt
```

## Output Formats

### Standard Output

Most commands output formatted text to stdout, suitable for terminal viewing.

### XML Output

The `query` command supports `--xml` flag for XML-formatted output, ideal for:
- LLM context packets
- Programmatic processing
- Integration with other tools

### JSON Output (Future)

Future versions may support `--json` flag for structured JSON output.

## Error Handling

The CLI provides clear error messages:

```bash
# Missing required option
$ python main.py scan
Error: Missing option '--path'

# Invalid path
$ python main.py scan --path /nonexistent
Error: Repository not found at /nonexistent

# API errors
$ python main.py analyze --task "..." --path /projects/my-repo
Error: Failed to connect to Neo4j. Is it running?
```

All errors exit with code 1, making them suitable for scripting and CI/CD pipelines.

## Performance Tips

1. **Incremental Scanning**: The `scan` command uses git hashes for incremental sync - only changed files are processed
2. **Result Limits**: Use `--n` to limit results and improve performance
3. **Graph Context**: Disable `--no-with-graph` if you don't need relationship data (faster queries)
4. **Model Selection**: Use `gemini-2.5-flash` for faster analysis, `gemini-3-pro-preview` for best quality

## Integration with Scripts

The CLI is designed to be script-friendly:

```bash
#!/bin/bash
# Analyze and save results
docker compose exec app python main.py analyze \
    --task "$1" \
    --path /projects/my-repo > analysis.txt

# Extract files to modify
grep "FILES TO MODIFY" -A 10 analysis.txt
```

## Troubleshooting

### Common Issues

**Neo4j Connection Error**:
```bash
# Ensure Neo4j is running
docker compose ps neo4j

# Check connection settings
docker compose exec app env | grep NEO4J
```

**Embedding Generation Fails**:
```bash
# Verify API key
docker compose exec app env | grep GOOGLE_API_KEY

# Check API quota
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY"
```

**No Results from Query**:
```bash
# Ensure repository is scanned first
docker compose exec app python main.py scan --path /projects/my-repo

# Check embeddings exist
ls -la /projects/my-repo/.tree_roots/
```

## Best Practices

1. **Always scan first**: Run `scan` before `query`, `analyze`, or `plan`
2. **Use appropriate `--n` values**: Larger values = more context but slower
3. **Choose the right model**: Balance speed vs quality based on your needs
4. **Customize prompts**: Use custom templates for domain-specific analysis
5. **Version control**: Commit prompt templates alongside your code

