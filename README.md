# Hugging Tree

A local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Quick Start

1. **Setup**: Copy `.env.example` to `.env` and configure your `PROJECTS_ROOT` and `GOOGLE_API_KEY`
2. **Start**: Run `docker-compose up -d --build`
3. **Scan**: `docker compose exec app python main.py scan --path /projects/your-repo`
4. **Query**: `docker compose exec app python main.py query --text "your query" --path /projects/your-repo`

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

## Prerequisites

- Docker & Docker Compose
- Git
- Google API Key (for embeddings and analysis)

For detailed information, see the [SOP documentation](.agent/sop/README.md).
