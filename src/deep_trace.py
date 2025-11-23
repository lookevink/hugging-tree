import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from .graph import GraphDB

class DeepTraceService:
    def __init__(self, graph_db: GraphDB):
        self.graph = graph_db
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not set. Deep Trace will not work.")
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_node(self, node_id: str, project_root: str) -> Dict[str, Any]:
        """
        Analyzes a node to find implicit relationships.
        """
        # 1. Get source code
        source_code = self.graph.get_node_source(node_id, project_root)
        if not source_code:
            return {"error": "Could not retrieve source code for node."}

        # 2. Prompt LLM
        prompt = f"""
        You are a senior code analyst. Your task is to identify implicit external calls in the following code snippet.
        Look for:
        - HTTP API calls (fetch, axios, requests, etc.)
        - Event bus publications (producer.send, emit, etc.)
        - Database queries that might imply a dependency
        
        Return a JSON object with a list of 'detected_calls'. Each item should have:
        - 'type': 'api_call' or 'event_publish'
        - 'method': HTTP method (GET, POST, etc.) or Event type
        - 'target': The URL path (e.g., '/api/v1/users') or Topic name
        - 'line_number': Approximate line number
        - 'confidence': 0.0 to 1.0
        - 'evidence': The code line that triggered this detection
        
        Code Snippet:
        ```
        {source_code}
        ```
        
        JSON Response:
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            detected_calls = data.get("detected_calls", [])
            
            # 3. Match against graph
            results = []
            for call in detected_calls:
                matches = []
                if call['type'] == 'api_call':
                    # Fuzzy search for endpoints
                    matches = self.graph.find_nodes_by_path_fuzzy(call['target'], project_root)
                
                results.append({
                    "call": call,
                    "proposed_matches": matches
                })
                
            return {"results": results}
            
        except Exception as e:
            return {"error": str(e)}

    def apply_relationship(self, source_id: str, target_id: str, rel_type: str):
        """
        Applies a confirmed relationship to the graph.
        """
        self.graph.create_deep_trace_relationship(source_id, target_id, rel_type, {"source": "deep_trace"})
