#!/bin/bash
# Setup script for frontend development

set -e

echo "🌳 Setting up Hugging Tree Frontend..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: Please run this script from the project root"
    exit 1
fi

# Check if Python dependencies are installed
echo "🔍 Checking Python dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Python dependencies not found. Installing..."
    pip install -r requirements.txt || {
        echo "❌ Failed to install Python dependencies"
        echo "   Please install manually: pip install -r requirements.txt"
        exit 1
    }
fi

# Generate OpenAPI spec
echo "📝 Generating OpenAPI specification..."
python scripts/generate-openapi.py || {
    echo "⚠️  OpenAPI generation failed. This is okay if the server isn't running."
    echo "   You can generate it later by running: python scripts/generate-openapi.py"
    echo "   Or start the server first: uvicorn main:api --port 8088"
}

# Check if npx is available (for SDK generation)
if command -v npx &> /dev/null; then
    echo "✅ npx found - will use Hey API for SDK generation"
elif command -v docker &> /dev/null; then
    echo "✅ Docker found - will use as fallback for SDK generation"
else
    echo "⚠️  Neither npx nor Docker found. SDK generation may fail."
    echo "   Install Node.js (includes npx): https://nodejs.org/"
    echo "   Or install Docker: https://docs.docker.com/get-docker/"
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
    python scripts/generate-sdk.py || echo "Warning: SDK generation failed, continuing with manual API client"
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

