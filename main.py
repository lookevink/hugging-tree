import typer
import os
from dotenv import load_dotenv
from src.scanner import scan_repo
from src.graph import GraphDB
from src.parser import CodeParser

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
        
        try:
            print("Syncing files to Neo4j...")
            graph.sync_files(files, project_root=path)
            
            print("Parsing and syncing definitions...")
            for file_info in files:
                # Read file content
                # Note: In a real incremental scan, we'd only do this for changed files
                full_path = os.path.join(path, file_info.path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    definitions = parser.parse_file(file_info.path, source_code)
                    if definitions:
                        graph.sync_definitions(file_info.path, definitions)
                        print(f"  Parsed {file_info.path}: {len(definitions)} definitions")
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
