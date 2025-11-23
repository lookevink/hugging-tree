# Hugging Tree

A local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Quick Start

1. **Setup**: Copy `.env.example` to `.env` and configure your `PROJECTS_ROOT` and `GOOGLE_API_KEY`
2. **Start**: Run `docker-compose up -d --build`
3. **Scan**: `docker compose exec app python main.py scan --path /projects/your-repo`
4. **Query**: `docker compose exec app python main.py query --text "your query" --path /projects/your-repo`
5. **Analyze**: `docker compose exec app python main.py analyze --task "your task" --path /projects/your-repo`
6. **Plan**: `docker compose exec app python main.py plan --task "your task" --path /projects/your-repo`

### Custom Prompt Templates

Customize LLM prompts for domain-specific analysis and planning:

```bash
# Analyze with custom prompt template
docker compose exec app python main.py analyze \
  --task "add authentication" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/analyze-example.txt

# Plan with custom prompt template
docker compose exec app python main.py plan \
  --task "add authentication" \
  --path /projects/my-app \
  --prompt-template /app/.example-prompts/plan-example.txt

# Or via environment variables
export ANALYZE_PROMPT_TEMPLATE=/app/.example-prompts/analyze-example.txt
export PLAN_PROMPT_TEMPLATE=/app/.example-prompts/plan-example.txt
docker compose exec app python main.py analyze --task "..." --path ...
```

See [Analyze Feature Documentation](.agent/prd/features/analyze.md#prompt-customization) and [Plan Feature Documentation](.agent/prd/features/plan.md#prompt-customization) for details.

## Documentation

This project uses a structured documentation system in the `.agent` directory:

- **[Product Requirements (PRD)](.agent/prd/README.md)**: Features, capabilities, and future roadmap
- **[Standard Operating Procedures (SOP)](.agent/sop/README.md)**: Setup, usage, development workflow, and best practices
- **[System Documentation (SYS)](.agent/sys/README.md)**: Architecture, technology stack, and technical details

## Key Features

- **Incremental Scanning**: Uses git hashes for O(1) performance on large repos
- **Semantic Search**: Vector embeddings for finding similar code
- **Graph Traversal**: Structural relationships (imports, function calls, dependencies)
- **Task Analysis**: LLM-powered insights for code changes and understanding
- **Execution Planning**: Generate executable, step-by-step plans in XML for AI coding tools
- **Customizable Prompts**: Customize LLM prompts via templates for domain-specific analysis and planning

## Prerequisites

- Docker & Docker Compose
- Git
- Google API Key (for embeddings and analysis)

For detailed information, see the [SOP documentation](.agent/sop/README.md).
