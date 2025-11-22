import os
import google.generativeai as genai
from typing import Dict, Any, List
from .graph import GraphDB
from .embeddings import EmbeddingService


class ContextAnalyzer:
    """
    Analyzes codebase context and generates actionable instructions.
    Combines semantic search, graph traversal, and LLM analysis.
    """
    
    def __init__(self, persistence_path: str = "./.tree_roots"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Required for analysis.")
        genai.configure(api_key=self.api_key)
        
        self.embeddings = EmbeddingService(persistence_path=persistence_path)
        self.graph = GraphDB()
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
    
    def analyze_task(self, task_description: str, n_results: int = 10) -> Dict[str, Any]:
        """
        Analyzes a task description and generates actionable context and instructions.
        
        Args:
            task_description: Natural language description of the task/change
            n_results: Number of semantic matches to consider
            
        Returns:
            Dictionary with analysis results including:
            - files_to_modify: List of files that need changes
            - blast_radius: Files that will be affected
            - actions: Step-by-step actions needed
            - dependencies: Dependencies to consider
            - risks: Potential risks or breaking changes
        """
        # 1. Get semantic search results
        vector_results = self.embeddings.query(task_description, n_results=n_results)
        
        # 2. Get expanded graph context
        expanded = self.graph.get_expanded_context(vector_results)
        
        # 3. Generate XML context packet
        xml_context = self.graph.generate_context_packet(vector_results)
        
        # 4. Generate analysis prompt
        analysis_prompt = self._build_analysis_prompt(task_description, expanded, xml_context)
        
        # 5. Get LLM analysis
        analysis = self._generate_analysis(analysis_prompt)
        
        # 6. Extract structured information
        structured_analysis = self._extract_structured_info(analysis, expanded)
        
        return {
            'task': task_description,
            'semantic_matches': len(expanded['semantic_matches']),
            'related_files': expanded['related_files'],
            'analysis': analysis,
            'structured': structured_analysis
        }
    
    def _build_analysis_prompt(self, task: str, expanded_context: Dict[str, Any], xml_context: str) -> str:
        """Builds a prompt for the LLM to analyze the task."""
        return f"""You are a senior software engineer analyzing a codebase. Based on the user's request below, provide actionable insights about what needs to be modified, the blast radius, and step-by-step actions.

USER REQUEST:
{task}

CODEBASE CONTEXT:
{xml_context}

Based on the semantic search results and graph relationships above, analyze the user's request and provide a comprehensive analysis in the following format:

## Files to Modify
[List the specific files that need to be changed, ordered by priority]

## Blast Radius
[Identify all files that will be affected by these changes, including:
- Direct dependencies (files that import the modified files)
- Indirect dependencies (files that depend on the dependents)
- Callers (functions that call modified functions)
- Callees (functions called by modified code)]

## Step-by-Step Actions
[Provide a numbered list of specific actions needed to complete this task]

## Dependencies to Consider
[List any external dependencies, imports, or relationships that need attention]

## Risks & Breaking Changes
[Identify potential breaking changes, test files that need updates, and areas of risk]

## Additional Context
[Any other relevant insights about the codebase structure or relationships]

Be specific and actionable. Reference actual file paths and function names from the context provided.
"""
    
    def _generate_analysis(self, prompt: str) -> str:
        """Generates analysis using Gemini."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise ValueError(f"Failed to generate analysis: {e}")
    
    def _extract_structured_info(self, analysis: str, expanded_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts structured information from the analysis text."""
        # Parse the markdown-style analysis to extract structured data
        files_to_modify = []
        blast_radius = []
        actions = []
        dependencies = []
        risks = []
        
        current_section = None
        for line in analysis.split('\n'):
            line = line.strip()
            
            if line.startswith('## Files to Modify'):
                current_section = 'files'
            elif line.startswith('## Blast Radius'):
                current_section = 'blast_radius'
            elif line.startswith('## Step-by-Step Actions'):
                current_section = 'actions'
            elif line.startswith('## Dependencies'):
                current_section = 'dependencies'
            elif line.startswith('## Risks'):
                current_section = 'risks'
            elif line.startswith('##'):
                current_section = None
            elif line and current_section:
                # Extract file paths or action items
                if line.startswith('- ') or line.startswith('* '):
                    content = line[2:].strip()
                elif line and line[0].isdigit() and '. ' in line:
                    content = line.split('. ', 1)[1].strip()
                else:
                    content = line
                
                if current_section == 'files' and content:
                    files_to_modify.append(content)
                elif current_section == 'blast_radius' and content:
                    blast_radius.append(content)
                elif current_section == 'actions' and content:
                    actions.append(content)
                elif current_section == 'dependencies' and content:
                    dependencies.append(content)
                elif current_section == 'risks' and content:
                    risks.append(content)
        
        return {
            'files_to_modify': files_to_modify,
            'blast_radius': blast_radius,
            'actions': actions,
            'dependencies': dependencies,
            'risks': risks
        }
    
    def close(self):
        """Closes database connections."""
        self.graph.close()

