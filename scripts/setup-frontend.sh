#!/bin/bash
# Setup script for frontend development

set -e

echo "🌳 Setting up Hugging Tree Frontend..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the project root"
    exit 1
fi

# Generate OpenAPI spec
echo "📝 Generating OpenAPI specification..."
python scripts/generate-openapi.py

# Install root dependencies (OpenAPI generator)
if [ ! -d "node_modules" ]; then
    echo "📦 Installing root dependencies..."
    npm install
fi

# Install frontend dependencies
if [ ! -d "hugging-tree-fe/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd hugging-tree-fe
    # Check if pnpm is available, otherwise use npm
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        echo "⚠️  pnpm not found, installing pnpm..."
        npm install -g pnpm
        pnpm install
    fi
    cd ..
fi

# Generate SDK from OpenAPI spec
if [ -f "openapi.json" ]; then
    echo "🔧 Generating TypeScript SDK from OpenAPI spec..."
    npm run generate:sdk || echo "Warning: SDK generation failed, continuing with manual API client"
else
    echo "Warning: openapi.json not found, skipping SDK generation"
fi

echo "✅ Frontend setup complete!"
echo ""
echo "To start development:"
echo "  cd hugging-tree-fe && pnpm run dev"
echo ""
echo "Or use Docker:"
echo "  docker compose up frontend"

