# Hugging Tree

A local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Context Tree" for LLMs.

## Quick Start

1. **Setup**: Copy `.env.example` to `.env` and configure your `PROJECTS_ROOT` and `GOOGLE_API_KEY`
2. **Start**: Run `docker-compose up -d --build`
3. **List Projects**: `docker compose exec app python main.py projects` (optional - see available projects)
4. **Scan**: `docker compose exec app python main.py scan --path /projects/your-repo`
5. **Query**: `docker compose exec app python main.py query --text "your query" --path /projects/your-repo`
6. **Analyze**: `docker compose exec app python main.py analyze --task "your task" --path /projects/your-repo`
7. **Plan**: `docker compose exec app python main.py plan --task "your task" --path /projects/your-repo`

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

## API Usage

The tool exposes a REST API via FastAPI, enabling programmatic access and integration with visualization tools and UI management systems.

### Starting the API Server

**Local Development**:
```bash
uvicorn main:api --reload --port 8000
```

**Docker**:
The API server starts automatically when you run `docker-compose up`.
The API will be available at `http://localhost:8088`.

### Interactive Documentation

Once the server is running, access the interactive Swagger UI at:
- **Swagger UI**: [http://localhost:8088/docs](http://localhost:8088/docs)
- **ReDoc**: [http://localhost:8088/redoc](http://localhost:8088/redoc)

### API Endpoints

#### `GET /projects`
List all available projects in PROJECTS_ROOT.

**Request**: No request body required.

**Response**:
```json
{
  "projects_root": "/projects",
  "projects": [
    {
      "name": "my-repo",
      "path": "/projects/my-repo",
      "is_git_repo": true,
      "is_scanned": true,
      "file_count": 42
    }
  ],
  "total": 1,
  "scanned_count": 1
}
```

#### `POST /scan`
Scan a repository and sync to Neo4j graph database and ChromaDB vector database.

**Request Body**:
```json
{
  "path": "/path/to/repository"
}
```

**Response**:
```json
{
  "status": "success",
  "files_scanned": 42,
  "total_files_in_graph": 42
}
```

#### `POST /query`
Semantic search with optional graph context expansion.

**Request Body**:
```json
{
  "text": "find authentication logic",
  "path": "/path/to/repository",
  "n": 5,
  "with_graph": true,
  "xml": false
}
```

**Response**:
```json
{
  "vector_results": [...],
  "expanded_context": {...},
  "xml_packet": null
}
```

#### `POST /analyze`
Analyze a task and generate actionable insights.

**Request Body**:
```json
{
  "task": "add user authentication",
  "path": "/path/to/repository",
  "n": 10,
  "model": "gemini-3-pro-preview",
  "prompt_template": "/path/to/template.txt"
}
```

**Response**:
```json
{
  "model_name": "gemini-3-pro-preview",
  "analysis_result": {
    "structured": {...},
    "analysis": "...",
    "semantic_matches": 10,
    "related_files": [...]
  }
}
```

#### `POST /plan`
Generate an executable, step-by-step plan in XML format.

**Request Body**:
```json
{
  "task": "implement user authentication",
  "path": "/path/to/repository",
  "n": 10,
  "model": "gemini-3-pro-preview",
  "prompt_template": "/path/to/template.txt"
}
```

**Response**:
```json
{
  "model_name": "gemini-3-pro-preview",
  "plan_xml": "<plan>...</plan>"
}
```

### Example Usage

**Using curl**:
```bash
# Query the codebase
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "find authentication logic",
       "path": "/projects/your-repo",
       "n": 5,
       "with_graph": true
     }'

# Analyze a task
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "task": "add user authentication",
       "path": "/projects/your-repo",
       "n": 10
     }'
```

For detailed API documentation, see [API Documentation](.agent/sys/api/README.md).

## Web UI

Hugging Tree includes a modern Next.js web interface for visual interaction with the tool.

### Starting the Web UI

**Docker** (Recommended):
```bash
# Start all services including frontend
docker compose up -d --build

# Access the web UI at http://localhost:3000
```

**Local Development**:
```bash
# First, generate OpenAPI spec and setup frontend
./scripts/setup-frontend.sh

# Start the frontend development server
cd frontend
npm run dev

# Access at http://localhost:3000
```

### Features

The web UI provides visual interfaces for:
- **Projects**: Browse and select projects from your PROJECTS_ROOT
- **Scan**: Scan repositories and sync to Neo4j and ChromaDB
- **Query**: Semantic search with graph context expansion
- **Analyze**: Task analysis with actionable insights
- **Plan**: Generate executable plans in XML format

### OpenAPI SDK Generation

The frontend uses an auto-generated TypeScript SDK from the FastAPI OpenAPI specification:

```bash
# Generate OpenAPI spec from FastAPI
npm run generate:openapi

# Generate TypeScript SDK from OpenAPI spec
npm run generate:sdk

# Or do both at once
npm run generate:all
```

The generated SDK will be available at `frontend/src/lib/api/` and can be imported in your components.

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
