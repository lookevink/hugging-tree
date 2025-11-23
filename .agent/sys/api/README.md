# FastAPI REST API Documentation

## Overview

Hugging Tree exposes a REST API via FastAPI, enabling programmatic access to all functionality. This is particularly useful for:
- **Visualization Tools**: Build dashboards and visual representations of code relationships
- **UI Management**: Create web interfaces for prompt template management
- **Integration**: Integrate with other tools and workflows
- **Automation**: Script and automate codebase analysis tasks

## Architecture

The API is built using FastAPI and shares the same business logic as the CLI interface. This ensures consistency between CLI and API usage.

### Design Pattern

The codebase follows a **separation of concerns** pattern:

1. **Business Logic Functions**: Core functionality extracted into reusable functions (`logic_scan`, `logic_query`, `logic_analyze`, `logic_plan`)
2. **API Endpoints**: FastAPI routes that wrap business logic with HTTP handling
3. **CLI Commands**: Typer commands that call the same business logic functions

This architecture ensures:
- Single source of truth for business logic
- Consistent behavior between CLI and API
- Easier testing and maintenance
- No code duplication

## Getting Started

### Starting the Server

**Local Development**:
```bash
uvicorn main:api --reload --port 8000
```

**Docker**:
```bash
docker compose exec app uvicorn main:api --host 0.0.0.0 --port 8000
```

**Production**:
```bash
uvicorn main:api --host 0.0.0.0 --port 8000 --workers 4
```

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Explore all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Understand parameter requirements

## API Endpoints

### GET /projects

Lists all available projects in the PROJECTS_ROOT directory. This endpoint is useful for discovering which projects are available for scanning and analysis.

**Request**: No request body required. This is a GET endpoint.

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
    },
    {
      "name": "another-project",
      "path": "/projects/another-project",
      "is_git_repo": true,
      "is_scanned": false,
      "file_count": 0
    }
  ],
  "total": 2,
  "scanned_count": 1
}
```

**Response Fields**:
- `projects_root` (string): The value of the PROJECTS_ROOT environment variable
- `projects` (array): List of project objects
  - `name` (string): Directory name of the project
  - `path` (string): Full path to the project directory
  - `is_git_repo` (boolean): Whether the directory is a git repository
  - `is_scanned` (boolean): Whether the project has been scanned (has `.tree_roots` directory or exists in Neo4j)
  - `file_count` (integer): Number of files in the Neo4j graph for this project (0 if not scanned)
- `total` (integer): Total number of projects found
- `scanned_count` (integer): Number of projects that have been scanned

**Error Response** (if PROJECTS_ROOT is not set or invalid):
```json
{
  "projects_root": null,
  "projects": [],
  "error": "PROJECTS_ROOT environment variable is not set"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/projects"
```

**Use Cases**:
- Discover available projects for scanning
- Check scan status of projects
- Build project selection UI
- Monitor which projects have been analyzed

### POST /scan

Scans a repository and syncs code structure to Neo4j graph database and ChromaDB vector database.

**Request Body** (`ScanRequest`):
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

**Error Response** (500):
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/scan" \
     -H "Content-Type: application/json" \
     -d '{"path": "/projects/my-repo"}'
```

### POST /query

Performs semantic search on the codebase with optional graph context expansion.

**Request Body** (`QueryRequest`):
```json
{
  "text": "find authentication logic",
  "path": "/path/to/repository",
  "n": 5,
  "with_graph": true,
  "xml": false
}
```

**Parameters**:
- `text` (required): Natural language query to search for
- `path` (required): Path to the repository (for loading embeddings)
- `n` (optional, default: 5): Number of semantic matches to return
- `with_graph` (optional, default: true): Include graph context (dependencies, callers, callees)
- `xml` (optional, default: false): Return results as XML context packet for LLMs

**Response**:
```json
{
  "vector_results": [
    {
      "document": "function authenticateUser() { ... }",
      "metadata": {
        "name": "authenticateUser",
        "type": "function",
        "file_path": "src/auth.ts",
        "start_line": 42
      },
      "score": 0.95
    }
  ],
  "expanded_context": {
    "semantic_matches": [
      {
        "vector_result": {...},
        "graph_context": {
          "callers": [...],
          "callees": [...],
          "dependencies": [...],
          "dependents": [...]
        }
      }
    ],
    "total_files": 15
  },
  "xml_packet": null
}
```

**When `xml: true`**:
- `expanded_context` will be `null`
- `xml_packet` will contain the XML-formatted context packet

**Example**:
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "find authentication logic",
       "path": "/projects/my-repo",
       "n": 5,
       "with_graph": true
     }'
```

### POST /analyze

Analyzes a task and generates actionable insights including files to modify, blast radius, and step-by-step actions.

**Request Body** (`AnalyzeRequest`):
```json
{
  "task": "add user authentication",
  "path": "/path/to/repository",
  "n": 10,
  "model": "gemini-3-pro-preview",
  "prompt_template": "/path/to/template.txt"
}
```

**Parameters**:
- `task` (required): Task description or question about the codebase
- `path` (required): Path to the repository
- `n` (optional, default: 10): Number of semantic matches to consider
- `model` (optional): Gemini model to use (e.g., `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`). Defaults to `GEMINI_MODEL` env var or `gemini-3-pro-preview`
- `prompt_template` (optional): Path to custom prompt template file. Can also be set via `ANALYZE_PROMPT_TEMPLATE` environment variable.

**Response**:
```json
{
  "model_name": "gemini-3-pro-preview",
  "analysis_result": {
    "structured": {
      "files_to_modify": [
        "src/auth.ts",
        "src/routes.ts"
      ],
      "blast_radius": [
        "src/auth.ts",
        "src/routes.ts",
        "src/middleware.ts"
      ],
      "actions": [
        "Create authentication service",
        "Add route handlers",
        "Update middleware"
      ],
      "dependencies": [
        "bcrypt for password hashing",
        "jwt for tokens"
      ],
      "risks": [
        "Breaking change to existing auth flow"
      ]
    },
    "analysis": "Full LLM-generated analysis text...",
    "semantic_matches": 10,
    "related_files": ["src/auth.ts", "src/routes.ts", ...]
  }
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "task": "add user authentication",
       "path": "/projects/my-repo",
       "n": 10
     }'
