import typer
import os
from dotenv import load_dotenv
from src.scanner import scan_repo
from src.graph import GraphDB
from src.parser import CodeParser
from src.resolver import ImportResolver

# Load environment variables
load_dotenv()

app = typer.Typer()

@app.command()
def scan(path: str = typer.Option(..., help="Path to the repository to scan")):
    """
    Scan the repository for changes and sync to Neo4j.
    """
    print(f"Scanning repository at: {path}")
    
    try:
        # 1. Scan the repo
        files = scan_repo(path)
        print(f"Found {len(files)} files in git index.")
        
        # 2. Sync to Neo4j
        graph = GraphDB()
        parser = CodeParser()
        resolver = ImportResolver(project_root=path)
        
        try:
            print("Syncing files to Neo4j...")
            graph.sync_files(files, project_root=path)
            
            print("Parsing and syncing definitions & dependencies...")
            for file_info in files:
                # Read file content
                # Note: In a real incremental scan, we'd only do this for changed files
                full_path = os.path.join(path, file_info.path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    definitions, imports = parser.parse_file(file_info.path, source_code)
                    
                    # Sync Definitions
                    if definitions:
                        graph.sync_definitions(file_info.path, definitions)
                        
                    # Sync Dependencies
                    if imports:
                        resolved_deps = []
                        for imp in imports:
                            target = resolver.resolve(file_info.path, imp.module)
                            if target:
                                resolved_deps.append({
                                    'target_path': target,
                                    'line': imp.start_line
                                })
                        
                        if resolved_deps:
                            graph.sync_dependencies(file_info.path, resolved_deps)
                            
                    print(f"  Parsed {file_info.path}: {len(definitions)} defs, {len(imports)} imports")
                        
                except Exception as e:
                    print(f"  Failed to parse {file_info.path}: {e}")

            count = graph.get_file_count()
            print(f"Sync complete. Total files in graph: {count}")
        finally:
            graph.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def parse():
    """
    Parse the changed files.
    """
    print("Parsing files...")
    # TODO: Implement parse logic

if __name__ == "__main__":
    app()
