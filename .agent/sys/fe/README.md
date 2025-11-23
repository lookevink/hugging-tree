# Frontend Setup Guide

This guide explains how to set up and use the Hugging Tree Next.js frontend.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start all services including frontend
docker compose up -d --build

# Access the web UI at http://localhost:3033
# API will be available at http://localhost:8088
```

### Option 2: Local Development

```bash
# 1. Generate OpenAPI spec and setup frontend
./scripts/setup-frontend.sh

# 2. Start the backend API (in one terminal)
uvicorn main:api --reload --port 8088

# 3. Start the frontend (in another terminal)
cd hugging-tree-fe
pnpm run dev

# Access at http://localhost:3033
```

## OpenAPI SDK Generation

The frontend uses an auto-generated TypeScript SDK from the FastAPI OpenAPI specification. We use [Hey API](https://heyapi.xyz/) - FastAPI's recommended TypeScript SDK generator.

### Generate OpenAPI Spec

```bash
# Generate OpenAPI JSON from FastAPI (from project root)
python scripts/generate-openapi.py
```

This creates `openapi.json` in the project root.

**Note**: The script will try to fetch from a running server first (no dependencies needed), or import the FastAPI app directly (requires Python dependencies).

### Generate TypeScript SDK

```bash
# Generate TypeScript SDK from OpenAPI spec (uses npx or Docker)
python scripts/generate-sdk.py

# Or generate both at once
python scripts/generate-openapi.py && python scripts/generate-sdk.py
```

The generated SDK will be at `hugging-tree-fe/src/lib/api/`.

**Note**: 
- Uses `@hey-api/openapi-ts` via npx (no installation needed)
- Falls back to Docker if npx is not available
- No npm/Node.js needed at project root - pure Python scripts!

### Using the Generated SDK

Once generated, you can use the generated SDK:

```typescript
import { client } from '@/src/lib/api'
import type { paths } from '@/src/lib/api/types'

// Use the generated client
const response = await client.GET('/projects')
```

See the generated SDK files in `hugging-tree-fe/src/lib/api/` for full API.

## Project Structure

```
hugging-tree-fe/
├── app/                    # Next.js app directory
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main page with tabs
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn UI components
│   ├── projects-tab.tsx    # Projects management
│   ├── scan-tab.tsx        # Repository scanning
│   ├── query-tab.tsx       # Semantic search
│   ├── analyze-tab.tsx     # Task analysis
│   └── plan-tab.tsx        # Plan generation
├── src/
│   └── lib/
│       ├── api/            # Generated OpenAPI SDK
│       │   ├── client/     # Client implementation
│       │   ├── core/       # Core utilities
│       │   ├── sdk.gen.ts  # Main SDK export
│       │   └── types.gen.ts # TypeScript types
│       └── utils.ts        # Utility functions
└── package.json            # Frontend dependencies (uses pnpm)
```

## Environment Variables

Create `hugging-tree-fe/.env.local` (optional):

```env
# For local development (if not using Next.js rewrites)
NEXT_PUBLIC_API_URL=http://localhost:8088
```

**Note**: Next.js rewrites handle API proxying automatically. The `next.config.ts` proxies `/api/*` requests to the backend.

## Development Workflow

1. **Make changes to FastAPI endpoints** in `main.py`
2. **Regenerate OpenAPI spec**: `python scripts/generate-openapi.py`
3. **Regenerate SDK**: `python scripts/generate-sdk.py`
4. **Update frontend components** to use new endpoints/types
5. **Test locally** or rebuild Docker containers

## Troubleshooting

### CORS Issues

If you see CORS errors, make sure:
- The API is running and accessible
- Next.js rewrites are configured correctly in `next.config.ts`
- In Docker, the frontend can reach the `app` service via internal network

### API Connection Issues

- **Docker**: Next.js rewrites proxy to `http://app:8000` (internal network)
- **Local**: Next.js rewrites proxy to `http://localhost:8088` (or configured URL)
- Client-side requests go through Next.js server which handles proxying

### OpenAPI Generation Fails

- **Option 1**: Start the server first, then generate (script will fetch from server)
  ```bash
  uvicorn main:api --port 8088
  python scripts/generate-openapi.py
  ```
- **Option 2**: Install Python dependencies, then generate (script will import FastAPI app)
  ```bash
  pip install -r requirements.txt
  python scripts/generate-openapi.py
  ```

### SDK Generation Fails

- Make sure `openapi.json` exists (run `python scripts/generate-openapi.py` first)
- Ensure npx is available (comes with Node.js) or Docker is running
- Check that the output directory `hugging-tree-fe/src/lib/api/` is writable

## Features

The web UI provides:

- **Projects Tab**: Browse and select projects from PROJECTS_ROOT
- **Scan Tab**: Scan repositories and sync to Neo4j/ChromaDB
- **Query Tab**: Semantic search with optional graph context
- **Analyze Tab**: Task analysis with actionable insights
- **Plan Tab**: Generate executable plans in XML format

All tabs support selecting a project from the Projects tab, which auto-fills the path field.

