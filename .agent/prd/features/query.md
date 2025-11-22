# Query Feature

**Purpose**: Search your codebase semantically with graph-enhanced context.

## Core Capabilities

### Vector Search
- [x] Query ChromaDB for semantically similar code definitions
- [x] Use Google Gemini `gemini-embedding-001` for query embedding
- [x] Return top N results with similarity scores
- [x] Include definition metadata (name, type, file path, line numbers)
- [x] Include code snippets in results

### Graph Traversal
- [x] Get callers (functions that call this function)
- [x] Get callees (functions called by this function)
- [x] Get dependents (files that import this definition's file)
- [x] Get dependencies (files this file imports)
- [x] Get siblings (other definitions in the same file)
- [x] Expand context for multiple semantic matches
- [x] Collect all related files across matches

### Output Formats
- [x] Human-readable format (default)
  - [x] Display semantic score
  - [x] Display file path and line numbers
  - [x] Display code snippets
  - [x] Display graph context (callers, callees, dependents, dependencies)
  - [x] Display summary statistics
- [x] XML context packet (for LLMs)
  - [x] Generate structured XML with all context
  - [x] Include semantic matches with scores
  - [x] Include graph relationships
  - [x] Include related files list
- [x] Vector search only (no graph context)
  - [x] `--no-with-graph` flag support

### Perfect Context Packet
- [x] Combine semantic search results with graph relationships
- [x] Generate comprehensive context for LLMs
- [x] Include all relevant files and relationships
- [x] Format as XML for easy LLM consumption

## Input/Output

**Input**: 
- Query text (natural language)
- Repository path (for loading embeddings)
- Number of results (default: 5)
- Output format options

**Output**: 
- Context packet with semantic matches + graph relationships
- Formatted as human-readable or XML

## Implementation Status

- [x] Vector search query (`src/embeddings.py`)
- [x] Graph context retrieval (`src/graph.py`)
- [x] Context packet generation (`src/graph.py`)
- [x] XML formatting (`src/graph.py`)
- [x] CLI command (`main.py query`)
- [x] Human-readable output formatting
- [x] XML output option (`--xml`)
- [x] Vector-only option (`--no-with-graph`)

## Future Enhancements

- [ ] Query templates for common patterns
- [ ] Filter by file type, language, or other metadata
- [ ] Export results to various formats (JSON, CSV)
- [ ] Interactive query refinement
- [ ] Query history and saved queries
- [ ] Multi-repository queries

