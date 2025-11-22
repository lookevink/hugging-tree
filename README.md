# Hugging Tree

A local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Prerequisites

- **Docker & Docker Compose**: For orchestrating Neo4j and the application container.
- **Git**: For scanning the repository.

## Setup

1. **Environment Variables**
   
   Copy `.env.example` to a `.env` file in the root directory with the following variables:
   
   ```bash
   cp .env.example .env
   ```
   
   Copy `.env.example` to a `.env` file in the root directory with the following variables:
   
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
    docker compose exec app python main.py scan --path /projects/my-app
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
docker compose exec app python main.py scan --path /projects/hugging-tree/.example/vanilla
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
    
5.  Run the following Cypher query to see specific file:

    ```cypher
6.  **Unlock Graph Intelligence**:

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