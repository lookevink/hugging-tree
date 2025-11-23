import typer
import os
import subprocess
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.scanner import scan_repo
from src.graph import GraphDB
from src.parser import CodeParser
from src.resolver import ImportResolver
from src.embeddings import EmbeddingService
from src.analyzer import ContextAnalyzer
from src.planner import PlanGenerator
from src.deep_trace import DeepTraceService

# Load environment variables (don't override existing env vars)
load_dotenv(override=False)

# --- 1. SETUP APPS ---
app = typer.Typer()
api = FastAPI(title="Hugging Tree API", description="API for Hugging Tree Codebase Analysis")

# Add CORS middleware to allow direct client calls (bypassing Next.js proxy)
# This avoids the 30s rewrite timeout issue
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3033", "http://localhost:3000"],  # Next.js dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODELS ---
class ScanRequest(BaseModel):
    path: str

class QueryRequest(BaseModel):
    text: str
    path: str
    n: int = 5
    with_graph: bool = True
    xml: bool = False

class AnalyzeRequest(BaseModel):
    task: str
    path: str
    n: int = 10
    model: Optional[str] = None
    prompt_template: Optional[str] = None

class PlanRequest(BaseModel):
    task: str
    path: str
    n: int = 10
    model: Optional[str] = None
    prompt_template: Optional[str] = None
    format: Optional[str] = "json" # "json" or "xml"

class GraphRequest(BaseModel):
    project_root: str
    file_paths: Optional[List[str]] = None
    max_nodes: int = 500

class DeepTraceAnalyzeRequest(BaseModel):
    node_id: str
    project_root: str

class DeepTraceApplyRequest(BaseModel):
    source_id: str
    target_id: str
    rel_type: str

# --- 3. SHARED LOGIC ---

def logic_scan(path: str) -> Dict[str, Any]:
    """Core logic for scanning a repository."""
    print(f"Scanning repository at: {path}")
    
    try:
        # 1. Scan the repo
        files = scan_repo(path)
        file_count = len(files)
        print(f"Found {file_count} files in git index.")
        
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
                full_path = os.path.join(path, file_info.path)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    definitions, imports, calls = parser.parse_file(file_info.path, source_code)
                    
                    # Sync Definitions
                    if definitions:
                        graph.sync_definitions(file_info.path, definitions)
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
                            
                            resolved_calls.append({
                                'caller_name': call.context,
                                'callee_name': callee_name,
                                'target_file': target_file,
                                'line': call.start_line
                            })
                            
                        if resolved_calls:
                            graph.sync_calls(file_info.path, resolved_calls)
                            
                    print(f"  Processed {file_info.path}: {len(definitions)} defs, {len(imports)} imports, {len(calls)} calls")
                        
                except Exception as e:
                    print(f"  Failed to parse {file_info.path}: {e}")

            final_count = graph.get_file_count()
            print(f"Sync complete. Total files in graph: {final_count}")
            return {"status": "success", "files_scanned": file_count, "total_files_in_graph": final_count}
            
        finally:
            graph.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

def logic_query(text: str, path: str, n: int, with_graph: bool, xml: bool) -> Dict[str, Any]:
    """Core logic for querying the codebase."""
    embeddings = EmbeddingService(persistence_path=os.path.join(path, ".tree_roots"))
    vector_results = embeddings.query(text, n_results=n)
    
    result = {
        "vector_results": vector_results,
        "expanded_context": None,
        "xml_packet": None
    }
    
    if with_graph or xml:
        # Connect to graph DB and get expanded context
        graph = GraphDB()
        try:
            if xml:
                # Output XML context packet
                result["xml_packet"] = graph.generate_context_packet(vector_results)
            else:
                result["expanded_context"] = graph.get_expanded_context(vector_results)
        finally:
            graph.close()
            
    return result

def logic_analyze(task: str, path: str, n: int, model: Optional[str], prompt_template: Optional[str]) -> Dict[str, Any]:
    """Core logic for analyzing a task."""
    # Load prompt template if provided (CLI flag takes precedence over env var)
    custom_template_path = prompt_template or os.getenv("ANALYZE_PROMPT_TEMPLATE")
    
    analyzer = ContextAnalyzer(
        persistence_path=os.path.join(path, ".tree_roots"),
        model_name=model,
        prompt_template=custom_template_path
    )
    
    try:
        result = analyzer.analyze_task(task, n_results=n)
        return {
            "model_name": analyzer.model_name,
            "analysis_result": result
        }
    finally:
        analyzer.close()

