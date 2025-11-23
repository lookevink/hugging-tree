import os
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from .scanner import FileInfo
from .parser import Definition

def _is_running_in_docker() -> bool:
    """Detect if code is running inside a Docker container."""
    # Check for Docker-specific files/environment
    return (
        os.path.exists("/.dockerenv") or
        os.path.exists("/proc/self/cgroup") and "docker" in open("/proc/self/cgroup").read()
    )

def _get_default_neo4j_uri() -> str:
    """Get the default Neo4j URI based on the environment."""
    if _is_running_in_docker():
        # Inside Docker: use service name for inter-container communication
        return "bolt://neo4j:7687"
    else:
        # Local development: use localhost (Neo4j exposed on host)
        return "bolt://localhost:7687"

def _normalize_neo4j_uri(uri: str) -> str:
    """Normalize Neo4j URI for the current environment.
    
    If running in Docker and URI uses localhost, convert to service name.
    This allows the same .env file to work for both local CLI and Docker API.
    """
    if _is_running_in_docker() and "localhost" in uri:
        # Replace localhost with neo4j service name for Docker inter-container communication
        return uri.replace("localhost", "neo4j")
    return uri

class GraphDB:
    def __init__(self):
        uri = os.getenv("NEO4J_URI") or _get_default_neo4j_uri()
        # Normalize URI for current environment (convert localhost to neo4j in Docker)
        uri = _normalize_neo4j_uri(uri)
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def sync_files(self, files: List[FileInfo], project_root: str):
        """
        Syncs the list of files to Neo4j.
        Creates :File nodes with properties {path, hash}.
        """
        # Prepare data for batch insertion
        file_data = [{"path": f.path, "hash": f.hash} for f in files]

        with self.driver.session() as session:
            session.execute_write(self._create_files_tx, file_data, project_root)

    @staticmethod
    def _create_files_tx(tx, file_data, project_root):
        query = """
        UNWIND $files AS file
        MERGE (f:File {path: file.path})
        SET f.hash = file.hash,
            f.project_root = $project_root,
            f.last_seen = timestamp()
        """
        tx.run(query, files=file_data, project_root=project_root)
        
    def get_file_count(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n:File) RETURN count(n) as count")
            return result.single()["count"]

    def sync_definitions(self, file_path: str, definitions: List[Definition]):
        """
        Syncs definitions (classes, functions) to Neo4j.
        """
        def_data = [
            {
                "name": d.name,
                "type": d.type,
                "start_line": d.start_line,
                "end_line": d.end_line,
                "id": f"{file_path}::{d.name}"
            }
            for d in definitions
        ]

        with self.driver.session() as session:
            session.execute_write(self._create_definitions_tx, file_path, def_data)

    @staticmethod
    def _create_definitions_tx(tx, file_path, def_data):
        # 1. Clear existing definitions for this file (to handle updates)
        # Note: This is a simple strategy. For incremental, we might want to be smarter.
        query_clear = """
        MATCH (f:File {path: $file_path})-[r:DEFINES]->(d)
        DETACH DELETE d
        """
        tx.run(query_clear, file_path=file_path)

        # 2. Create new definitions
        query_create = """
        MATCH (f:File {path: $file_path})
        UNWIND $definitions AS def
        CALL {
            WITH f, def
            MERGE (d:Definition {id: def.id})
            SET d.name = def.name,
                d.type = def.type,
                d.start_line = def.start_line,
                d.end_line = def.end_line
            MERGE (f)-[:DEFINES]->(d)
            
            // Add specific labels
            FOREACH (_ IN CASE WHEN def.type = 'class' THEN [1] ELSE [] END | SET d:Class)
            FOREACH (_ IN CASE WHEN def.type = 'function' THEN [1] ELSE [] END | SET d:Function)
        } IN TRANSACTIONS OF 100 ROWS
        """
        # Note: IN TRANSACTIONS is good for large batches, but might be overkill here. 
        # Removing it for simplicity and compatibility with older Neo4j versions if needed,
        # but keeping UNWIND.
        
        query_create_simple = """
        MATCH (f:File {path: $file_path})
        UNWIND $definitions AS def
        MERGE (d:Definition {id: def.id})
        SET d.name = def.name,
            d.type = def.type,
            d.start_line = def.start_line,
            d.end_line = def.end_line
        MERGE (f)-[:DEFINES]->(d)
        
        FOREACH (_ IN CASE WHEN def.type = 'class' THEN [1] ELSE [] END | SET d:Class)
        FOREACH (_ IN CASE WHEN def.type = 'function' THEN [1] ELSE [] END | SET d:Function)
        """
        
        tx.run(query_create_simple, file_path=file_path, definitions=def_data)

    def sync_dependencies(self, file_path: str, dependencies: List[dict]):
        """
        Syncs dependencies (imports) to Neo4j.
        dependencies is a list of dicts: {'target_path': str, 'line': int}
        """
        with self.driver.session() as session:
            session.execute_write(self._create_dependencies_tx, file_path, dependencies)

    @staticmethod
    def _create_dependencies_tx(tx, file_path, dependencies):
        # 1. Clear existing imports for this file
        query_clear = """
        MATCH (f:File {path: $file_path})-[r:IMPORTS]->()
        DELETE r
        """
        tx.run(query_clear, file_path=file_path)

        # 2. Create new imports
        # We match the target file by path. If it doesn't exist (e.g. ignored file), we skip.
        query_create = """
        MATCH (source:File {path: $file_path})
        UNWIND $deps AS dep
        MATCH (target:File {path: dep.target_path})
        MERGE (source)-[r:IMPORTS]->(target)
        SET r.line = dep.line
        """
        tx.run(query_create, file_path=file_path, deps=dependencies)

    def sync_calls(self, file_path: str, calls: List[dict]):
        """
        Syncs function calls to Neo4j.
        calls is a list of dicts: {'caller_name': str, 'callee_name': str, 'target_file': str, 'line': int}
        """
        with self.driver.session() as session:
            session.execute_write(self._create_calls_tx, file_path, calls)

    @staticmethod
    def _create_calls_tx(tx, file_path, calls):
        # 1. Clear existing calls for this file
        # Note: This clears all calls originating from functions in this file
        query_clear = """
        MATCH (f:File {path: $file_path})-[:DEFINES]->(caller:Function)-[r:CALLS]->()
        DELETE r
        """
        tx.run(query_clear, file_path=file_path)

        # 2. Create new calls
        # We need to match:
        # - The caller function (defined in current file)
        # - The callee function (defined in target file, or current file if target_file is None)
        query_create = """
        MATCH (f:File {path: $file_path})-[:DEFINES]->(caller:Function {name: $caller_name})
        MATCH (target_file:File {path: $target_file})-[:DEFINES]->(callee:Function {name: $callee_name})
        MERGE (caller)-[r:CALLS]->(callee)
        SET r.line = $line
        """
        
        # Batch processing manually since the query depends on row values for matching logic
        # Actually, we can use UNWIND if we handle the target_file logic carefully
        
        query_create_batch = """
        UNWIND $calls AS call
        MATCH (f:File {path: $file_path})-[:DEFINES]->(caller:Function {name: call.caller_name})
        MATCH (target_file:File {path: call.target_file})-[:DEFINES]->(callee:Function {name: call.callee_name})
        MERGE (caller)-[r:CALLS]->(callee)
        SET r.line = call.line
        """
        
        tx.run(query_create_batch, file_path=file_path, calls=calls)

    def get_definition_context(self, file_path: str, definition_name: str, max_hops: int = 2) -> Dict[str, Any]:
        """
        Gets graph context for a definition (function/class).
        Returns related code through graph traversal:
        - Files that import this definition's file
        - Functions that call this function
        - Functions called by this function
        - Related definitions in the same file
        """
        def_id = f"{file_path}::{definition_name}"
        
        with self.driver.session() as session:
            # First, get the definition and its file
            def_result = session.run("""
                MATCH (file:File)-[:DEFINES]->(def:Definition {id: $def_id})
                RETURN def, file.path as file_path
            """, def_id=def_id)
            
            def_record = def_result.single()
            if not def_record or not def_record['def']:
                return {}
            
            file_path = def_record['file_path']
            
            # Get dependents (files that import this file)
            dependents_result = session.run("""
                MATCH (dependent:File)-[:IMPORTS]->(file:File {path: $file_path})
                RETURN collect(DISTINCT dependent.path) as dependents
            """, file_path=file_path)
            dependents = dependents_result.single()['dependents'] or []
            
            # Get dependencies (files this file imports)
            deps_result = session.run("""
                MATCH (file:File {path: $file_path})-[:IMPORTS]->(dependency:File)
                RETURN collect(DISTINCT dependency.path) as dependencies
            """, file_path=file_path)
            dependencies = deps_result.single()['dependencies'] or []
            
            # Get callers (functions that call this function) - only if def is a Function
            callers_result = session.run("""
                MATCH (caller:Function)-[:CALLS]->(def:Function {id: $def_id})
                MATCH (caller_file:File)-[:DEFINES]->(caller)
                RETURN collect(DISTINCT {name: caller.name, file: caller_file.path}) as callers
            """, def_id=def_id)
            callers = callers_result.single()['callers'] or []
            
            # Get callees (functions called by this function) - only if def is a Function
            callees_result = session.run("""
                MATCH (def:Function {id: $def_id})-[:CALLS]->(callee:Function)
                MATCH (callee_file:File)-[:DEFINES]->(callee)
                RETURN collect(DISTINCT {name: callee.name, file: callee_file.path}) as callees
            """, def_id=def_id)
            callees = callees_result.single()['callees'] or []
            
            # Get siblings (other definitions in the same file)
            siblings_result = session.run("""
                MATCH (file:File {path: $file_path})-[:DEFINES]->(sibling:Definition)
                WHERE sibling.id <> $def_id
                RETURN collect(DISTINCT {id: sibling.id, name: sibling.name, type: sibling.type}) as siblings
            """, file_path=file_path, def_id=def_id)
            siblings = siblings_result.single()['siblings'] or []
            
            return {
                'definition': {
                    'id': def_record['def']['id'],
                    'name': def_record['def']['name'],
                    'type': def_record['def']['type'],
                    'file_path': file_path,
                    'start_line': def_record['def']['start_line'],
                    'end_line': def_record['def']['end_line']
                },
                'dependents': dependents,
                'callers': callers,
                'callees': callees,
                'siblings': siblings,
                'dependencies': dependencies
            }

    def get_expanded_context(self, vector_results: List[Dict[str, Any]], max_hops: int = 2) -> Dict[str, Any]:
        """
        Takes vector search results and expands them with graph context.
        Returns a combined "Perfect Context Packet" with semantic matches + graph relationships.
        """
        expanded_results = []
        all_related_files = set()
        
        for result in vector_results:
            meta = result['metadata']
            file_path = meta['file_path']
            name = meta['name']
            
            # Get graph context for this definition
            context = self.get_definition_context(file_path, name, max_hops=max_hops)
            
            # Collect related files
            all_related_files.add(file_path)
            all_related_files.update(context.get('dependents', []))
            all_related_files.update(context.get('dependencies', []))
            for caller in context.get('callers', []):
                if caller.get('file'):
                    all_related_files.add(caller['file'])
            for callee in context.get('callees', []):
                if callee.get('file'):
                    all_related_files.add(callee['file'])
            
            expanded_results.append({
                'vector_result': result,
                'graph_context': context
            })
        
        return {
            'semantic_matches': expanded_results,
            'related_files': list(all_related_files),
            'total_files': len(all_related_files)
        }

    def generate_context_packet(self, vector_results: List[Dict[str, Any]], max_hops: int = 2) -> str:
        """
        Generates a "Perfect Context Packet" in XML format for LLMs.
        Combines semantic search results with graph relationships.
        """
        expanded = self.get_expanded_context(vector_results, max_hops=max_hops)
        
        xml_parts = ['<codebase_context>']
        xml_parts.append(f'  <query_results count="{len(expanded["semantic_matches"])}">')
        
        for item in expanded['semantic_matches']:
            result = item['vector_result']
            context = item['graph_context']
            meta = result['metadata']
            
            xml_parts.append(f'    <match score="{result["score"]:.4f}">')
            xml_parts.append(f'      <definition name="{meta["name"]}" type="{meta["type"]}"/>')
            xml_parts.append(f'      <file path="{meta["file_path"]}" line="{meta["start_line"]}"/>')
            xml_parts.append(f'      <code><![CDATA[{result["document"]}]]></code>')
            
            if context:
                if context.get('callers'):
                    xml_parts.append('      <called_by>')
                    for caller in context['callers']:
                        xml_parts.append(f'        <function name="{caller["name"]}" file="{caller["file"]}"/>')
                    xml_parts.append('      </called_by>')
                
                if context.get('callees'):
                    xml_parts.append('      <calls>')
                    for callee in context['callees']:
                        xml_parts.append(f'        <function name="{callee["name"]}" file="{callee["file"]}"/>')
                    xml_parts.append('      </calls>')
                
                if context.get('dependents'):
                    xml_parts.append('      <used_by>')
                    for dep in context['dependents']:
                        xml_parts.append(f'        <file path="{dep}"/>')
                    xml_parts.append('      </used_by>')
                
                if context.get('dependencies'):
                    xml_parts.append('      <depends_on>')
                    for dep in context['dependencies']:
                        xml_parts.append(f'        <file path="{dep}"/>')
                    xml_parts.append('      </depends_on>')
            
            xml_parts.append('    </match>')
        
        xml_parts.append('  </query_results>')
        xml_parts.append(f'  <related_files count="{expanded["total_files"]}">')
        for file_path in sorted(expanded['related_files']):
            xml_parts.append(f'    <file path="{file_path}"/>')
        xml_parts.append('  </related_files>')
        xml_parts.append('</codebase_context>')
        
        return '\n'.join(xml_parts)

    def get_graph_for_visualization(self, project_root: str, file_paths: Optional[List[str]] = None, max_nodes: int = 500) -> Dict[str, Any]:
        """
        Gets graph data in a format suitable for visualization.
        Returns nodes and edges in a format compatible with graph visualization libraries.
        
        Args:
            project_root: Root path of the project
            file_paths: Optional list of file paths to filter to (for blast radius visualization)
            max_nodes: Maximum number of nodes to return
            
        Returns:
            Dictionary with 'nodes' and 'edges' lists
        """
        with self.driver.session() as session:
            # Build the query based on whether we're filtering to specific files
            if file_paths:
                # Get nodes and relationships for specific files and their neighbors
                # First, find related files through imports
                related_files_query = """
                MATCH (target:File)
                WHERE target.path IN $file_paths AND target.project_root = $project_root
                OPTIONAL MATCH (target)-[:IMPORTS]->(imported:File)
                OPTIONAL MATCH (importer:File)-[:IMPORTS]->(target)
                WITH collect(DISTINCT target.path) + collect(DISTINCT imported.path) + collect(DISTINCT importer.path) as all_files
                UNWIND all_files as file_path
                RETURN DISTINCT file_path
                """
                related_result = session.run(related_files_query, project_root=project_root, file_paths=file_paths)
                related_file_paths = [record['file_path'] for record in related_result if record['file_path']]
                all_file_paths = list(set(file_paths + related_file_paths))[:max_nodes]
                
                query = """
                MATCH (f:File)
                WHERE f.project_root = $project_root AND f.path IN $all_file_paths
                OPTIONAL MATCH (f)-[:DEFINES]->(d:Definition)
                WITH f, collect(DISTINCT d) as definitions
                OPTIONAL MATCH (f)-[:IMPORTS]->(imported:File)
                WITH f, definitions, collect(DISTINCT imported) as imports
                OPTIONAL MATCH (imported_file:File)-[:IMPORTS]->(f)
                WITH f, definitions, imports, collect(DISTINCT imported_file) as imported_by
                OPTIONAL MATCH (f)-[:DEFINES]->(caller:Function)-[:CALLS]->(callee:Function)<-[:DEFINES]-(callee_file:File)
                WITH f, definitions, imports, imported_by, collect(DISTINCT {caller: caller, callee: callee, callee_file: callee_file}) as calls
                RETURN f, definitions, imports, imported_by, calls
                """
                result = session.run(query, project_root=project_root, all_file_paths=all_file_paths)
            else:
                # Get all files and relationships for the project
                query = """
                MATCH (f:File)
                WHERE f.project_root = $project_root
                WITH f
                LIMIT $max_nodes
                OPTIONAL MATCH (f)-[:DEFINES]->(d:Definition)
                WITH f, collect(DISTINCT d) as definitions
                OPTIONAL MATCH (f)-[:IMPORTS]->(imported:File)
                WITH f, definitions, collect(DISTINCT imported) as imports
                OPTIONAL MATCH (imported_file:File)-[:IMPORTS]->(f)
                WITH f, definitions, imports, collect(DISTINCT imported_file) as imported_by
                OPTIONAL MATCH (f)-[:DEFINES]->(caller:Function)-[:CALLS]->(callee:Function)<-[:DEFINES]-(callee_file:File)
                WITH f, definitions, imports, imported_by, collect(DISTINCT {caller: caller, callee: callee, callee_file: callee_file}) as calls
                RETURN f, definitions, imports, imported_by, calls
                """
                result = session.run(query, project_root=project_root, max_nodes=max_nodes)
            
            nodes = []
            edges = []
            node_ids = set()
            
            for record in result:
                file_node = record['f']
                if not file_node:
                    continue
                    
                file_path = file_node['path']
                file_id = f"file:{file_path}"
                
                # Add file node
                if file_id not in node_ids:
                    nodes.append({
                        'id': file_id,
                        'label': file_path.split('/')[-1],
                        'type': 'file',
                        'path': file_path,
                        'properties': {
                            'path': file_path,
                            'hash': file_node.get('hash', ''),
                        }
                    })
                    node_ids.add(file_id)
                
                # Add definition nodes and edges
                definitions = record['definitions'] or []
                for def_node in definitions:
                    def_id = f"def:{def_node['id']}"
                    if def_id not in node_ids:
                        nodes.append({
                            'id': def_id,
                            'label': def_node['name'],
                            'type': def_node['type'],
                            'properties': {
                                'name': def_node['name'],
                                'file_path': file_path,
                                'start_line': def_node.get('start_line'),
                                'end_line': def_node.get('end_line'),
                            }
                        })
                        node_ids.add(def_id)
                    
                    # Add DEFINES edge
                    edges.append({
                        'id': f"{file_id}->{def_id}",
                        'source': file_id,
                        'target': def_id,
                        'type': 'DEFINES',
                        'label': 'defines'
                    })
                
                # Add IMPORT edges
                imports = record['imports'] or []
                for imported_file in imports:
                    imported_path = imported_file['path']
                    imported_id = f"file:{imported_path}"
                    
                    # Add imported file node if not already added
                    if imported_id not in node_ids:
                        nodes.append({
                            'id': imported_id,
                            'label': imported_path.split('/')[-1],
                            'type': 'file',
                            'path': imported_path,
                            'properties': {
                                'path': imported_path,
                            }
                        })
                        node_ids.add(imported_id)
                    
                    edges.append({
                        'id': f"{file_id}->{imported_id}",
                        'source': file_id,
                        'target': imported_id,
                        'type': 'IMPORTS',
                        'label': 'imports'
                    })
                
                # Add imported_by edges (reverse direction)
                imported_by = record['imported_by'] or []
                for importer_file in imported_by:
                    importer_path = importer_file['path']
                    importer_id = f"file:{importer_path}"
                    
                    if importer_id not in node_ids:
                        nodes.append({
                            'id': importer_id,
                            'label': importer_path.split('/')[-1],
                            'type': 'file',
                            'path': importer_path,
                            'properties': {
                                'path': importer_path,
                            }
                        })
                        node_ids.add(importer_id)
                    
                    edges.append({
                        'id': f"{importer_id}->{file_id}",
                        'source': importer_id,
                        'target': file_id,
                        'type': 'IMPORTS',
                        'label': 'imports'
                    })
                
                # Add CALLS edges
                calls = record['calls'] or []
                for call_data in calls:
                    caller = call_data.get('caller')
                    callee = call_data.get('callee')
                    callee_file = call_data.get('callee_file')
                    
                    if caller and callee and callee_file:
                        caller_id = f"def:{caller['id']}"
                        callee_id = f"def:{callee['id']}"
                        
                        # Ensure callee is in nodes
                        if callee_id not in node_ids:
                            callee_file_path = callee_file['path']
                            nodes.append({
                                'id': callee_id,
                                'label': callee['name'],
                                'type': 'function',
                                'properties': {
                                    'name': callee['name'],
                                    'file_path': callee_file_path,
                                }
                            })
                            node_ids.add(callee_id)
                            
                            # Add callee file if needed
                            callee_file_id = f"file:{callee_file_path}"
                            if callee_file_id not in node_ids:
                                nodes.append({
                                    'id': callee_file_id,
                                    'label': callee_file_path.split('/')[-1],
                                    'type': 'file',
                                    'path': callee_file_path,
                                    'properties': {
                                        'path': callee_file_path,
                                    }
                                })
                                node_ids.add(callee_file_id)
                            
                            # Add DEFINES edge for callee
                            edges.append({
                                'id': f"{callee_file_id}->{callee_id}",
                                'source': callee_file_id,
                                'target': callee_id,
                                'type': 'DEFINES',
                                'label': 'defines'
                            })
                        
                        edges.append({
                            'id': f"{caller_id}->{callee_id}",
                            'source': caller_id,
                            'target': callee_id,
                            'type': 'CALLS',
                            'label': 'calls'
                        })
            
            return {
                'nodes': nodes,
                'edges': edges
            }
            
    def get_node_source(self, node_id: str, project_root: str = None) -> Optional[str]:
        """
        Retrieves the source code for a given node (File or Definition).
        """
        with self.driver.session() as session:
            # Check if it's a definition
            if node_id.startswith("def:"):
                query = """
                MATCH (d:Definition {id: $id})
                RETURN d.code as code
                """
                result = session.run(query, id=node_id[4:]) # Strip 'def:' prefix
                record = result.single()
                if record:
                    return record['code']
            
            # Check if it's a file
            elif node_id.startswith("file:"):
                # For files, we might need to read from disk if we don't store full content in DB
                # But we have the path
                path = node_id[5:] # Strip 'file:' prefix
                
                # Handle relative paths if project_root is provided
                if project_root and not os.path.isabs(path):
                    path = os.path.join(project_root, path)
                    
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            return f.read()
                    except Exception:
                        return None
            
            return None

    def get_node_details(self, node_id: str, project_root: str) -> Dict[str, Any]:
        """
        Gets comprehensive details for a node including source code, related nodes, and metadata.
        Returns data suitable for a detailed trace view.
        """
        source_code = self.get_node_source(node_id, project_root)
        
        # Get related nodes for graph visualization
        related_nodes_data = self.get_graph_for_visualization(
            project_root, 
            file_paths=None,  # We'll filter to related nodes after
            max_nodes=100
        )
        
        # Extract node info and find related nodes
        node_info = None
        related_nodes = []
        related_edges = []
        
        with self.driver.session() as session:
            if node_id.startswith("def:"):
                # Get definition details
                def_id = node_id[4:]  # Strip 'def:' prefix
                query = """
                MATCH (file:File)-[:DEFINES]->(def:Definition {id: $def_id})
                RETURN def, file.path as file_path
                """
                result = session.run(query, def_id=def_id)
                record = result.single()
                
                if record:
                    def_node = record['def']
                    file_path = record['file_path']
                    
                    node_info = {
                        'id': node_id,
                        'label': def_node['name'],
                        'type': def_node['type'],
                        'path': file_path,
                        'properties': {
                            'name': def_node['name'],
                            'file_path': file_path,
                            'start_line': def_node.get('start_line'),
                            'end_line': def_node.get('end_line'),
                        }
                    }
                    
                    # Get related nodes through relationships
                    # Callers
                    callers_query = """
                    MATCH (caller:Function)-[:CALLS]->(def:Function {id: $def_id})
                    MATCH (caller_file:File)-[:DEFINES]->(caller)
                    RETURN caller, caller_file.path as file_path
                    """
                    for record in session.run(callers_query, def_id=def_id):
                        caller = record['caller']
                        related_nodes.append({
                            'id': f"def:{caller['id']}",
                            'label': caller['name'],
                            'type': 'function',
                            'path': record['file_path'],
                            'properties': {
                                'name': caller['name'],
                                'file_path': record['file_path'],
                            }
                        })
                        related_edges.append({
                            'id': f"def:{caller['id']}->{node_id}",
                            'source': f"def:{caller['id']}",
                            'target': node_id,
                            'type': 'CALLS',
                            'label': 'calls'
                        })
                    
                    # Callees
                    callees_query = """
                    MATCH (def:Function {id: $def_id})-[:CALLS]->(callee:Function)
                    MATCH (callee_file:File)-[:DEFINES]->(callee)
                    RETURN callee, callee_file.path as file_path
                    """
                    for record in session.run(callees_query, def_id=def_id):
                        callee = record['callee']
                        related_nodes.append({
                            'id': f"def:{callee['id']}",
                            'label': callee['name'],
                            'type': 'function',
                            'path': record['file_path'],
                            'properties': {
                                'name': callee['name'],
                                'file_path': record['file_path'],
                            }
                        })
                        related_edges.append({
                            'id': f"{node_id}->def:{callee['id']}",
                            'source': node_id,
                            'target': f"def:{callee['id']}",
                            'type': 'CALLS',
                            'label': 'calls'
                        })
                    
                    # File that defines it
                    related_nodes.append({
                        'id': f"file:{file_path}",
                        'label': file_path.split('/')[-1],
                        'type': 'file',
                        'path': file_path,
                        'properties': {'path': file_path}
                    })
                    related_edges.append({
                        'id': f"file:{file_path}->{node_id}",
                        'source': f"file:{file_path}",
                        'target': node_id,
                        'type': 'DEFINES',
                        'label': 'defines'
                    })
                    
            elif node_id.startswith("file:"):
                # Get file details
                file_path = node_id[5:]  # Strip 'file:' prefix
                query = """
                MATCH (file:File {path: $file_path})
                RETURN file
                """
                result = session.run(query, file_path=file_path)
                record = result.single()
                
                if record:
                    file_node = record['file']
                    node_info = {
                        'id': node_id,
                        'label': file_path.split('/')[-1],
                        'type': 'file',
                        'path': file_path,
                        'properties': {
                            'path': file_path,
                            'hash': file_node.get('hash', ''),
                        }
                    }
                    
                    # Get definitions in this file
                    defs_query = """
                    MATCH (file:File {path: $file_path})-[:DEFINES]->(def:Definition)
                    RETURN def
                    """
                    for record in session.run(defs_query, file_path=file_path):
                        def_node = record['def']
                        related_nodes.append({
                            'id': f"def:{def_node['id']}",
                            'label': def_node['name'],
                            'type': def_node['type'],
                            'path': file_path,
                            'properties': {
                                'name': def_node['name'],
                                'file_path': file_path,
                                'start_line': def_node.get('start_line'),
                                'end_line': def_node.get('end_line'),
                            }
                        })
                        related_edges.append({
                            'id': f"{node_id}->def:{def_node['id']}",
                            'source': node_id,
                            'target': f"def:{def_node['id']}",
                            'type': 'DEFINES',
                            'label': 'defines'
                        })
                    
                    # Get imports
                    imports_query = """
                    MATCH (file:File {path: $file_path})-[:IMPORTS]->(imported:File)
                    RETURN imported.path as path
                    """
                    for record in session.run(imports_query, file_path=file_path):
                        imported_path = record['path']
                        related_nodes.append({
                            'id': f"file:{imported_path}",
                            'label': imported_path.split('/')[-1],
                            'type': 'file',
                            'path': imported_path,
                            'properties': {'path': imported_path}
                        })
                        related_edges.append({
                            'id': f"{node_id}->file:{imported_path}",
                            'source': node_id,
                            'target': f"file:{imported_path}",
                            'type': 'IMPORTS',
                            'label': 'imports'
                        })
                    
                    # Get files that import this file
                    imported_by_query = """
                    MATCH (importer:File)-[:IMPORTS]->(file:File {path: $file_path})
                    RETURN importer.path as path
                    """
                    for record in session.run(imported_by_query, file_path=file_path):
                        importer_path = record['path']
                        related_nodes.append({
                            'id': f"file:{importer_path}",
                            'label': importer_path.split('/')[-1],
                            'type': 'file',
                            'path': importer_path,
                            'properties': {'path': importer_path}
                        })
                        related_edges.append({
                            'id': f"file:{importer_path}->{node_id}",
                            'source': f"file:{importer_path}",
                            'target': node_id,
                            'type': 'IMPORTS',
                            'label': 'imports'
                        })
        
        # Deduplicate related nodes
        seen_ids = {node_info['id']} if node_info else set()
        unique_related_nodes = []
        for node in related_nodes:
            if node['id'] not in seen_ids:
                unique_related_nodes.append(node)
                seen_ids.add(node['id'])
        
        return {
            'node': node_info,
            'source_code': source_code,
            'related_nodes': unique_related_nodes,
            'related_edges': related_edges,
        }

    def find_nodes_by_path_fuzzy(self, path_fragment: str, project_root: str) -> List[Dict[str, Any]]:
        """
        Finds API endpoints or functions that might match a path fragment.
        """
        with self.driver.session() as session:
            # Search for ApiEndpoints matching the path
            query = """
            MATCH (api:ApiEndpoint)
            WHERE api.path CONTAINS $fragment
            RETURN api
            LIMIT 5
            """
            result = session.run(query, fragment=path_fragment)
            matches = []
            for record in result:
                node = record['api']
                matches.append({
                    'id': f"api:{node['id']}",
                    'label': f"{node['method']} {node['path']}",
                    'type': 'api_endpoint',
                    'score': 1.0 # Placeholder score
                })
            return matches

    def create_deep_trace_relationship(self, source_id: str, target_id: str, rel_type: str, props: Dict[str, Any] = None):
        """
        Creates a relationship between two nodes based on Deep Trace analysis.
        """
        with self.driver.session() as session:
            # Determine node labels/types based on ID prefix
            source_label = "Definition" if source_id.startswith("def:") else "File"
            target_label = "ApiEndpoint" if target_id.startswith("api:") else "Definition" # Simplified
            
            # Strip prefixes
            s_id = source_id.split(':', 1)[1]
            t_id = target_id.split(':', 1)[1]
            
            query = f"""
            MATCH (s:{source_label} {{id: $s_id}})
            MATCH (t:{target_label} {{id: $t_id}})
            MERGE (s)-[r:{rel_type}]->(t)
            SET r += $props
            RETURN r
            """
            session.run(query, s_id=s_id, t_id=t_id, props=props or {})
