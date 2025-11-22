# Analyze Feature

**Purpose**: Generate actionable insights for any task or question about your codebase.

## Core Capabilities

### Semantic Search Integration
- [x] Find code semantically similar to task description
- [x] Configurable number of semantic matches (default: 10)
- [x] Use vector embeddings for semantic matching

### Graph Analysis
- [x] Analyze dependencies (files that import modified files)
- [x] Analyze callers (functions that call modified functions)
- [x] Analyze callees (functions called by modified code)
- [x] Analyze file relationships
- [x] Build comprehensive context packet

### LLM Analysis
- [x] Use Gemini models for analysis
- [x] Generate structured insights:
  - [x] Files to Modify (ordered by priority)
  - [x] Blast Radius (affected files)
  - [x] Step-by-Step Actions
  - [x] Dependencies to Consider
  - [x] Risks & Breaking Changes
  - [x] Full Analysis
- [x] Model configuration support
  - [x] Default: `gemini-3-pro-preview`
  - [x] Support for `gemini-2.5-pro`
  - [x] Support for `gemini-2.5-flash`
  - [x] Support for `gemini-2.5-flash-lite`
  - [x] Environment variable configuration (`GEMINI_MODEL`)
  - [x] Per-command model override (`--model` flag)

### Structured Extraction
- [x] Parse markdown-style analysis output
- [x] Extract files to modify
- [x] Extract blast radius files
- [x] Extract step-by-step actions
- [x] Extract dependencies
- [x] Extract risks and breaking changes
- [x] Display structured output with formatting

### Use Cases
- [x] Feature requests
- [x] Bug fixes
- [x] Code understanding
- [x] Refactoring planning

## Input/Output

**Input**: 
- Task description/question (any string)
- Repository path
- Number of semantic matches (optional, default: 10)
- Model selection (optional)

**Output**: 
- Structured analysis with actionable insights
- Files to modify (ordered by priority)
- Blast radius (affected files)
- Step-by-step actions
- Dependencies
- Risks & breaking changes
- Full LLM-generated analysis

## Implementation Status

- [x] Context analyzer module (`src/analyzer.py`)
- [x] Semantic search integration
- [x] Graph analysis integration
- [x] LLM prompt building
- [x] LLM analysis generation
- [x] Structured extraction from markdown
- [x] CLI command (`main.py analyze`)
- [x] Model configuration support
- [x] Formatted output display

## Future Enhancements

- [ ] More sophisticated structured extraction (use function calling)
- [ ] Support for multiple analysis models in parallel
- [ ] Analysis templates for common tasks
- [ ] Export analysis to markdown files
- [ ] Integration with issue trackers
- [ ] Analysis history and comparison
- [ ] Multi-repository analysis