def logic_plan(task: str, path: str, n: int, model: Optional[str], prompt_template: Optional[str]) -> Dict[str, Any]:
    """Core logic for generating a plan."""
    # Load prompt template if provided (CLI flag takes precedence over env var)
    custom_template_path = prompt_template or os.getenv("PLAN_PROMPT_TEMPLATE")
    
    planner = PlanGenerator(
        persistence_path=os.path.join(path, ".tree_roots"),
        model_name=model,
        prompt_template=custom_template_path
    )
    
    try:
        plan_result = planner.generate_plan(task, n_results=n)
        return {
            "model_name": planner.model_name,
            "plan_xml": plan_result["plan_xml"],
            "related_files": plan_result["related_files"],
            "semantic_matches": plan_result["semantic_matches"],
            "semantic_matches_count": plan_result["semantic_matches_count"]
        }
    finally:
        planner.close()

def logic_get_graph(path: str, file_paths: Optional[List[str]] = None, max_nodes: int = 500) -> Dict[str, Any]:
    """Core logic for getting graph data for visualization."""
    graph = GraphDB()
    try:
        return graph.get_graph_for_visualization(path, file_paths=file_paths, max_nodes=max_nodes)
    finally:
        graph.close()

def logic_list_projects() -> Dict[str, Any]:
    """Core logic for listing available projects."""
    projects_root = os.getenv("PROJECTS_ROOT")
    
    if not projects_root:
        return {
            "projects_root": None,
            "projects": [],
            "error": "PROJECTS_ROOT environment variable is not set"
        }
    
    if not os.path.exists(projects_root):
        return {
            "projects_root": projects_root,
            "projects": [],
            "error": f"PROJECTS_ROOT path does not exist: {projects_root}"
        }
    
    projects = []
    
    # Get all directories in PROJECTS_ROOT
    try:
        entries = os.listdir(projects_root)
    except PermissionError:
        return {
            "projects_root": projects_root,
            "projects": [],
            "error": f"Permission denied accessing PROJECTS_ROOT: {projects_root}"
        }
    
    # Check Neo4j for scanned projects and get file counts
    graph = GraphDB()
    project_file_counts = {}  # Map project_root -> file_count
    scanned_projects = set()
    try:
        with graph.driver.session() as session:
            # Get all projects with their file counts in one query
            result = session.run(
                "MATCH (f:File) WHERE f.project_root IS NOT NULL "
                "RETURN f.project_root as project_root, count(f) as file_count"
            )
            for record in result:
                project_root = record["project_root"]
                file_count = record["file_count"]
                if project_root:
                    scanned_projects.add(project_root)
                    project_file_counts[project_root] = file_count
    finally:
        graph.close()
    
    for entry in entries:
        entry_path = os.path.join(projects_root, entry)
        
        # Skip if not a directory
        if not os.path.isdir(entry_path):
            continue
        
        # Check if it's a git repository
        is_git_repo = False
        if os.path.exists(os.path.join(entry_path, ".git")):
            is_git_repo = True
        else:
            # Check if it's inside a git work tree
            try:
                subprocess.check_call(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=entry_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                is_git_repo = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        # Check if it's been scanned
        is_scanned = False
        file_count = 0
        
        # Check for .tree_roots directory (embeddings exist)
        tree_roots_path = os.path.join(entry_path, ".tree_roots")
        has_embeddings = os.path.exists(tree_roots_path) and os.path.isdir(tree_roots_path)
        
        # Check if project exists in Neo4j
        if entry_path in scanned_projects:
            is_scanned = True
            file_count = project_file_counts.get(entry_path, 0)
        elif has_embeddings:
            is_scanned = True
        
        projects.append({
            "name": entry,
            "path": entry_path,
            "is_git_repo": is_git_repo,
            "is_scanned": is_scanned,
            "file_count": file_count if is_scanned else 0
        })
    
    # Sort by name
    projects.sort(key=lambda x: x["name"])
    
    return {
        "projects_root": projects_root,
        "projects": projects,
        "total": len(projects),
        "scanned_count": sum(1 for p in projects if p["is_scanned"])
    }


# --- 4. FASTAPI INTERFACE (WEB) ---

@api.post("/scan")
def api_scan(request: ScanRequest):
    try:
        return logic_scan(request.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/query")
def api_query(request: QueryRequest):
    try:
        return logic_query(request.text, request.path, request.n, request.with_graph, request.xml)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/analyze")
def api_analyze(request: AnalyzeRequest):
    try:
        return logic_analyze(request.task, request.path, request.n, request.model, request.prompt_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/plan")
def api_plan(request: PlanRequest):
    try:
        result = logic_plan(request.task, request.path, request.n, request.model, request.prompt_template)
        
        # Always return JSON with plan_xml as a string field
        # The XML is still valid and copyable, but now we also have structured data for visualization
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/graph")
async def get_graph(request: GraphRequest):
    """
    Get graph data for visualization.
    Returns nodes and edges in a format suitable for graph visualization libraries.
    """
    try:
        graph = GraphDB()
        data = graph.get_graph_for_visualization(request.project_root, request.file_paths, request.max_nodes)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/deep-trace/analyze")
async def deep_trace_analyze(request: DeepTraceAnalyzeRequest):
    """
    Analyzes a node for potential deep trace relationships.
    """
    try:
        graph = GraphDB()
        service = DeepTraceService(graph)
        return service.analyze_node(request.node_id, request.project_root)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/deep-trace/apply")
async def deep_trace_apply(request: DeepTraceApplyRequest):
    """
    Applies a deep trace relationship between two nodes.
    """
    try:
        graph = GraphDB()
        service = DeepTraceService(graph)
        service.apply_relationship(request.source_id, request.target_id, request.rel_type)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.get("/projects")
def api_list_projects():
    """
    List all available projects in PROJECTS_ROOT.
    Returns project information including scan status and file counts.
    """
    try:
        return logic_list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. TYPER INTERFACE (CLI) ---

@app.command()
def scan(path: str = typer.Option(..., help="Path to the repository to scan")):
    """
    Scan the repository for changes and sync to Neo4j.
    """
    try:
        logic_scan(path)
    except Exception as e:
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
def projects():
    """
    List all available projects in PROJECTS_ROOT.
    """
    try:
        result = logic_list_projects()
        
        if result.get("error"):
            print(f"Error: {result['error']}")
            raise typer.Exit(code=1)
        
        projects_root = result["projects_root"]
        projects = result["projects"]
        total = result["total"]
        scanned_count = result["scanned_count"]
        
        print(f"\n📁 Projects in: {projects_root}\n")
        print("=" * 80)
        
        if not projects:
            print("No projects found.")
            return
        
        for i, project in enumerate(projects, 1):
            status_icon = "✅" if project["is_scanned"] else "⏳"
            git_icon = "📦" if project["is_git_repo"] else "📂"
            
            print(f"\n[{i}] {project['name']}")
            print(f"    {git_icon} Path: {project['path']}")
            print(f"    {status_icon} Status: {'Scanned' if project['is_scanned'] else 'Not scanned'}")
            
            if project["is_git_repo"]:
                print(f"    🔷 Git Repository: Yes")
            else:
                print(f"    🔷 Git Repository: No")
            
            if project["is_scanned"]:
                print(f"    📊 Files in graph: {project['file_count']}")
        
        print("\n" + "=" * 80)
        print(f"\n📊 Summary:")
        print(f"   • Total projects: {total}")
        print(f"   • Scanned: {scanned_count}")
        print(f"   • Not scanned: {total - scanned_count}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def query(
    text: str = typer.Option(..., help="The natural language query"),
    path: str = typer.Option(..., help="Path to the repository (for loading embeddings)"),
    n: int = typer.Option(5, help="Number of results to return"),
    with_graph: bool = typer.Option(True, help="Include graph context (dependencies, callers, callees)"),
    xml: bool = typer.Option(False, help="Output as XML context packet for LLMs")
):
    """
    Search the codebase using semantic search, optionally enhanced with graph traversal.
    """
    try:
        results = logic_query(text, path, n, with_graph, xml)
        
        vector_results = results["vector_results"]
        
        print(f"\n🔍 Semantic Search Results for: '{text}'\n")
        print("=" * 80)
        
        if results["xml_packet"]:
            
             print(results["xml_packet"])
             return

        if results["expanded_context"]:
            expanded = results["expanded_context"]
            
            for i, item in enumerate(expanded['semantic_matches'], 1):
                result = item['vector_result']
                context = item['graph_context']
                meta = result['metadata']
                
                print(f"\n[{i}] {meta['name']} ({meta['type']})")
                print(f"    📄 File: {meta['file_path']}:{meta['start_line']}")
                print(f"    🎯 Semantic Score: {result['score']:.4f}")
                print(f"    📝 Code snippet:\n{result['document'][:200]}...")
                
                # Show graph context
                if context:
                    print(f"\n    🔗 Graph Context:")
                    
                    if context.get('callers'):
                        print(f"       ⬇️  Called by: {', '.join([c['name'] for c in context['callers'][:5]])}")
                        if len(context['callers']) > 5:
                            print(f"          ... and {len(context['callers']) - 5} more")
                    
                    if context.get('callees'):
                        print(f"       ⬆️  Calls: {', '.join([c['name'] for c in context['callees'][:5]])}")
                        if len(context['callees']) > 5:
                            print(f"          ... and {len(context['callees']) - 5} more")
                    
                    if context.get('dependents'):
                        print(f"       📦 Used by files: {len(context['dependents'])} file(s)")
                        for dep in context['dependents'][:3]:
                            print(f"          - {dep}")
                        if len(context['dependents']) > 3:
                            print(f"          ... and {len(context['dependents']) - 3} more")
                    
                    if context.get('dependencies'):
                        print(f"       📥 Depends on: {len(context['dependencies'])} file(s)")
                        for dep in context['dependencies'][:3]:
                            print(f"          - {dep}")
                        if len(context['dependencies']) > 3:
                            print(f"          ... and {len(context['dependencies']) - 3} more")
                
                print()
            
            print("=" * 80)
            print(f"\n📊 Summary:")
            print(f"   • Found {len(expanded['semantic_matches'])} semantic matches")
            print(f"   • Related files in graph: {expanded['total_files']}")
            
        else:
            # Just show vector search results
            for i, r in enumerate(vector_results, 1):
                meta = r['metadata']
                print(f"\n[{i}] {meta['name']} ({meta['type']})")
                print(f"    📄 File: {meta['file_path']}:{meta['start_line']}")
                print(f"    🎯 Score: {r['score']:.4f}")
                print(f"    📝 Code snippet:\n{r['document'][:200]}...\n")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def analyze(
    task: str = typer.Option(..., help="Any query, task description, or question about the codebase"),
    path: str = typer.Option(..., help="Path to the repository"),
    n: int = typer.Option(10, help="Number of semantic matches to consider"),
    model: str = typer.Option(None, help="Gemini model to use for analysis (e.g., 'gemini-3-pro-preview', 'gemini-2.5-pro', 'gemini-2.5-flash'). Defaults to GEMINI_MODEL env var or 'gemini-3-pro-preview'"),
    prompt_template: str = typer.Option(None, help="Path to a custom prompt template file. Can also be set via ANALYZE_PROMPT_TEMPLATE environment variable.")
):
    """
    Analyze a query/task and generate actionable context including files to modify, blast radius, and step-by-step actions.
    """
    try:
        output = logic_analyze(task, path, n, model, prompt_template)
        result = output["analysis_result"]
        model_name = output["model_name"]
        
        print(f"\n🔍 Analyzing task: '{task}'\n")
        print(f"🤖 Using model: {model_name}\n")
        print("=" * 80)
        
        # Display structured analysis
        structured = result['structured']
        
        print("=" * 80)
        print("\n📋 ANALYSIS RESULTS\n")
        print("=" * 80)
        
        # Files to Modify
        if structured.get('files_to_modify'):
            print("\n📝 FILES TO MODIFY:")
            print("-" * 80)
            for i, file in enumerate(structured['files_to_modify'], 1):
                print(f"  {i}. {file}")
        
        # Blast Radius
        if structured.get('blast_radius'):
            print("\n💥 BLAST RADIUS (Affected Files):")
            print("-" * 80)
            for i, file in enumerate(structured['blast_radius'], 1):
                print(f"  {i}. {file}")
        
        # Actions
        if structured.get('actions'):
            print("\n✅ STEP-BY-STEP ACTIONS:")
            print("-" * 80)
            for i, action in enumerate(structured['actions'], 1):
                print(f"  {i}. {action}")
        
        # Dependencies
        if structured.get('dependencies'):
            print("\n🔗 DEPENDENCIES TO CONSIDER:")
            print("-" * 80)
            for i, dep in enumerate(structured['dependencies'], 1):
                print(f"  {i}. {dep}")
        
        # Risks
        if structured.get('risks'):
            print("\n⚠️  RISKS & BREAKING CHANGES:")
            print("-" * 80)
            for i, risk in enumerate(structured['risks'], 1):
                print(f"  {i}. {risk}")
        
        # Full analysis
        print("\n" + "=" * 80)
        print("\n📄 FULL ANALYSIS:")
        print("=" * 80)
        print(result['analysis'])
        
        print("\n" + "=" * 80)
        print(f"\n📊 SUMMARY:")
        print(f"   • Semantic matches found: {result['semantic_matches']}")
        print(f"   • Related files in graph: {len(result['related_files'])}")
        print(f"   • Files to modify: {len(structured.get('files_to_modify', []))}")
        print(f"   • Blast radius files: {len(structured.get('blast_radius', []))}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)


@app.command()
def plan(
    task: str = typer.Option(..., help="The task description or feature request"),
    path: str = typer.Option(..., help="Path to the repository"),
    n: int = typer.Option(10, help="Number of semantic matches to consider"),
    model: str = typer.Option(None, help="Gemini model to use for planning"),
    prompt_template: str = typer.Option(None, help="Path to a custom prompt template file")
):
    """
    Generate an executable, step-by-step plan in XML format for AI coding tools.
    """
    try:
        output = logic_plan(task, path, n, model, prompt_template)
        model_name = output["model_name"]
        plan_xml = output["plan_xml"]
        
        print(f"\n📋 Generating plan for: '{task}'\n")
        print(f"🤖 Using model: {model_name}\n")
        print("=" * 80)
        
        # For CLI, just print the XML (backward compatible)
        print(plan_xml)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
