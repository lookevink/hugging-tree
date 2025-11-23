#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.

This script can work in two ways:
1. Import the FastAPI app directly (requires Python dependencies installed)
2. Fetch from a running server (if server is running on http://localhost:8088)
"""
import json
import sys
import os
import urllib.request
import urllib.error

def generate_from_server(server_url="http://localhost:8088"):
    """Fetch OpenAPI spec from a running server."""
    try:
        openapi_url = f"{server_url}/openapi.json"
        print(f"📡 Fetching OpenAPI spec from {openapi_url}...")
        with urllib.request.urlopen(openapi_url) as response:
            openapi_schema = json.loads(response.read())
        return openapi_schema
    except urllib.error.URLError as e:
        print(f"❌ Could not connect to server at {server_url}")
        print(f"   Error: {e}")
        return None

def generate_from_import():
    """Generate OpenAPI spec by importing the FastAPI app."""
    # Add parent directory to path to import main
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from main import api
        print("📝 Generating OpenAPI spec from FastAPI app...")
        return api.openapi()
    except ImportError as e:
        print(f"❌ Could not import FastAPI app: {e}")
        print("\n💡 Tip: Install Python dependencies first:")
        print("   pip install -r requirements.txt")
        print("\n   Or start the server and use the fetch method:")
        print("   uvicorn main:api --port 8088")
        return None

def generate_openapi():
    """Generate OpenAPI JSON specification."""
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.json")
    
    # Try fetching from running server first (easier, no deps needed)
    openapi_schema = generate_from_server()
    
    # Fall back to importing if server not available
    if not openapi_schema:
        print("\n🔄 Trying to import FastAPI app directly...")
        openapi_schema = generate_from_import()
    
    if not openapi_schema:
        print("\n❌ Failed to generate OpenAPI spec.")
        print("\nOptions:")
        print("1. Install Python dependencies: pip install -r requirements.txt")
        print("2. Start the server: uvicorn main:api --port 8088")
        sys.exit(1)
    
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI specification generated: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_openapi()

