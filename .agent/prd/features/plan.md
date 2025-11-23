# Plan Feature

**Purpose**: Generate executable, step-by-step plans in XML format optimized for AI coding tools like Cursor and Claude.

## Core Concept

While `analyze` provides exploratory insights and understanding, `plan` generates concrete, actionable execution plans. The output is structured XML that can be directly consumed by AI coding assistants to execute tasks.

## Core Capabilities

### Task Breakdown
- [ ] Break down feature requests into concrete, executable steps
- [ ] Order steps by dependencies and priority
- [ ] Identify prerequisites for each step
- [ ] Estimate complexity/difficulty for each step
- [ ] Group related steps into phases/milestones

### XML Output Format
- [ ] Generate structured XML plan optimized for AI tools
- [ ] Include task metadata (title, description, estimated effort)
- [ ] Include file-level changes (which files to create/modify)
- [ ] Include step-by-step instructions with code references
- [ ] Include context snippets for each step
- [ ] Include validation criteria for each step
- [ ] Include rollback instructions if needed

### Semantic Search Integration
- [ ] Find code semantically similar to task description
- [ ] Use vector embeddings for semantic matching
- [ ] Configurable number of semantic matches (default: 10)

### Graph Analysis
- [ ] Analyze dependencies (files that import modified files)
- [ ] Analyze callers (functions that call modified functions)
- [ ] Analyze callees (functions called by modified code)
- [ ] Identify impact radius for each step
- [ ] Build comprehensive context packet

### LLM Planning
- [ ] Use Gemini models for plan generation
- [ ] Generate executable steps (not just analysis)
- [ ] Include specific code locations and references
- [ ] Include code snippets/examples for each step
- [ ] Model configuration support
  - [ ] Default: `gemini-3-pro-preview`
  - [ ] Support for `gemini-2.5-pro`
  - [ ] Support for `gemini-2.5-flash`
  - [ ] Support for `gemini-2.5-flash-lite`
  - [ ] Environment variable configuration (`GEMINI_MODEL`)
  - [ ] Per-command model override (`--model` flag)
- [ ] Prompt customization
  - [ ] Custom prompt templates via file (`--prompt-template` flag)
  - [ ] Environment variable for prompt template path (`PLAN_PROMPT_TEMPLATE`)
  - [ ] Template variable substitution (task, xml_context, etc.)
  - [ ] Default built-in prompts if none provided
  - [ ] Prompt validation and error handling

## XML Schema

The plan XML should follow a structure like:

```xml
<execution_plan>
  <task>
    <title>Add user authentication with JWT tokens</title>
    <description>...</description>
    <estimated_effort>medium</estimated_effort>
    <prerequisites>
      <prerequisite>...</prerequisite>
    </prerequisites>
  </task>
  
  <context>
    <relevant_files>
      <file path="..." reason="..."/>
    </relevant_files>
    <code_snippets>
      <snippet file="..." lines="..." code="..."/>
    </code_snippets>
  </context>
  
  <phases>
    <phase id="1" name="Setup">
      <step id="1.1" order="1">
        <title>Create JWT utility module</title>
        <description>...</description>
        <files>
          <create path="src/utils/jwt.ts"/>
          <modify path="src/utils/index.ts" action="export jwt utilities"/>
        </files>
        <code_references>
          <reference file="..." function="..." lines="..."/>
        </code_references>
        <instructions>
          <instruction>...</instruction>
        </instructions>
        <validation>
          <check>JWT token can be generated</check>
          <check>JWT token can be verified</check>
        </validation>
        <dependencies>
          <depends_on step="1.2"/>
        </dependencies>
      </step>
    </phase>
  </phases>
  
  <impact_analysis>
    <affected_files>
      <file path="..." impact="direct|indirect" reason="..."/>
    </affected_files>
  </impact_analysis>
  
  <rollback>
    <step>...</step>
  </rollback>
</execution_plan>
```

## Input/Output

**Input**: 
- Task/feature description (any string)
- Repository path
- Number of semantic matches (optional, default: 10)
- Model selection (optional)
- Custom prompt template file (optional)
- Output format (XML only, optimized for tools)

**Output**: 
- XML execution plan with:
  - Task metadata
  - Context (relevant files, code snippets)
  - Phased steps with:
    - Title and description
    - Files to create/modify
    - Code references
    - Step-by-step instructions
    - Validation criteria
    - Dependencies between steps
  - Impact analysis
  - Rollback instructions

