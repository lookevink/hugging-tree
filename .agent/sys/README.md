# System Documentation

## Architecture Overview

Hugging Tree combines Vector Search with Graph Traversal to provide comprehensive code understanding. The system uses two complementary data structures:

1. **Vector Database (ChromaDB)**: Semantic similarity search
2. **Graph Database (Neo4j)**: Structural relationship traversal

## Technology Stack

### Core Technologies

- **Language**: Python 3.11+
- **CLI Framework**: Typer
- **Orchestration**: Docker Compose
- **Graph Database**: Neo4j 5.x Community Edition
- **Vector Database**: ChromaDB (Embedded mode)
- **Parser**: tree-sitter (with tree-sitter-languages wrapper)
- **Scanner**: Git (via subprocess `git ls-files`)
- **LLM**: Google Gemini API
- **Embedding Model**: `gemini-embedding-001` (fixed, cannot be changed after scanning)
- **Analysis Models**: 
  - `gemini-3-pro-preview` (default) - Most intelligent, best for complex analysis
  - `gemini-2.5-pro` - State-of-the-art thinking model, great for reasoning
  - `gemini-2.5-flash` - Best price-performance, fast and capable
  - `gemini-2.5-flash-lite` - Fastest, most cost-efficient

### Infrastructure

- **Docker**: Containerization for consistent environments
- **Docker Compose**: Orchestrates Neo4j and application containers
- **Neo4j**: Graph database accessible at http://localhost:7474
- **ChromaDB**: Embedded vector database stored locally

## System Components

### 1. Scanner (`src/scanner.py`)

**Purpose**: Identifies changed files using git hashes for incremental sync.

**Process**:
1. Run `git ls-files --stage` to get a map of `{filepath: git_hash}`
2. Compare against Neo4j: `MATCH (f:File) RETURN f.path, f.hash`
3. Identify: New, Modified (Hash Mismatch), and Deleted files
4. Only parse the diff (O(1) performance for large repos)

### 2. Parser (`src/parser.py`)

**Purpose**: Extracts code structure using tree-sitter.

**Extracts**:
- **Definitions**: Classes (`class_definition`), Functions (`function_definition`)
- **Signatures**: Function arguments and return types (critical for context)
- **Dependencies**: Import statements (`import_from_statement`, `import_statement`)

**Strategy**: Store the raw source code of functions in ChromaDB for retrieval.

### 3. Graph Builder (`src/graph.py`)

**Purpose**: Constructs the knowledge graph in Neo4j.

**Process**:
1. **Node Creation**:
   - Create `:File` nodes with properties `{path, hash, project_id}`
   - Create `:Function` and `:Class` nodes linked to their file:
     `(:File)-[:DEFINES]->(:Function)`
   - Use `file_path` as the primary key for Files
   - Use `file_path::function_name` as the ID for functions

2. **Edge Resolution**:
   - Convert string imports like `import { foo } from './utils'` into graph edges
   - Algorithm:
     1. Parse import path (`./utils`)
     2. Resolve to absolute path (e.g., `src/utils.ts` or `src/utils/index.ts`)
     3. Cypher Query: `MATCH (a:File {path: 'src/main.ts'}), (b:File {path: 'src/utils.ts'}) MERGE (a)-[:IMPORTS]->(b)`
   - Result: A fully traversable dependency graph

### 4. Resolver (`src/resolver.py`)

**Purpose**: Resolves import paths to absolute file paths.

**Handles**:
- Relative imports (`./utils`, `../services`)
- Absolute imports (`src/utils`)
- Index file resolution (`./utils` → `./utils/index.ts`)

### 5. Embeddings (`src/embeddings.py`)

**Purpose**: Generates vector embeddings for semantic search.

**Process**:
- During scanning, extracts all code definitions from repository
- Each definition (function, class, method) is embedded using Google's Gemini API
- Embeddings include the definition name, type, and code snippet for context
- Stored in ChromaDB at `.tree_roots/` directory in project root

**Model**: `gemini-embedding-001` (fixed, ensures consistency in vector database)

### 6. Analyzer (`src/analyzer.py`)

**Purpose**: Combines semantic search, graph traversal, and LLM analysis.

