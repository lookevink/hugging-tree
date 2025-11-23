# Deep Link Feature

**Purpose**: Allow users to manually create relationships (edges) between nodes in the graph, enabling curation and explicit linking of code entities.

## Overview

Deep Link provides a manual way to establish relationships between nodes that may not be automatically detected by the parser or deep trace analysis. This is useful for:
- Linking related concepts that aren't directly connected in code
- Creating custom relationship types
- Curating the knowledge graph
- Documenting implicit dependencies

## API Design

### 1. Search Nodes Endpoint

**Endpoint**: `POST /deep-link/search`

**Request**:
```json
{
  "query": "string",           // Search query (name, path, etc.)
  "project_root": "string",    // Project root path
  "limit": 20                  // Optional, default 20
}
```

**Response**:
```json
{
  "nodes": [
    {
      "id": "def:path/to/file::functionName",
      "label": "functionName",
      "type": "function",
      "path": "path/to/file",
      "properties": {
        "name": "functionName",
        "start_line": 10,
        "end_line": 25
      }
    }
  ],
  "total": 5
}
```

**Implementation**:
- Search across File and Definition nodes
- Match by name (fuzzy) and path (fuzzy)
- Filter by project_root
- Return formatted node data similar to get_node_details

### 2. Create Link Endpoint

**Endpoint**: `POST /deep-link/create`

**Request**:
```json
{
  "source_id": "string",       // Source node ID (e.g., "def:path::name")
  "target_id": "string",      // Target node ID
  "rel_type": "string",        // Relationship type (e.g., "RELATES_TO", "DEPENDS_ON", "USES")
  "properties": {              // Optional relationship properties
    "label": "string",
    "notes": "string",
    "source": "deep_link"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "relationship_id": "string"
}
```

**Implementation**:
- Validate both nodes exist
- Create relationship with MERGE (idempotent)
- Support custom relationship types
- Store metadata (source: "deep_link", timestamp, etc.)

## Graph Database Schema

### Relationship Types
- `RELATES_TO` - General relationship
- `DEPENDS_ON` - Dependency relationship
- `USES` - Usage relationship
- `SIMILAR_TO` - Similarity relationship
- Custom types allowed

### Relationship Properties
- `source`: "deep_link" (to distinguish from auto-generated)
- `created_at`: timestamp
- `label`: optional human-readable label
- `notes`: optional notes/description

## Frontend Implementation

### New Tab: "Nurture"

Add a "Nurture" tab to the node details page for managing node associations.

**Features**:
1. **Search Interface**
   - Search input field
   - Real-time search results
   - Display node type, path, and preview

2. **Current Links**
   - Display existing relationships created via deep link
   - Show relationship type and target node
   - Option to remove links

3. **Create New Link**
   - Search for target node
   - Select relationship type from dropdown
   - Optional notes/description
   - Create button

4. **Link Management**
   - List all deep link relationships for current node
   - Filter by relationship type
   - Delete relationships

### UI Components

```
[Nurture Tab]
├── Current Links Section
│   ├── List of existing deep links
│   └── Delete button for each
│
└── Create New Link Section
    ├── Search input
    ├── Search results list
    ├── Relationship type selector
    ├── Notes textarea (optional)
    └── Create Link button
```

## Implementation Steps

1. ✅ Document plan (this file)
2. ⬜ Implement `search_nodes` method in GraphDB
3. ⬜ Implement `create_deep_link_relationship` method in GraphDB
4. ⬜ Add API endpoints in main.py
5. ⬜ Generate OpenAPI schema
6. ⬜ Generate OpenSDK
7. ⬜ Add "Nurture" tab to node details page
8. ⬜ Implement search UI
9. ⬜ Implement link creation UI
10. ⬜ Implement link management UI

## Edge Cases

- **Duplicate Links**: Use MERGE to prevent duplicates
- **Invalid Node IDs**: Validate nodes exist before creating link
- **Self-links**: Allow or prevent? (Allow for now)
- **Circular dependencies**: Allow (graph can handle cycles)
- **Node not found**: Return clear error message
- **Search no results**: Show empty state with helpful message

## Future Enhancements

- Bulk link creation
- Link templates/presets
- Link validation (warnings for unusual patterns)
- Link visualization in graph view
- Export/import link definitions
- Link suggestions based on semantic similarity