## Use Cases

- [ ] Feature implementation planning
- [ ] Bug fix execution plans
- [ ] Refactoring execution plans
- [ ] Migration plans
- [ ] Integration plans

## Differences from Analyze

| Aspect | Analyze | Plan |
|--------|---------|------|
| **Purpose** | Understanding & insights | Execution & action |
| **Output** | Human-readable markdown | Tool-ready XML |
| **Focus** | "What needs to change?" | "How to make the changes?" |
| **Format** | Exploratory analysis | Executable steps |
| **Audience** | Human developers | AI coding tools |
| **Steps** | High-level actions | Concrete, code-referenced steps |

## Implementation Status

- [ ] Plan generator module (`src/planner.py`)
- [ ] Semantic search integration
- [ ] Graph analysis integration
- [ ] LLM prompt building for plan generation
- [ ] XML plan generation
- [ ] Step dependency resolution
- [ ] CLI command (`main.py plan`)
- [ ] Model configuration support
- [ ] XML schema validation
- [ ] Prompt customization (planned)

## Prompt Customization

Users can customize the LLM prompts used for plan generation:

### Custom Prompt Templates

- **File-based**: Provide a custom prompt template file via `--prompt-template` flag
- **Environment variable**: Set `PLAN_PROMPT_TEMPLATE` to point to a template file
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
docker compose exec app python main.py plan \
  --task "add user authentication with JWT tokens" \
  --path /projects/hugging-tree/.example/express
```

#### Using Custom Prompt Template via CLI Flag

```bash
# Create a custom prompt template file for plan generation
cat > /app/.example-prompts/plan-detailed.txt << 'EOF'
You are a senior software engineer creating a detailed execution plan for AI coding tools.

TASK:
{task}

CODEBASE CONTEXT:
{xml_context}

STATISTICS:
- Found {semantic_matches_count} semantically relevant code definitions
- Identified {related_files_count} related files through graph traversal

Generate a comprehensive execution plan in XML format. The plan should be:
1. Highly detailed with specific code references
2. Ordered by dependencies (prerequisites first)
3. Include validation criteria for each step
4. Include rollback instructions
5. Optimized for AI coding assistants like Cursor and Claude

Follow the execution_plan XML schema exactly. Each step must include:
- Exact file paths to create or modify
- Specific function/class names to reference
- Code snippets or examples where helpful
- Clear validation criteria
- Dependencies on other steps

Be extremely specific and actionable. AI tools will execute this plan step-by-step.
EOF

# Use the custom template
docker compose exec app python main.py plan \
  --task "add user authentication" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/plan-detailed.txt
```

#### Using Environment Variable

```bash
# Set the environment variable
export PLAN_PROMPT_TEMPLATE=/app/.example-prompts/plan-detailed.txt

# Run plan (will automatically use the template)
docker compose exec app python main.py plan \
  --task "refactor user service to use dependency injection" \
  --path /projects/my-app

# CLI flag takes precedence over environment variable
docker compose exec app python main.py plan \
  --task "add feature" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/different-plan-template.txt
```

#### Example Template File

Create `.example-prompts/plan-example.txt`:

```
You are a senior software engineer creating an execution plan optimized for AI coding tools 
like Cursor and Claude.

TASK:
{task}

CODEBASE CONTEXT:
{xml_context}

STATISTICS:
- Found {semantic_matches_count} semantically relevant code definitions
- Identified {related_files_count} related files through graph traversal

Generate an execution plan in XML format following the execution_plan schema. The plan must:

1. Break down the task into concrete, executable steps
2. Order steps by dependencies (what must be done first)
3. Group related steps into logical phases
4. Include specific file paths, function names, and code references
5. Provide validation criteria for each step
6. Include impact analysis of affected files
7. Include rollback instructions

Each step should be detailed enough for an AI coding assistant to execute without 
additional context. Reference actual code locations from the context provided.

Output ONLY valid XML following the execution_plan schema.
```

## Future Enhancements

- [ ] Plan templates for common tasks
- [ ] Plan execution tracking
- [ ] Plan versioning and diff
- [ ] Integration with issue trackers (create issues from plan)
- [ ] Plan estimation (time/complexity)
- [ ] Plan validation (check if plan is still valid)
- [ ] Interactive plan refinement
- [ ] Multi-repository planning
- [ ] Prompt template library (pre-built templates for common scenarios)

