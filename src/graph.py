import os
from neo4j import GraphDatabase
from typing import List
from .scanner import FileInfo

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
