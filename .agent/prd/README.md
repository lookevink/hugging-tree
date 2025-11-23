# Product Requirements Document

## Overview

Hugging Tree is a local CLI that builds a Semantic Knowledge Graph of your codebase. It combines Vector Search with Graph Traversal to provide the "Perfect Context Packet" for LLMs.

## Core Features

Detailed feature documentation with progress tracking is available in the `features/` directory:

- **[Scan Feature](features/scan.md)**: Build a semantic knowledge graph with incremental sync
- **[Query Feature](features/query.md)**: Semantic search with graph-enhanced context
- **[Analyze Feature](features/analyze.md)**: Generate actionable insights using LLM analysis
- **[Plan Feature](features/plan.md)**: Generate executable, step-by-step plans in XML for AI coding tools
- **[Vector + Graph Integration](features/vector-graph-integration.md)**: How the two data structures work together

### Quick Summary

1. **Codebase Scanning (`scan`)**: Builds a semantic knowledge graph with incremental sync capabilities
2. **Semantic Query (`query`)**: Searches codebase semantically with graph-enhanced context
3. **Task Analysis (`analyze`)**: Generates actionable insights for any task or question
4. **Execution Planning (`plan`)**: Generates executable, step-by-step plans in XML format for AI coding tools

## Vector + Graph Integration

Hugging Tree combines two powerful data structures:

1. **Vector Database (ChromaDB)**: Semantic similarity search
2. **Graph Database (Neo4j)**: Structural relationship traversal

This dual approach solves the "Blast Radius" problem: semantic search finds the starting point, graph traversal finds the hidden dependencies that don't share keywords.

See [Vector + Graph Integration](features/vector-graph-integration.md) for detailed documentation.

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