```

### POST /plan

Generates an executable, step-by-step plan in XML format for AI coding tools.

**Request Body** (`PlanRequest`):
```json
{
  "task": "implement user authentication",
  "path": "/path/to/repository",
  "n": 10,
  "model": "gemini-3-pro-preview",
  "prompt_template": "/path/to/template.txt"
}
```

**Parameters**:
- `task` (required): Task description or feature request
- `path` (required): Path to the repository
- `n` (optional, default: 10): Number of semantic matches to consider
- `model` (optional): Gemini model to use for planning
- `prompt_template` (optional): Path to custom prompt template file. Can also be set via `PLAN_PROMPT_TEMPLATE` environment variable.

**Response**:
```json
{
  "model_name": "gemini-3-pro-preview",
  "plan_xml": "<plan>\n  <step>...</step>\n  <step>...</step>\n</plan>"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/plan" \
     -H "Content-Type: application/json" \
     -d '{
       "task": "implement user authentication",
       "path": "/projects/my-repo",
       "n": 10
     }'
```

## Request/Response Models

All endpoints use Pydantic models for request validation and response serialization:

### ScanRequest
```python
class ScanRequest(BaseModel):
    path: str
```

### QueryRequest
```python
class QueryRequest(BaseModel):
    text: str
    path: str
    n: int = 5
    with_graph: bool = True
    xml: bool = False
```

### AnalyzeRequest
```python
class AnalyzeRequest(BaseModel):
    task: str
    path: str
    n: int = 10
    model: Optional[str] = None
    prompt_template: Optional[str] = None
```

### PlanRequest
```python
class PlanRequest(BaseModel):
    task: str
    path: str
    n: int = 10
    model: Optional[str] = None
    prompt_template: Optional[str] = None
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **422 Unprocessable Entity**: Validation error (invalid request body)
- **500 Internal Server Error**: Server error during processing

Error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Integration Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

def scan_repository(path: str):
    response = requests.post(
        f"{BASE_URL}/scan",
        json={"path": path}
    )
    response.raise_for_status()
    return response.json()

def query_codebase(text: str, path: str, n: int = 5):
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "text": text,
            "path": path,
            "n": n,
            "with_graph": True
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
result = scan_repository("/projects/my-repo")
print(f"Scanned {result['files_scanned']} files")

results = query_codebase("authentication", "/projects/my-repo")
for match in results["vector_results"]:
    print(f"{match['metadata']['name']}: {match['score']}")
```

### JavaScript/TypeScript Client

```typescript
const BASE_URL = "http://localhost:8000";

async function scanRepository(path: string) {
  const response = await fetch(`${BASE_URL}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  return response.json();
}

async function queryCodebase(text: string, path: string, n: number = 5) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      path,
      n,
      with_graph: true,
    }),
  });
  return response.json();
}
```

## Use Cases

### Visualization Tools

The API is ideal for building visualization dashboards:

```python
# Get code relationships for graph visualization
query_result = query_codebase("", repo_path, n=100)
expanded_context = query_result["expanded_context"]

# Extract graph data
for match in expanded_context["semantic_matches"]:
    context = match["graph_context"]
    # Visualize callers, callees, dependencies
    visualize_relationships(context)
```

### Prompt Template Management UI

Build a web interface for managing prompt templates:

```python
# Analyze with custom template
analyze_result = requests.post(
    f"{BASE_URL}/analyze",
    json={
        "task": "add feature",
        "path": repo_path,
        "prompt_template": "/custom/template.txt"
    }
)
```

### CI/CD Integration

Automate codebase analysis in CI/CD pipelines:

```bash
# In CI pipeline
curl -X POST "${API_URL}/analyze" \
     -H "Content-Type: application/json" \
     -d "{
       \"task\": \"Review PR changes\",
       \"path\": \"${REPO_PATH}\"
     }" > analysis.json
```

## Performance Considerations

- **Async Support**: FastAPI supports async endpoints (can be added for better concurrency)
- **Caching**: Consider adding caching for frequently accessed queries
- **Rate Limiting**: Implement rate limiting for production deployments
- **Connection Pooling**: Neo4j and ChromaDB connections are managed per request

## Security Considerations

- **Authentication**: Add authentication middleware for production use
- **CORS**: Configure CORS appropriately for your frontend
- **Input Validation**: All inputs are validated via Pydantic models
- **Path Validation**: Ensure repository paths are validated to prevent directory traversal

## Future Enhancements

Potential API improvements:
- WebSocket support for real-time updates
- Batch operations for multiple repositories
- Streaming responses for long-running operations
- Authentication and authorization
- Rate limiting and quotas
- Response caching
- Webhook support for async operations

