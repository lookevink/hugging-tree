#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.
"""
import json
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import api

def generate_openapi():
    """Generate OpenAPI JSON specification."""
    openapi_schema = api.openapi()
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openapi.json")
    
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI specification generated: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_openapi()

