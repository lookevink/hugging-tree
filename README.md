# Hugging Tree

A local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Prerequisites

- **Docker & Docker Compose**: For orchestrating Neo4j and the application container.
- **Git**: For scanning the repository.

## Setup

1. **Environment Variables**
   
   Copy `.env.example` to a `.env` file in the root directory:
   
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set `PROJECTS_ROOT` to the parent directory containing your projects (e.g., your main `projects` folder):
   
   ```bash
   PROJECTS_ROOT=/Users/me/projects
   ```

2. **Start the Infrastructure**

   Build and start the services using Docker Compose:

   ```bash
   docker-compose up -d --build
   ```

   This will start:
   - **Neo4j Database**: Accessible at http://localhost:7474 (Default login: `neo4j` / `your_secure_password`)
   - **App Container**: The Python environment for the CLI and scanner.

   NOTE: if you haven't already, you'll need to install docker for your machine. check out https://www.docker.com/

## Usage

### Running Commands

You can run commands inside the app container:

```bash
docker-compose exec app python main.py [COMMAND]
```

## Development Workflow

The `app` service mounts your local directory to `/app` in the container. This means you can edit files locally and run them immediately in the container without rebuilding.

1.  **Modify Code**: Edit `main.py` or any other file in your IDE.
2.  **Run Code**: Execute the script inside the container:

    ```bash
    docker compose exec app python main.py [COMMAND]
    ```

    For example, if you mounted your `projects` folder, you can scan any repo inside it:

    ```bash
    docker compose exec app python main.py scan --path /projects/hugging-tree/.example/express
    ```

3.  **Rebuild Dependencies**: If you add a new package to `requirements.txt`, you must rebuild the container:

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

The project root is mounted to `/app` inside the container.
- **Always use relative paths** from the project root (e.g., `src/main.py` or `./src/main.py`).
- **Do NOT use absolute paths** from your host machine (e.g., `/Users/kevinloo/...`), as the container cannot see them.


## Testing on a sample typscript project:

```bash
docker compose exec app python main.py scan --path /projects/hugging-tree/.example/express
```

This will scan the vanilla typescript project and sync it to the Neo4j database.

## Visualizing the Graph

You can explore the graph using the Neo4j Browser:

