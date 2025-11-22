from tree_sitter_languages import get_language, get_parser
from dataclasses import dataclass
from typing import List, Optional
import os

@dataclass
class Definition:
    name: str
    type: str  # 'class' or 'function'
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    code: Optional[str] = None

class CodeParser:
    def __init__(self):
        self.parsers = {
            'python': get_parser('python'),
            'typescript': get_parser('typescript'),
            'javascript': get_parser('javascript'),
        }
        self.languages = {
            'python': get_language('python'),
            'typescript': get_language('typescript'),
            'javascript': get_language('javascript'),
        }
        
        # Queries for extracting definitions
        self.queries = {
            'python': """
                (class_definition
                    name: (identifier) @name
                    body: (block) @body
                ) @class
                (function_definition
                    name: (identifier) @name
                    body: (block) @body
                ) @function
            """,
            'typescript': """
                (class_declaration
                    name: (type_identifier) @name
                    body: (class_body) @body
                ) @class
                (function_declaration
                    name: (identifier) @name
                    body: (statement_block) @body
                ) @function
                (method_definition
                    name: (property_identifier) @name
                    body: (statement_block) @body
                ) @function
                (arrow_function
                    body: (statement_block) @body
                ) @function
            """,
             'javascript': """
                (class_declaration
                    name: (identifier) @name
                    body: (class_body) @body
                ) @class
                (function_declaration
                    name: (identifier) @name
                    body: (statement_block) @body
                ) @function
            """
        }

    def _get_language_for_file(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1]
        if ext == '.py':
            return 'python'
        elif ext in ['.ts', '.tsx']:
            return 'typescript'
        elif ext in ['.js', '.jsx']:
            return 'javascript'
        return None

    def parse_file(self, filename: str, source_code: str) -> List[Definition]:
        lang_name = self._get_language_for_file(filename)
        if not lang_name:
            return []

        parser = self.parsers.get(lang_name)
        if not parser:
            return []

        tree = parser.parse(bytes(source_code, "utf8"))
        language = self.languages.get(lang_name)
        query = language.query(self.queries.get(lang_name))
        
        definitions = []
        captures = query.captures(tree.root_node)
        
        # Process captures
        # Note: captures is a list of (node, capture_name)
        # We need to group them by the parent node to form complete definitions
        
        # Simplified approach: Iterate over captures and create definitions
        # This might need refinement for nested structures, but good for v1
        
        for node, name in captures:
            if name in ['class', 'function']:
                def_type = name
                
                # Find the name node
                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                    
                def_name = source_code[name_node.start_byte:name_node.end_byte]
                
                definitions.append(Definition(
                    name=def_name,
                    type=def_type,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    code=source_code[node.start_byte:node.end_byte]
                ))
                
        return definitions
