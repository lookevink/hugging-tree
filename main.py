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
                    
                    definitions, imports, calls = parser.parse_file(file_info.path, source_code)
                    
                    # Sync Definitions
                    if definitions:
                        graph.sync_definitions(file_info.path, definitions)
                        
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
                            # 1. Check if it's a local function call (defined in same file)
                            # 2. Check if it's an imported function call
                            
                            target_file = file_info.path # Default to self
                            callee_name = call.name
                            
                            # If call is like 'service.getUser()', we need to resolve 'service'
                            if '.' in call.name:
                                obj, method = call.name.split('.', 1)
                                # Check if 'obj' is an import
                                # This is tricky without full symbol table. 
                                # Simplified: if we imported a module named 'obj', assume method is in that file.
                                # But usually imports are 'import * as service from ...' or 'import { getUser } ...'
                                
                                # Let's try to find if 'obj' matches an imported module name
                                # This is very rough.
                                pass
                            else:
                                # Direct call 'getUser()'
                                # Check if 'getUser' was imported? 
                                # We didn't extract imported names yet in parser.py (TODO item)
                                # So we can't distinguish local vs imported easily without that.
                                pass
                                
                            # FOR NOW: Only link calls if we can guess the target.
                            # Since we don't have imported names, we can't resolve 'getUser' to 'userService.ts' yet.
                            # BUT, we can link local calls!
                            
                            # Let's just try to link local calls for demonstration
                            resolved_calls.append({
                                'caller_name': call.context,
                                'callee_name': call.name,
                                'target_file': file_info.path, # Self-call assumption for now
                                'line': call.start_line
                            })
                            
                        if resolved_calls:
                            graph.sync_calls(file_info.path, resolved_calls)
                            
                    print(f"  Parsed {file_info.path}: {len(definitions)} defs, {len(imports)} imports, {len(calls)} calls")
                        
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
