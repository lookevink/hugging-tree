# Analyze Feature

**Purpose**: Generate actionable insights for any task or question about your codebase.

## Core Capabilities

### Semantic Search Integration
- [x] Find code semantically similar to task description
- [x] Configurable number of semantic matches (default: 10)
- [x] Use vector embeddings for semantic matching

### Graph Analysis
- [x] Analyze dependencies (files that import modified files)
- [x] Analyze callers (functions that call modified functions)
- [x] Analyze callees (functions called by modified code)
- [x] Analyze file relationships
- [x] Build comprehensive context packet

### LLM Analysis
- [x] Use Gemini models for analysis
- [x] Generate structured insights:
  - [x] Files to Modify (ordered by priority)
  - [x] Blast Radius (affected files)
  - [x] Step-by-Step Actions
  - [x] Dependencies to Consider
  - [x] Risks & Breaking Changes
  - [x] Full Analysis
- [x] Model configuration support
  - [x] Default: `gemini-3-pro-preview`
  - [x] Support for `gemini-2.5-pro`
  - [x] Support for `gemini-2.5-flash`
  - [x] Support for `gemini-2.5-flash-lite`
  - [x] Environment variable configuration (`GEMINI_MODEL`)
  - [x] Per-command model override (`--model` flag)
- [x] Prompt customization
  - [x] Custom prompt templates via file (`--prompt-template` flag)
  - [x] Environment variable for prompt template path (`ANALYZE_PROMPT_TEMPLATE`)
  - [x] Template variable substitution (task, xml_context, expanded_context, etc.)
  - [x] Default built-in prompts if none provided
  - [x] Prompt validation and error handling

### Structured Extraction
- [x] Parse markdown-style analysis output
- [x] Extract files to modify
- [x] Extract blast radius files
- [x] Extract step-by-step actions
- [x] Extract dependencies
- [x] Extract risks and breaking changes
- [x] Display structured output with formatting

### Use Cases
- [x] Feature requests
- [x] Bug fixes
- [x] Code understanding
- [x] Refactoring planning

## Input/Output

**Input**: 
- Task description/question (any string)
- Repository path
- Number of semantic matches (optional, default: 10)
- Model selection (optional)
- Custom prompt template file (optional)

**Output**: 
- Structured analysis with actionable insights
- Files to modify (ordered by priority)
- Blast radius (affected files)
- Step-by-step actions
- Dependencies
- Risks & breaking changes
- Full LLM-generated analysis

## Implementation Status

- [x] Context analyzer module (`src/analyzer.py`)
- [x] Semantic search integration
- [x] Graph analysis integration
- [x] LLM prompt building (hardcoded prompts)
- [x] LLM analysis generation
- [x] Structured extraction from markdown
- [x] CLI command (`main.py analyze`)
- [x] Model configuration support
- [x] Formatted output display
- [x] Prompt customization

## Prompt Customization

Users can customize the LLM prompts used for analysis:

### Custom Prompt Templates

- **File-based**: Provide a custom prompt template file via `--prompt-template` flag
- **Environment variable**: Set `ANALYZE_PROMPT_TEMPLATE` to point to a template file
- **Template variables**: Use placeholders like `{task}`, `{xml_context}`, `{expanded_context}`

### Template Format

Prompt templates support Python-style string formatting:
- `{task}` - The user's task description
- `{xml_context}` - The XML context packet with code and relationships
- `{expanded_context}` - The expanded context dictionary (JSON)
- `{semantic_matches_count}` - Number of semantic matches found
- `{related_files_count}` - Number of related files in graph

### Usage Examples

#### Basic Usage (Default Prompt)

```bash
docker compose exec app python main.py analyze \
  --task "add user authentication with JWT tokens" \
  --path /projects/hugging-tree/.example/express
```

#### Using Custom Prompt Template via CLI Flag

```bash
# Create a custom prompt template file
cat > /app/.example-prompts/security-focused.txt << 'EOF'
You are a senior security engineer analyzing code changes for security implications.

USER REQUEST:
{task}

CODEBASE CONTEXT:
{xml_context}

STATISTICS:
- Found {semantic_matches_count} semantically relevant code definitions
- Identified {related_files_count} related files through graph traversal

Analyze this request with a focus on security best practices, authentication, 
authorization, and data protection. Provide analysis in the following format:

## Files to Modify
[List files that need changes, ordered by security priority]

## Security Considerations
[Identify security risks, authentication/authorization needs, data protection requirements]

## Blast Radius
[Files affected by security changes]

## Step-by-Step Actions
[Security-focused implementation steps]

## Security Testing Requirements
[What security tests need to be added or updated]
EOF

# Use the custom template
docker compose exec app python main.py analyze \
  --task "add user authentication" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/security-focused.txt
```

#### Using Environment Variable

```bash
# Set the environment variable
export ANALYZE_PROMPT_TEMPLATE=/app/.example-prompts/analyze-example.txt

# Run analyze (will automatically use the template)
docker compose exec app python main.py analyze \
  --task "refactor user service to use dependency injection" \
  --path /projects/my-app

# CLI flag takes precedence over environment variable
docker compose exec app python main.py analyze \
  --task "add feature" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/different-template.txt
```

#### Example Template File

Create `.example-prompts/analyze-example.txt`:

```
You are a senior software engineer specializing in TypeScript and modern web development. 
Your expertise includes clean architecture, test-driven development, and security best practices.

USER REQUEST:
{task}

CODEBASE CONTEXT:
{xml_context}

STATISTICS:
- Found {semantic_matches_count} semantically relevant code definitions
- Identified {related_files_count} related files through graph traversal

Based on the semantic search results and graph relationships above, analyze the user's request 
and provide a comprehensive analysis in the following format:

## Files to Modify
[List the specific files that need to be changed, ordered by priority. Include the reason for each change.]

## Blast Radius
[Identify all files that will be affected by these changes...]

## Step-by-Step Actions
[Provide a numbered list of specific, actionable steps...]

## Dependencies to Consider
[List any external dependencies, imports, npm packages...]

## Risks & Breaking Changes
[Identify potential breaking changes, test files that need updates...]

## Testing Strategy
[Recommend what tests should be added or modified...]

Be specific and actionable. Reference actual file paths and function names from the context provided.
```

## Future Enhancements

- [ ] More sophisticated structured extraction (use function calling)
- [ ] Support for multiple analysis models in parallel
- [ ] Analysis templates for common tasks
- [ ] Export analysis to markdown files
- [ ] Integration with issue trackers
- [ ] Analysis history and comparison
- [ ] Multi-repository analysis
- [ ] Prompt template library (pre-built templates for common scenarios)

