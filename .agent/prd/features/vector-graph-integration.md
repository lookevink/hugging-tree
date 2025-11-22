# Vector + Graph Integration

**Purpose**: Combine Vector Search with Graph Traversal to provide comprehensive code understanding.

## Core Concept

Hugging Tree combines two powerful data structures:

1. **Vector Database (ChromaDB)**: Semantic similarity search
2. **Graph Database (Neo4j)**: Structural relationship traversal

This dual approach solves the "Blast Radius" problem: semantic search finds the starting point, graph traversal finds the hidden dependencies that don't share keywords.

## Vector Database (ChromaDB)

### Purpose
- [x] Semantic similarity search
- [x] Find code that does something similar to X

### Storage
- [x] Code embeddings (vector representations of functions, classes, methods)
- [x] Metadata (name, type, file path, line numbers)
- [x] Code snippets for context
- [x] Location: `.tree_roots/` directory in project root

### Capabilities
- [x] Generate embeddings using `gemini-embedding-001`
- [x] Store embeddings in ChromaDB (embedded mode)
- [x] Query embeddings for semantic similarity
- [x] Handle dimension mismatches
- [x] Persistent storage across sessions

## Graph Database (Neo4j)

### Purpose
- [x] Structural relationship traversal
- [x] Answer questions like "What breaks if I change this file?" or "Who calls this function?"

### Storage
- [x] Files (nodes with path, hash, project_root)
- [x] Definitions (Function, Class nodes)
- [x] Imports (IMPORTS relationships between files)
- [x] Function calls (CALLS relationships between functions)
- [x] Definition relationships (DEFINES relationships)

### Capabilities
- [x] Traverse import dependencies
- [x] Traverse function call chains
- [x] Find dependents (files that import a file)
- [x] Find dependencies (files a file imports)
- [x] Find callers (functions that call a function)
- [x] Find callees (functions called by a function)
- [x] Find siblings (other definitions in same file)

## The Perfect Context Packet

### Process
- [x] Find semantically similar code using vector search (ChromaDB)
- [x] Traverse graph relationships to find structural connections (Neo4j)
- [x] Combine both into comprehensive context packet

### Context Includes
- [x] The matching code (from vector search)
- [x] What calls it (from graph)
- [x] What it calls (from graph)
- [x] What files depend on it (from graph)
- [x] What files it depends on (from graph)

## Implementation Status

- [x] Vector search integration (`src/embeddings.py`)
- [x] Graph traversal integration (`src/graph.py`)
- [x] Context packet generation (`src/graph.py`)
- [x] XML formatting for LLMs
- [x] Human-readable formatting
- [x] Used in query command
- [x] Used in analyze command

## Future Enhancements

- [ ] Caching layer for frequently accessed queries
- [ ] Incremental graph updates
- [ ] Graph visualization tools
- [ ] Advanced graph queries (shortest path, cycles, etc.)
- [ ] Graph analytics (centrality, clustering, etc.)
- [ ] Multi-repository graph traversal

