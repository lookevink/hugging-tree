import os
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from .graph import GraphDB
from .embeddings import EmbeddingService

class PlanGenerator:
    """
    Generates executable, step-by-step plans in XML format optimized for AI coding tools.
    Combines semantic search, graph traversal, and LLM planning.
    """
    
    def __init__(self, persistence_path: str = "./.tree_roots", model_name: str = None, prompt_template: str = None):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Required for planning.")
        genai.configure(api_key=self.api_key)
        
        # Use provided model, or environment variable, or default
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
            
        self.embeddings = EmbeddingService(persistence_path=persistence_path)
        self.graph = GraphDB()
        self.model = genai.GenerativeModel(self.model_name)
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template(prompt_template)

    def _load_prompt_template(self, template_path: Optional[str]) -> str:
        """Loads the prompt template from file or returns default."""
        if template_path and os.path.exists(template_path):
            try:
                with open(template_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Failed to load prompt template from {template_path}: {e}")
        
        # Default XML Plan Prompt
        return """You are a senior software engineer creating a detailed execution plan for AI coding tools.

TASK:
{task}

CODEBASE CONTEXT:
{xml_context}

STATISTICS:
- Found {semantic_matches_count} semantically relevant code definitions
- Identified {related_files_count} related files through graph traversal

Generate a comprehensive execution plan in XML format. The plan should be:
1. Highly detailed with specific code references
2. Ordered by dependencies (prerequisites first)
3. Include validation criteria for each step
4. Include rollback instructions
5. Optimized for AI coding assistants like Cursor and Claude

Follow this XML structure exactly:

<execution_plan>
  <task>
    <title>[Task Title]</title>
    <description>[Task Description]</description>
    <estimated_effort>[low|medium|high]</estimated_effort>
  </task>
  
  <context>
    <relevant_files>
      <file path="[path]" reason="[reason]"/>
    </relevant_files>
  </context>
  
  <phases>
    <phase id="1" name="[Phase Name]">
      <step id="1.1" order="1">
        <title>[Step Title]</title>
        <description>[Step Description]</description>
        <files>
          <create path="[path]"/>
          <modify path="[path]" action="[action]"/>
        </files>
        <code_references>
          <reference file="[path]" function="[name]"/>
        </code_references>
        <instructions>
          <instruction>[Detailed instruction]</instruction>
        </instructions>
        <validation>
          <check>[Validation check]</check>
        </validation>
      </step>
    </phase>
  </phases>
  
  <impact_analysis>
    <affected_files>
      <file path="[path]" impact="[direct|indirect]" reason="[reason]"/>
    </affected_files>
  </impact_analysis>
  
  <rollback>
    <step>[Rollback instruction]</step>
  </rollback>
</execution_plan>

Output ONLY valid XML. Do not include markdown formatting (```xml).
"""

    def generate_plan(self, task_description: str, n_results: int = 10) -> str:
        """
        Generates an execution plan for the given task.
        
        Args:
            task_description: Natural language description of the task
            n_results: Number of semantic matches to consider
            
        Returns:
            XML string containing the execution plan
        """
        # 1. Get semantic search results
        vector_results = self.embeddings.query(task_description, n_results=n_results)
        
        # 2. Get expanded graph context (for stats and template variables)
        expanded = self.graph.get_expanded_context(vector_results)
        
        # 3. Generate XML context packet (primary input for LLM)
        xml_context = self.graph.generate_context_packet(vector_results)
        
        # 4. Build prompt
        prompt = self.prompt_template.format(
            task=task_description,
            xml_context=xml_context,
            expanded_context=expanded, # Available for custom templates that might use it
            semantic_matches_count=len(expanded['semantic_matches']),
            related_files_count=expanded['total_files']
        )
        
        # 5. Generate Plan
        return self._generate_xml(prompt)

    def _generate_xml(self, prompt: str) -> str:
        """Generates XML using Gemini."""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if text.startswith("```xml"):
                text = text[6:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate plan: {e}")

    def close(self):
        """Closes database connections."""
        self.graph.close()
