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

2. **Start the Infrastructure**

   Build and start the services using Docker Compose:

   ```bash
   docker-compose up -d --build
   ```

   This will start:
   - **Neo4j Database**: Accessible at http://localhost:7474 (Default login: `neo4j` / `your_secure_password`)
   - **App Container**: The Python environment for the CLI and scanner.

## Usage

### Running Commands

You can run commands inside the app container:

```bash
docker-compose exec app python main.py [COMMAND]
```

*(Note: CLI commands are currently under development)*

## Development

The `app` service mounts the current directory to `/app`, so changes to the code are reflected immediately inside the container.
