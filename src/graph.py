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
