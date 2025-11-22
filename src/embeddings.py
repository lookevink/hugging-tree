import os
import chromadb
import google.generativeai as genai
from typing import List, Dict, Any
from .parser import Definition

class EmbeddingService:
    def __init__(self, persistence_path: str = "./.tree_roots"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY not set. Embeddings will fail.")
        else:
            genai.configure(api_key=self.api_key)

        self.client = chromadb.PersistentClient(path=persistence_path)
        self._ensure_collection()

    def _ensure_collection(self):
        """
        Ensures the collection exists. Will be created on first use.
        """
        try:
            self.collection = self.client.get_collection(name="code_definitions")
        except Exception:
            # Collection doesn't exist, will be created on first upsert
            self.collection = None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding for the given text using Gemini.
        """
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")
            
        # Model: gemini-embedding-001
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
            title="Code Snippet"
        )
        return result['embedding']

    def store_definitions(self, file_path: str, definitions: List[Definition]):
        """
        Stores definitions in ChromaDB.
        """
        if not definitions:
            return

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        # Track counts to handle duplicates (e.g. overloads, constructors in different classes)
        # Since we don't have class context in Definition yet (TODO), we'll just use an incrementing index if needed.
        # Actually, we should probably fix the parser to include class context, but for now:
        seen_ids = {}

        for d in definitions:
            # Create a unique ID
            base_id = f"{file_path}::{d.name}"
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                def_id = f"{base_id}::{seen_ids[base_id]}"
            else:
                seen_ids[base_id] = 0
                def_id = base_id
            
            # Prepare content for embedding
            # We include the name, type, and code to give context
            content = f"{d.type} {d.name}\n{d.code}"
            
            try:
                embedding = self.generate_embedding(content)
                
                ids.append(def_id)
                embeddings.append(embedding)
                documents.append(content)
                metadatas.append({
                    "file_path": file_path,
                    "name": d.name,
                    "type": d.type,
                    "start_line": d.start_line,
                    "end_line": d.end_line
                })
            except Exception as e:
                print(f"Failed to generate embedding for {def_id}: {e}")

        if ids:
            # Ensure collection exists
            if self.collection is None:
                self.collection = self.client.get_or_create_collection(name="code_definitions")
            
            try:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                error_msg = str(e)
                if "dimension" in error_msg.lower() or "expecting" in error_msg.lower():
                    # Dimension mismatch - recreate collection and retry
                    if embeddings:
                        embedding_dimension = len(embeddings[0])
                        print(f"Detected embedding dimension mismatch. Recreating collection (new dimension: {embedding_dimension})...")
                        try:
                            self.client.delete_collection(name="code_definitions")
                        except Exception:
                            pass
                        self.collection = self.client.get_or_create_collection(name="code_definitions")
                        # Retry upsert
                        self.collection.upsert(
                            ids=ids,
                            embeddings=embeddings,
                            documents=documents,
                            metadatas=metadatas
                        )
                else:
                    raise

    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the vector store for relevant definitions.
        """
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        # Embed the query
        query_embedding = genai.embed_content(
            model="models/gemini-embedding-001",
            content=query_text,
            task_type="retrieval_query"
        )['embedding']

        # Ensure collection exists
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(name="code_definitions")

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        except Exception as e:
            error_msg = str(e)
            if "dimension" in error_msg.lower() or "expecting" in error_msg.lower():
                # Dimension mismatch - collection needs to be recreated
                embedding_dimension = len(query_embedding)
                print(f"Detected embedding dimension mismatch. Collection needs to be recreated. Please run 'scan' command first to rebuild embeddings.")
                raise ValueError(f"Embedding dimension mismatch. Collection expects different dimension than model produces ({embedding_dimension}). Please delete .tree_roots directory and re-scan.")
            raise
        
        # Format results
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "score": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i],
                    "document": results['documents'][0][i]
                })
                
        return formatted_results
