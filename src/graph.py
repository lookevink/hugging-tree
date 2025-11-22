import os
from neo4j import GraphDatabase
from typing import List
from .scanner import FileInfo
from .parser import Definition

class GraphDB:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
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
        DELETE r, d
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

