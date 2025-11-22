import typer
import os
from dotenv import load_dotenv
from src.scanner import scan_repo
from src.graph import GraphDB
from src.parser import CodeParser
from src.resolver import ImportResolver
from src.embeddings import EmbeddingService

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
        embeddings = EmbeddingService(persistence_path=os.path.join(path, ".tree_roots"))
        
        try:
            print("Parsing, syncing graph, and generating embeddings...")
            graph.sync_files(files, project_root=path)
            
            print("Parsing and syncing definitions & dependencies...")
            for file_info in files:
                # Read file content
                # Note: In a real incremental scan, we'd only do this for changed files
                full_path = os.path.join(path, file_info.path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    definitions, imports, calls = parser.parse_file(file_info.path, source_code)
                    
                    # Sync Definitions
                    if definitions:
                        graph.sync_definitions(file_info.path, definitions)
                        # Store Embeddings
                        # print(f"  [DEBUG] Generating embeddings for {len(definitions)} definitions in {file_info.path}")
                        embeddings.store_definitions(file_info.path, definitions)
                        
                    # Sync Dependencies
                    resolved_imports = {} # Map module_name -> resolved_path
                    if imports:
                        resolved_deps = []
                        for imp in imports:
                            target = resolver.resolve(file_info.path, imp.module)
                            if target:
                                resolved_imports[imp.module] = target
                                resolved_deps.append({
                                    'target_path': target,
                                    'line': imp.start_line
                                })
                        
                        if resolved_deps:
                            graph.sync_dependencies(file_info.path, resolved_deps)

                    # Sync Calls (Pass 3)
                    if calls:
                        resolved_calls = []
                        for call in calls:
                            if not call.context:
                                continue # Skip top-level calls for now
                                
                            # Heuristic Resolution
                            target_file = file_info.path # Default to self
                            callee_name = call.name
                            
                            # Try to resolve using imports
                            if '.' in call.name:
                                obj, method = call.name.split('.', 1)
                                if obj in resolved_imports:
                                    target_file = resolved_imports[obj]
                                    callee_name = method
                            
                            # We can't easily distinguish local vs imported calls without more symbol info
                            # But if we assume local unless imported...
                            
                            resolved_calls.append({
                                'caller_name': call.context,
                                'callee_name': callee_name,
                                'target_file': target_file,
                                'line': call.start_line
                            })
                            
                        if resolved_calls:
                            if 'orderHandlers.ts' in file_info.path:
                                # print(f"  [DEBUG] OrderHandlers calls: {resolved_calls[:5]}") # Print first 5
                                pass
                            graph.sync_calls(file_info.path, resolved_calls)
                            
                    print(f"  Processed {file_info.path}: {len(definitions)} defs, {len(imports)} imports, {len(calls)} calls")
                        
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

@app.command()
def query(
    text: str = typer.Option(..., help="The natural language query"),
    path: str = typer.Option(..., help="Path to the repository (for loading embeddings)"),
    n: int = typer.Option(5, help="Number of results to return")
):
    """
    Search the codebase using semantic search.
    """
    try:
        embeddings = EmbeddingService(persistence_path=os.path.join(path, ".tree_roots"))
        results = embeddings.query(text, n_results=n)
        
        print(f"\nResults for: '{text}'\n")
        for r in results:
            meta = r['metadata']
            print(f"--- {meta['name']} ({meta['type']}) ---")
            print(f"File: {meta['file_path']}:{meta['start_line']}")
            print(f"Score: {r['score']:.4f}")
            print(f"Code snippet:\n{r['document'][:200]}...\n")
            
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
