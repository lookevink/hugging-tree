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

