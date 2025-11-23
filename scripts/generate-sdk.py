#!/usr/bin/env python3
"""
Generate TypeScript SDK from OpenAPI specification using Hey API.

Hey API is FastAPI's recommended TypeScript SDK generator - purpose-built and optimized.
Uses npx so no installation needed (or Docker as fallback).
"""
import os
import subprocess
import sys

def generate_sdk_with_npx(openapi_file, output_dir):
    """Generate SDK using npx (no installation needed)."""
    npx_cmd = [
        "npx", "-y", "@hey-api/openapi-ts",
        "-i", openapi_file,
        "-o", output_dir
    ]
    
    print("🔧 Generating TypeScript SDK using Hey API (npx)...")
    print(f"   Input: {openapi_file}")
    print(f"   Output: {output_dir}")
    print(f"   Tool: @hey-api/openapi-ts (FastAPI recommended)")
    
    try:
        result = subprocess.run(npx_cmd, check=True, capture_output=True, text=True)
        print("✅ TypeScript SDK generated successfully!")
        print(f"   SDK available at: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate SDK with npx:")
        if e.stderr:
            print(f"   {e.stderr}")
        if e.stdout:
            print(f"   {e.stdout}")
        return False
    except FileNotFoundError:
        return False

def generate_sdk_with_docker(openapi_file, output_dir, project_root):
    """Generate SDK using Docker as fallback."""
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_root}:/local",
        "-w", "/local",
        "node:20-alpine",
        "npx", "-y", "@hey-api/openapi-ts",
        "-i", "/local/openapi.json",
        "-o", "/local/hugging-tree-fe/src/lib/api"
    ]
    
    print("🔄 Trying Docker fallback...")
    print(f"   Using: Docker (node:20-alpine + npx)")
    
    try:
        result = subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
        print("✅ TypeScript SDK generated successfully!")
        print(f"   SDK available at: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate SDK with Docker:")
        if e.stderr:
            print(f"   {e.stderr}")
        return False
    except FileNotFoundError:
        return False

def generate_sdk():
    """Generate TypeScript SDK from openapi.json using Hey API."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    openapi_file = os.path.join(project_root, "openapi.json")
    output_dir = os.path.join(project_root, "hugging-tree-fe", "src", "lib", "api")
    
    # Check if openapi.json exists
    if not os.path.exists(openapi_file):
        print(f"❌ OpenAPI spec not found: {openapi_file}")
        print("   Run 'python scripts/generate-openapi.py' first")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Try npx first (fastest, no Docker needed)
    if generate_sdk_with_npx(openapi_file, output_dir):
        return output_dir
    
    # Fallback to Docker if npx not available
    print("\n⚠️  npx not found, trying Docker...")
    if generate_sdk_with_docker(openapi_file, output_dir, project_root):
        return output_dir
    
    # If both fail, provide helpful error
    print("\n❌ Failed to generate SDK with both methods.")
    print("\n💡 Options:")
    print("1. Install Node.js (includes npx): https://nodejs.org/")
    print("2. Or install Docker: https://docs.docker.com/get-docker/")
    print("3. Or run manually:")
    print(f"   npx -y @hey-api/openapi-ts -i {openapi_file} -o {output_dir}")
    sys.exit(1)

if __name__ == "__main__":
    generate_sdk()

