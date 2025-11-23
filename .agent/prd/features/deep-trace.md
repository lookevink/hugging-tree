# Deep Trace Feature

**Purpose**: Leverage LLMs to discover and establish implicit relationships (like API calls, event bus messages) that static analysis misses, enabling a "Deep Trace" capability from the graph visualization.

## Core Capabilities

### On-Demand Analysis
- [ ] Triggered by user action from the Graph Visualization UI
- [ ] Context-aware analysis based on the selected node (Function or File)

### LLM Code Analysis
- [ ] Retrieve source code for the selected node
- [ ] Prompt LLM to identify implicit external calls (e.g., `fetch('/api/v1/users')`, `producer.send('user-created')`)
- [ ] Extract structured data: Method, URL/Topic, Payload structure

### Target Matching
- [ ] Search existing graph nodes (Definitions, API Endpoints) for matches
- [ ] Use vector embeddings to find semantically similar endpoints if exact string match fails
- [ ] Verify existence of the target within the project boundaries

### Graph Enrichment
- [ ] Propose new relationships (e.g., `[:CALLS_API]`, `[:PRODUCES_EVENT]`)
- [ ] Create new nodes if necessary (e.g., `ApiEndpoint`, `EventTopic`)
- [ ] Persist confirmed relationships to Neo4j

## User Interface

### Graph Node Dialog
- [ ] Add "Deep Trace" button to the node details dialog
- [ ] Show loading state during LLM analysis
- [ ] Display discovered relationships
- [ ] Option to approve/reject proposed links

## Input/Output

**Input**:
- Selected Node ID (Function or File) from the graph

**Output**:
- New relationships (Edges) in the Neo4j graph
- Updated graph visualization showing the new connections

## Implementation Plan

- [ ] Backend: New `/deep-trace` endpoint in `main.py`
- [ ] Backend: `DeepTraceService` to handle LLM interaction and graph updates
- [ ] Frontend: Update `GraphTab` component to include "Deep Trace" action
- [ ] Frontend: UI for displaying and confirming results
