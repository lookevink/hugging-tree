# Scan Feature

**Purpose**: Build a semantic knowledge graph of your codebase with incremental sync capabilities.

## Core Capabilities

### Incremental Sync
- [x] Use `git ls-files --stage` to get file inventory with hashes
- [x] Compare file hashes against Neo4j to identify changes
- [ ] Only parse files that are new, modified, or deleted (currently parses all files)
- [ ] Delete nodes for files that no longer exist in git
- [x] O(1) performance for large repos (git-based scanning)

### Semantic Parse (Tree-sitter)
- [x] Extract class definitions (`class_definition` / `class_declaration`)
- [x] Extract function definitions (`function_definition` / `function_declaration`)
- [x] Extract method definitions (`method_definition`)
- [x] Extract arrow functions
- [x] Extract import statements (`import_statement`, `import_from_statement`)
- [x] Extract function calls (`call_expression`)
- [x] Capture function signatures (arguments, return types)
- [x] Store raw source code for definitions
- [x] Support Python, TypeScript, JavaScript
- [ ] Support additional languages (Go, Rust, etc.)

### Graph Construction
- [x] Create `:File` nodes with properties `{path, hash, project_root}`
- [x] Create `:Definition` nodes with labels `:Function` or `:Class`
- [x] Create `(:File)-[:DEFINES]->(:Definition)` relationships
- [x] Use `file_path::function_name` as unique ID for definitions
- [x] Create `(:File)-[:IMPORTS]->(:File)` relationships
- [x] Create `(:Function)-[:CALLS]->(:Function)` relationships
- [x] Handle updates (clear old definitions/imports/calls before creating new ones)

### Import Resolution
- [x] Resolve relative imports (`./utils`, `../services`)
- [x] Handle file extensions (`.ts`, `.tsx`, `.js`, `.jsx`, `.py`)
- [x] Handle directory index files (`index.ts`, `index.js`)
- [x] Ignore external imports (node_modules, pip packages)
- [ ] Support TypeScript path aliases (tsconfig paths)
- [ ] Support Python package imports

### Automatic Embedding Generation
- [x] Generate embeddings for all code definitions during scanning
- [x] Use Google Gemini `gemini-embedding-001` model
- [x] Store embeddings in ChromaDB at `.tree_roots/` directory
- [x] Include definition name, type, and code snippet in embedding content
- [x] Handle duplicate IDs (overloads, constructors)
- [x] Handle dimension mismatches (recreate collection if needed)
- [ ] Incremental embedding updates (only re-embed changed definitions)

## Input/Output

**Input**: 
- Path to repository

**Output**: 
- Neo4j graph database (Files, Definitions, Relationships)
- ChromaDB vector database (Embeddings)

## Implementation Status

- [x] Scanner module (`src/scanner.py`)
- [x] Parser module (`src/parser.py`)
- [x] Graph builder module (`src/graph.py`)
- [x] Embeddings module (`src/embeddings.py`)
- [x] Resolver module (`src/resolver.py`)
- [x] CLI command (`main.py scan`)
- [ ] Incremental sync optimization (compare hashes before parsing)

## Future Enhancements

- [ ] Real-time file watching and sync
- [ ] Support for more languages
- [ ] Better import resolution (TypeScript paths, Python packages)
- [ ] Incremental embedding updates
- [ ] Batch processing for large repositories
- [ ] Progress indicators for long scans