**Process**:
1. **Semantic Search**: Finds code semantically similar to task using vector embeddings
2. **Graph Traversal**: Analyzes dependencies, callers, callees, and file relationships
3. **Context Building**: Creates comprehensive context packet with all relevant code and relationships
4. **LLM Analysis**: Uses Gemini to analyze the context and generate actionable insights
5. **Structured Extraction**: Parses the analysis into actionable sections

## Data Flow

### Scanning Flow

```
Repository → Scanner (git hashes) → Parser (tree-sitter) → Graph Builder (Neo4j) + Embeddings (ChromaDB)
```

1. Scanner identifies changed files via git hashes
2. Parser extracts code structure (definitions, imports, signatures)
3. Graph Builder creates nodes and relationships in Neo4j
4. Embeddings generates vector representations in ChromaDB

### Query Flow

```
User Query → Vector Search (ChromaDB) → Graph Traversal (Neo4j) → Context Packet
```

1. Vector search finds semantically similar code definitions
2. Graph traversal finds structural relationships for each match
3. Context packet combines both sources

### Analysis Flow

```
User Task → Semantic Search → Graph Analysis → LLM Analysis → Structured Insights
```

1. Semantic search finds relevant code
2. Graph analysis identifies dependencies and relationships
3. LLM generates structured insights with actionable recommendations

## Storage Architecture

### Neo4j Graph Database

**Location**: Docker container, accessible at http://localhost:7474

**Schema**:
- **Nodes**:
  - `:File` - Properties: `path`, `hash`, `project_id`
  - `:Function` - Properties: `name`, `signature`, `code`
  - `:Class` - Properties: `name`, `code`
- **Relationships**:
  - `(:File)-[:DEFINES]->(:Function|:Class)`
  - `(:File)-[:IMPORTS]->(:File)`
  - `(:Function)-[:CALLS]->(:Function)`

### ChromaDB Vector Database

**Location**: `.tree_roots/` directory within scanned project

**Content**:
- Vector embeddings of code definitions
- Metadata: definition name, type, file path, code snippet
- Collection per project/repository

## Configuration

### Environment Variables

- `PROJECTS_ROOT`: Parent directory containing projects
- `GOOGLE_API_KEY`: Google API key for Gemini API
- `GEMINI_MODEL`: Default Gemini model for analysis (optional)
- `NEO4J_URI`: Neo4j connection URI (default: `bolt://neo4j:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password

### Model Configuration

**Embedding Model**: 
- Fixed to `gemini-embedding-001` after scanning
- Cannot be changed to ensure consistency in vector database

**Analysis Model**:
- Flexible, can be changed per command
- Default: `gemini-3-pro-preview`
- Can be overridden via `--model` flag or `GEMINI_MODEL` environment variable

## Performance Considerations

### Incremental Sync

- Uses git hashes to identify only changed files
- O(1) performance for large repositories
- Only parses files that have changed since last scan

### Vector Search

- ChromaDB embedded mode for fast local queries
- Pre-computed embeddings stored per project
- Efficient similarity search using cosine distance

### Graph Traversal

- Neo4j optimized for graph queries
- Indexed on file paths for fast lookups
- Efficient relationship traversal up to 5 hops

## Security

### API Keys

- Google API key stored in `.env` file (not committed to git)
- Neo4j credentials stored in `.env` file

### Data Privacy

- All processing happens locally
- No code is sent to external services except for:
  - Embedding generation (Google Gemini API)
  - LLM analysis (Google Gemini API)
- Graph and vector databases stored locally

## Limitations

### Current Limitations

- **Language Support**: Primarily TypeScript/JavaScript (tree-sitter support)
- **Embedding Model**: Fixed after scanning (cannot change without re-scanning)
- **Single Repository**: One repository per scan operation
- **Local Only**: Requires Docker and local infrastructure

### Known Issues

- Import resolution may fail for complex module systems
- Large repositories may take significant time to scan initially
- ChromaDB storage grows with repository size

## Future Architecture Considerations

- **Multi-language Support**: Expand tree-sitter parsers
- **Distributed Storage**: Support for remote Neo4j/ChromaDB instances
- **Caching Layer**: Cache frequently accessed graph queries
- **Incremental Embeddings**: Update embeddings incrementally without full re-scan
- **API Server**: REST API for programmatic access

