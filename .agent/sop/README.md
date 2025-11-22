# Standard Operating Procedures

## Setup

### Initial Setup

1. **Environment Variables**
   
   Copy `.env.example` to a `.env` file in the root directory:
   
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set `PROJECTS_ROOT` to the parent directory containing your projects:
   
   ```bash
   PROJECTS_ROOT=/Users/me/projects
   ```

2. **Set up Google API Key**
   
   Add your Google API key to your `.env` file:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **Start the Infrastructure**
   
   Build and start the services using Docker Compose:
   
   ```bash
   docker-compose up -d --build
   ```
   
   This will start:
   - **Neo4j Database**: Accessible at http://localhost:7474
   - **App Container**: The Python environment for the CLI and scanner

## Usage

### Running Commands

You can run commands inside the app container:

```bash
docker-compose exec app python main.py [COMMAND]
```

### Scanning a Repository

Scan a repository to build the knowledge graph:

```bash
docker compose exec app python main.py scan --path /projects/hugging-tree/.example/express
```

This will:
- Parse all code definitions from your repository
- Generate embeddings using Google's Gemini API
- Store embeddings in ChromaDB at `.tree_roots/` directory
- Create graph nodes and relationships in Neo4j

### Querying the Codebase

#### Basic semantic search

```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5
```

#### XML context packet (for LLMs)

```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5 --xml
```

#### Vector search only (no graph context)

```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5 --no-with-graph
```

### Task Analysis

Analyze a task or question about your codebase:

```bash
docker compose exec app python main.py analyze --task "your task or question" --path /projects/hugging-tree/.example/express
```

**Example Use Cases**:

- **Feature Request:**
  ```bash
  docker compose exec app python main.py analyze --task "add user authentication with JWT tokens" --path /projects/hugging-tree/.example/express
  ```

- **Bug Fix:**
  ```bash
  docker compose exec app python main.py analyze --task "fix the order creation bug when inventory is zero" --path /projects/hugging-tree/.example/express
  ```

- **Code Understanding:**
  ```bash
  docker compose exec app python main.py analyze --task "how does the payment processing work?" --path /projects/hugging-tree/.example/express
  ```

- **Refactoring:**
  ```bash
  docker compose exec app python main.py analyze --task "refactor the user service to use dependency injection" --path /projects/hugging-tree/.example/express
  ```

**Options**:
- `--task`: (Required) Any query, task description, or question about the codebase
- `--path`: (Required) Path to the repository
- `--n`: (Optional, default: 10) Number of semantic matches to consider
- `--model`: (Optional) Gemini model to use for analysis

## Development Workflow

### Code Modification

The `app` service mounts your local directory to `/app` in the container. This means you can edit files locally and run them immediately in the container without rebuilding.

1. **Modify Code**: Edit `main.py` or any other file in your IDE.
2. **Run Code**: Execute the script inside the container:
   ```bash
   docker compose exec app python main.py [COMMAND]
   ```
3. **Rebuild Dependencies**: If you add a new package to `requirements.txt`, you must rebuild the container:
   ```bash
   docker compose up -d --build
   ```

### Interactive Shell

If you prefer to run multiple commands without typing `docker compose exec app ...` every time, you can open a shell inside the container:

```bash
docker compose exec app bash
# Now you are inside the container at /app
python main.py scan
```

### File Paths

**Important**: The project root is mounted to `/app` inside the container.
- **Always use relative paths** from the project root (e.g., `src/main.py` or `./src/main.py`).
- **Do NOT use absolute paths** from your host machine (e.g., `/Users/kevinloo/...`), as the container cannot see them.

## Visualizing the Graph

### Neo4j Browser

1. Open [http://localhost:7474](http://localhost:7474) in your browser.
2. Login with the credentials defined in your `.env` file (default: `neo4j` / `password`).
3. Run Cypher queries to explore the graph.

### Common Queries

**See all files:**
```cypher
MATCH (n:File) RETURN n LIMIT 25
```

**See all classes and functions:**
```cypher
MATCH (f:File)-[r:DEFINES]->(d) RETURN f, r, d LIMIT 50
```

**Dependency Graph (Who imports whom?):**
```cypher
MATCH (source:File)-[r:IMPORTS]->(target:File)
RETURN source, r, target LIMIT 50
```

**Impact Analysis (If I change `userService.ts`, what breaks?):**
```cypher
MATCH (source:File)-[:IMPORTS*1..5]->(target:File {path: 'src/services/userService.ts'})
RETURN source, target
```

**Code Structure (Show me all functions in `productService.ts`):**
```cypher
MATCH (f:File {path: 'src/services/productService.ts'})-[:DEFINES]->(func:Function)
RETURN f, func
```

**Function Usage (Who calls `createOrder`?):**
```cypher
MATCH (caller:Function)-[r:CALLS]->(callee:Function {name: 'createOrder'})
RETURN caller, r, callee
```

**Call Graph (Visualize function interactions):**
```cypher
MATCH (f1:Function)-[r:CALLS]->(f2:Function)
RETURN f1, r, f2 LIMIT 50
```

## Database Management

### Drop the Graph

To clear all data from Neo4j, go to the Neo4j Browser and run:

```cypher
MATCH (n) DETACH DELETE n;
```

### Storage Locations

- **Neo4j Database**: Managed by Docker, accessible at http://localhost:7474
- **ChromaDB**: Stored in `.tree_roots/` directory within your scanned project

## Testing

### Testing on Sample Project

Test the system on a sample TypeScript project:

```bash
docker compose exec app python main.py scan --path /projects/hugging-tree/.example/express
```

This will scan the vanilla TypeScript project and sync it to the Neo4j database.

## Documentation Practices

### Code Documentation

- Document all public functions and classes
- Include docstrings for complex logic
- Add inline comments for non-obvious code paths

### Command Documentation

- Document all CLI commands and their options
- Provide usage examples for common scenarios
- Include error handling documentation

### Architecture Documentation

- Document major architectural decisions
- Keep system documentation in `.agent/sys/README.md`
- Update PRD when adding new features

## Best Practices

### Repository Scanning

- Always scan from the repository root
- Use consistent path formats (relative to PROJECTS_ROOT)
- Re-scan after major code changes

### Query Optimization

- Start with smaller `--n` values for faster results
- Use `--no-with-graph` for quick semantic searches
- Use `--xml` format when feeding results to LLMs

### Model Selection

- Use `gemini-3-pro-preview` for complex analysis (default)
- Use `gemini-2.5-flash` for faster, cost-effective queries
- Set `GEMINI_MODEL` environment variable for default model

### Error Handling

- Check Neo4j connection before running commands
- Verify Google API key is set before scanning
- Monitor disk space for ChromaDB storage

