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
uvicorn main:api --reload --port 8000

# 3. Start the frontend (in another terminal)
cd frontend
npm run dev

# Access at http://localhost:3033
```

## OpenAPI SDK Generation

The frontend can use an auto-generated TypeScript SDK from the FastAPI OpenAPI specification.

### Generate OpenAPI Spec

```bash
# Generate OpenAPI JSON from FastAPI
python scripts/generate-openapi.py

# Or using npm
npm run generate:openapi
```

This creates `openapi.json` in the project root.

### Generate TypeScript SDK

```bash
# Generate TypeScript SDK from OpenAPI spec
npm run generate:sdk

# Or generate both at once
npm run generate:all
```

The generated SDK will be at `frontend/src/lib/api/`.

### Using the Generated SDK

Once generated, you can replace the manual API client (`frontend/lib/api-client.ts`) with the generated SDK:

```typescript
// Instead of:
import { apiClient } from '@/lib/api-client'

// Use:
import { DefaultApi } from '@/lib/api'
const api = new DefaultApi({ basePath: process.env.NEXT_PUBLIC_API_URL })
```

## Project Structure

```
frontend/
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
├── lib/
│   ├── api-client.ts       # Manual API client (temporary)
│   ├── api/                # Generated OpenAPI SDK (after generation)
│   └── utils.ts            # Utility functions
└── package.json
```

## Environment Variables

Create `frontend/.env.local`:

```env
# For local development
NEXT_PUBLIC_API_URL=http://localhost:8088

# For Docker (handled automatically)
# NEXT_PUBLIC_API_URL=http://app:8000
```

## Development Workflow

1. **Make changes to FastAPI endpoints** in `main.py`
2. **Regenerate OpenAPI spec**: `npm run generate:openapi`
3. **Regenerate SDK** (if using): `npm run generate:sdk`
4. **Update frontend components** to use new endpoints/types
5. **Test locally** or rebuild Docker containers

## Troubleshooting

### CORS Issues

If you see CORS errors, make sure:
- The API is running and accessible
- `NEXT_PUBLIC_API_URL` is set correctly
- In Docker, the frontend can reach the `app` service

### API Connection Issues

- **Docker**: Frontend connects to `http://app:8000` (internal network)
- **Local**: Frontend connects to `http://localhost:8088` (or your configured URL)

### OpenAPI Generation Fails

- Make sure the FastAPI server is running when generating the spec
- Or use the script: `python scripts/generate-openapi.py`

## Features

The web UI provides:

- **Projects Tab**: Browse and select projects from PROJECTS_ROOT
- **Scan Tab**: Scan repositories and sync to Neo4j/ChromaDB
- **Query Tab**: Semantic search with optional graph context
- **Analyze Tab**: Task analysis with actionable insights
- **Plan Tab**: Generate executable plans in XML format

All tabs support selecting a project from the Projects tab, which auto-fills the path field.

