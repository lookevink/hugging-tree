import typer
import os
from dotenv import load_dotenv
from src.scanner import scan_repo
from src.graph import GraphDB
from src.parser import CodeParser
from src.resolver import ImportResolver
from src.embeddings import EmbeddingService
from src.analyzer import ContextAnalyzer
from src.planner import PlanGenerator

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
    n: int = typer.Option(5, help="Number of results to return"),
    with_graph: bool = typer.Option(True, help="Include graph context (dependencies, callers, callees)"),
    xml: bool = typer.Option(False, help="Output as XML context packet for LLMs")
):
    """
    Search the codebase using semantic search, optionally enhanced with graph traversal.
    """
    try:
        embeddings = EmbeddingService(persistence_path=os.path.join(path, ".tree_roots"))
        vector_results = embeddings.query(text, n_results=n)
        
        print(f"\n🔍 Semantic Search Results for: '{text}'\n")
        print("=" * 80)
        
        if with_graph or xml:
            # Connect to graph DB and get expanded context
            graph = GraphDB()
            try:
                if xml:
                    # Output XML context packet
                    xml_packet = graph.generate_context_packet(vector_results)
                    print(xml_packet)
                else:
                    expanded = graph.get_expanded_context(vector_results)
                    
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
                
            finally:
                graph.close()
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
    
    The task parameter can be any string - a question, task description, feature request, bug report, etc.
    The system will find relevant code, analyze dependencies, and provide actionable insights.
    
    Prompt templates support Python-style string formatting with variables:
    - {task}: The user's task description
    - {xml_context}: The XML context packet with code and relationships
    - {expanded_context}: The expanded context dictionary (JSON)
    - {semantic_matches_count}: Number of semantic matches found
    - {related_files_count}: Number of related files in graph
    
    Note: The embedding model (for semantic search) is fixed and cannot be changed after scanning.
    Only the analysis model (for LLM generation) can be configured.
    """
    try:
        # Load prompt template if provided (CLI flag takes precedence over env var)
        custom_template_path = prompt_template or os.getenv("ANALYZE_PROMPT_TEMPLATE")
        
        analyzer = ContextAnalyzer(
            persistence_path=os.path.join(path, ".tree_roots"),
            model_name=model,
            prompt_template=custom_template_path  # Pass path, let ContextAnalyzer load it
        )
        
        print(f"\n🔍 Analyzing task: '{task}'\n")
        print(f"🤖 Using model: {analyzer.model_name}\n")
        print("=" * 80)
        print("Gathering context from codebase...\n")
        
        result = analyzer.analyze_task(task, n_results=n)
        
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
        
        analyzer.close()
        
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
        # Load prompt template if provided (CLI flag takes precedence over env var)
        custom_template_path = prompt_template or os.getenv("PLAN_PROMPT_TEMPLATE")
        
        planner = PlanGenerator(
            persistence_path=os.path.join(path, ".tree_roots"),
            model_name=model,
            prompt_template=custom_template_path
        )
        
        print(f"\n📋 Generating plan for: '{task}'\n")
        print(f"🤖 Using model: {planner.model_name}\n")
        print("=" * 80)
        print("Gathering context and generating plan...\n")
        
        plan_xml = planner.generate_plan(task, n_results=n)
        
        print(plan_xml)
        
        planner.close()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
