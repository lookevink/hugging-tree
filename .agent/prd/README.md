# Product Requirements Document

## Overview

Hugging Tree is a local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Core Features

### 1. Codebase Scanning (`scan`)

**Purpose**: Build a semantic knowledge graph of your codebase with incremental sync capabilities.

**Key Capabilities**:
- **Incremental Sync**: Uses git hashes to identify only new, modified, and deleted files (O(1) performance for large repos)
- **Semantic Parse**: Extracts definitions (classes, functions), signatures (arguments, return types), and dependencies (imports) using tree-sitter
- **Graph Construction**: Creates nodes (Files, Functions, Classes) and relationships (DEFINES, IMPORTS)
- **Automatic Embedding Generation**: Generates vector embeddings for all code definitions during scanning

**Input**: Path to repository
**Output**: Neo4j graph database + ChromaDB vector database

### 2. Semantic Query (`query`)

**Purpose**: Search your codebase semantically with graph-enhanced context.

**Key Capabilities**:
- **Vector Search**: Finds code definitions semantically similar to your query
- **Graph Traversal**: Enhances results with structural relationships:
  - Callers: Functions that call this function
  - Callees: Functions called by this function
  - Dependents: Files that import this definition's file
  - Dependencies: Files this file imports
- **Output Formats**:
  - Human-readable format (default)
  - XML context packet (for LLMs)
  - Vector search only (no graph context)

**Input**: Query text, repository path, number of results
**Output**: Context packet with semantic matches + graph relationships

### 3. Task Analysis (`analyze`)

**Purpose**: Generate actionable insights for any task or question about your codebase.

**Key Capabilities**:
- **Semantic Search**: Finds code semantically similar to your task
- **Graph Analysis**: Analyzes dependencies, callers, callees, and file relationships
- **LLM Analysis**: Uses Gemini to generate structured insights:
  - Files to Modify (ordered by priority)
  - Blast Radius (affected files)
  - Step-by-Step Actions
  - Dependencies
  - Risks & Breaking Changes
  - Full Analysis

**Input**: Task description/question, repository path
**Output**: Structured analysis with actionable insights

**Use Cases**:
- Feature requests
- Bug fixes
- Code understanding
- Refactoring planning

## Vector + Graph Integration

### The Perfect Context Packet

Hugging Tree combines two powerful data structures:

1. **Vector Database (ChromaDB)**: Semantic similarity search
   - Stores code embeddings (vector representations of functions, classes, methods)
   - Use case: "Find code that does something similar to X"

2. **Graph Database (Neo4j)**: Structural relationship traversal
   - Stores files, definitions, imports, function calls
   - Use case: "What breaks if I change this file?" or "Who calls this function?"

When you run a query, the system:
1. Finds semantically similar code using vector search (ChromaDB)
2. Traverses graph relationships to find structural connections (Neo4j)
3. Combines both into a comprehensive context packet

This dual approach solves the "Blast Radius" problem: semantic search finds the starting point, graph traversal finds the hidden dependencies that don't share keywords.

## Future Features

### Planned Enhancements

- **Multi-language Support**: Expand beyond TypeScript/JavaScript to Python, Go, Rust, etc.
- **Incremental Updates**: Real-time sync as files change
- **IDE Integration**: Direct integration with popular IDEs
- **Batch Operations**: Process multiple repositories simultaneously
- **Custom Query Templates**: Save and reuse common query patterns
- **Export Formats**: Export graph data in various formats (JSON, GraphML, etc.)
- **Performance Optimization**: Caching, indexing improvements
- **Advanced Graph Queries**: Pre-built query templates for common use cases

### Research Areas

- **Code Change Impact Prediction**: Predict which files will be affected by a change
- **Code Similarity Detection**: Find duplicate or similar code patterns
- **Architecture Analysis**: Detect architectural patterns and anti-patterns
- **Test Coverage Analysis**: Map test files to production code
- **Documentation Generation**: Auto-generate documentation from code structure