1.  Open [http://localhost:7474](http://localhost:7474) in your browser.
2.  Login with the credentials defined in your `.env` file (default: `neo4j` / `password`). (bolt://0.0.0.0:7687)
3.  Run the following Cypher query to see all files:

    ```cypher
    MATCH (n:File) RETURN n LIMIT 25
    ```

4.  Run the following Cypher query to see all classes and functions:

    ```cypher
    MATCH (f:File)-[r:DEFINES]->(d) RETURN f, r, d LIMIT 50
    ```
    
5.  **Unlock Graph Intelligence**:

    To see the *visual graph*, you must return the nodes and relationships themselves, not just their properties.

    **Dependency Graph (Who imports whom?)**:
    ```cypher
    MATCH (source:File)-[r:IMPORTS]->(target:File)
    RETURN source, r, target LIMIT 50
    ```

    **Impact Analysis (If I change `userService.ts`, what breaks?)**:
    ```cypher
    MATCH (source:File)-[:IMPORTS*1..5]->(target:File {path: 'src/services/userService.ts'})
    RETURN source, target
    ```
    *(This finds all files that depend on `userService.ts` up to 5 hops away)*

    **Code Structure (Show me all functions in `productService.ts`)**:
    ```cypher
    MATCH (f:File {path: 'src/services/productService.ts'})-[:DEFINES]->(func:Function)
    RETURN f, func
    ```

    **Function Usage (Who calls `createOrder`?)**:
    ```cypher
    MATCH (caller:Function)-[r:CALLS]->(callee:Function {name: 'createOrder'})
    RETURN caller, r, callee
    ```

    **Call Graph (Visualize function interactions)**:
    ```cypher
    MATCH (f1:Function)-[r:CALLS]->(f2:Function)
    RETURN f1, r, f2 LIMIT 50
    ```

## Managing db

    **Drop the graph**:
    Go to the Neo4j Browser and run:
    ```cypher
    MATCH (n) DETACH DELETE n;
    ```

## Generating embeddings

Embeddings are **automatically generated** when you run the `scan` command. The system extracts all code definitions (functions, classes, methods, etc.) and generates vector embeddings for semantic search.

### Prerequisites

1. **Set up Google API Key**: Add your Google API key to your `.env` file:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```
   
   The embeddings use Google's Gemini `gemini-embedding-001` model.

2. **Run the scan command**: Embeddings are generated automatically during scanning:
   ```bash
   docker compose exec app python main.py scan --path /projects/hugging-tree/.example/express
   ```

### How it works

- During scanning, the system parses all code definitions from your repository
- Each definition (function, class, method) is embedded using Google's Gemini API
- Embeddings are stored in ChromaDB at `.tree_roots/` directory in your project root
- The embeddings include the definition name, type, and code snippet for context

### Querying embeddings

Use the `query` command to search your codebase semantically. The command combines **vector search** (semantic similarity) with **graph traversal** (structural relationships) to provide rich context.

#### Basic semantic search

```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5
```

This returns the top 5 most semantically similar code definitions to your query, enhanced with graph context showing:
- **Callers**: Functions that call this function
- **Callees**: Functions called by this function  
- **Dependents**: Files that import this definition's file
- **Dependencies**: Files this file imports

#### Output options

**Human-readable format (default):**
```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5
```

**XML context packet (for LLMs):**
```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5 --xml
```

The XML output generates a "Perfect Context Packet" that you can paste directly into Gemini, Claude, or other LLMs for code understanding tasks.

**Vector search only (no graph context):**
```bash
docker compose exec app python main.py query --text "authentication middleware" --path /projects/hugging-tree/.example/express --n 5 --no-with-graph
```

#### How it works

1. **Semantic Search**: Uses ChromaDB to find code definitions semantically similar to your query
2. **Graph Traversal**: For each match, queries Neo4j to find:
   - Structural relationships (imports, function calls)
   - Impact analysis (what breaks if this changes)
   - Related code in the same file
3. **Context Packet**: Combines both sources into a comprehensive context for understanding code relationships

### Storage location

Embeddings are persisted in the `.tree_roots/` directory within your scanned project. This directory contains the ChromaDB database files.

## Vector + Graph Integration

Hugging Tree combines two powerful data structures to provide comprehensive code understanding:

### Vector Database (ChromaDB)
- **Purpose**: Semantic similarity search
- **Stores**: Code embeddings (vector representations of functions, classes, methods)
- **Use Case**: "Find code that does something similar to X"
- **Location**: `.tree_roots/` directory in your project

### Graph Database (Neo4j)
- **Purpose**: Structural relationship traversal
- **Stores**: Files, definitions, imports, function calls
- **Use Case**: "What breaks if I change this file?" or "Who calls this function?"
- **Location**: Neo4j database (accessible at http://localhost:7474)

### The Perfect Context Packet

When you run a query, the system:

1. **Finds semantically similar code** using vector search (ChromaDB)
2. **Traverses graph relationships** to find structural connections (Neo4j)
3. **Combines both** into a comprehensive context packet that includes:
   - The matching code (from vector search)
   - What calls it (from graph)
   - What it calls (from graph)
   - What files depend on it (from graph)
   - What files it depends on (from graph)

This dual approach solves the "Blast Radius" problem: semantic search finds the starting point, graph traversal finds the hidden dependencies that don't share keywords.

## Task Analysis & Action Planning

The `analyze` command combines semantic search, graph traversal, and LLM analysis to generate actionable insights for any task or question about your codebase.

### Usage

```bash
docker compose exec app python main.py analyze --task "your task or question" --path /projects/hugging-tree/.example/express
```

The `--task` parameter accepts **any string** - a feature request, bug report, question, or task description. The system will:
1. Find semantically relevant code
2. Analyze graph relationships and dependencies
3. Generate actionable insights using LLM analysis

### Example Use Cases

**Feature Request:**
```bash
docker compose exec app python main.py analyze --task "add user authentication with JWT tokens" --path /projects/hugging-tree/.example/express
```

**Bug Fix:**
```bash
docker compose exec app python main.py analyze --task "fix the order creation bug when inventory is zero" --path /projects/hugging-tree/.example/express
```

**Code Understanding:**
```bash
docker compose exec app python main.py analyze --task "how does the payment processing work?" --path /projects/hugging-tree/.example/express
```

**Refactoring:**
```bash
docker compose exec app python main.py analyze --task "refactor the user service to use dependency injection" --path /projects/hugging-tree/.example/express
```

### Output

The `analyze` command provides structured insights:

- **📝 Files to Modify**: Specific files that need changes, ordered by priority
- **💥 Blast Radius**: All files that will be affected (direct and indirect dependencies)
- **✅ Step-by-Step Actions**: Numbered list of specific actions needed
- **🔗 Dependencies**: External dependencies, imports, or relationships to consider
- **⚠️ Risks & Breaking Changes**: Potential breaking changes, test files that need updates, and areas of risk
- **📄 Full Analysis**: Complete LLM-generated analysis with detailed context

### How It Works

1. **Semantic Search**: Finds code semantically similar to your task using vector embeddings
2. **Graph Traversal**: Analyzes dependencies, callers, callees, and file relationships
3. **Context Building**: Creates a comprehensive context packet with all relevant code and relationships
4. **LLM Analysis**: Uses Gemini to analyze the context and generate actionable insights
5. **Structured Extraction**: Parses the analysis into actionable sections

### Options

- `--task`: (Required) Any query, task description, or question about the codebase
- `--path`: (Required) Path to the repository
- `--n`: (Optional, default: 10) Number of semantic matches to consider
- `--model`: (Optional) Gemini model to use for analysis. Examples:
  - `gemini-3-pro-preview` (default) - Most intelligent, best for complex analysis
  - `gemini-2.5-pro` - State-of-the-art thinking model, great for reasoning
  - `gemini-2.5-flash` - Best price-performance, fast and capable
  - `gemini-2.5-flash-lite` - Fastest, most cost-efficient
  
  You can also set the `GEMINI_MODEL` environment variable as a default.
  
  **Note**: Gemini 1.5 models are deprecated. Use 2.5 or 3.0 models instead.

### Model Configuration

**Important**: The embedding model (`gemini-embedding-001`) is fixed and cannot be changed after scanning. This ensures consistency in your vector database.

However, the **analysis model** (used for generating insights) is flexible and can be changed per command:

```bash
# Use default model (gemini-3-pro-preview)
docker compose exec app python main.py analyze --task "add auth" --path /projects/my-app

# Use a specific model
docker compose exec app python main.py analyze --task "add auth" --path /projects/my-app --model gemini-2.5-flash

# Set default via environment variable
export GEMINI_MODEL=gemini-2.5-pro
docker compose exec app python main.py analyze --task "add auth" --path /projects/my-app
```

Different models have different strengths:
- **gemini-3-pro-preview**: Most intelligent, best for complex multimodal understanding (default)
- **gemini-2.5-pro**: State-of-the-art thinking model, excellent for reasoning over complex problems
- **gemini-2.5-flash**: Best price-performance, fast and capable, great for most tasks
- **gemini-2.5-flash-lite**: Fastest and most cost-efficient, good for high-volume tasks

### Example Output

```
📋 ANALYSIS RESULTS

📝 FILES TO MODIFY:
  1. src/middleware/auth.ts
  2. src/api/routes.ts
  3. src/services/userService.ts

💥 BLAST RADIUS (Affected Files):
  1. src/api/handlers/userHandlers.ts
  2. src/api/handlers/orderHandlers.ts
  3. src/utils/validation.ts

✅ STEP-BY-STEP ACTIONS:
  1. Create JWT token generation utility
  2. Add authentication middleware
  3. Update route handlers to use middleware
  ...

⚠️ RISKS & BREAKING CHANGES:
  1. Existing sessions will be invalidated
  2. API endpoints require authentication headers
  ...
```

This command is perfect for understanding the impact of changes before you start coding, ensuring you don't miss hidden dependencies or breaking changes.
