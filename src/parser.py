from tree_sitter_languages import get_language, get_parser
from dataclasses import dataclass
from typing import List, Optional, Tuple
import os

@dataclass
class Definition:
    name: str
    type: str  # 'class' or 'function'
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    code: Optional[str] = None

@dataclass
class Import:
    module: str
    names: List[str]  # imported names, e.g. ['foo', 'bar'] from 'from x import foo, bar'
    start_line: int
    end_line: int
    code: str

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
                (import_statement
                    name: (dotted_name) @module
                ) @import
                (import_from_statement
                    module_name: (dotted_name) @module
                ) @import_from
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
                (import_statement
                    source: (string) @module
                ) @import
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
                (import_statement
                    source: (string) @module
                ) @import
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

    def parse_file(self, filename: str, source_code: str) -> Tuple[List[Definition], List[Import]]:
        lang_name = self._get_language_for_file(filename)
        if not lang_name:
            return [], []

        parser = self.parsers.get(lang_name)
        if not parser:
            return [], []

        tree = parser.parse(bytes(source_code, "utf8"))
        language = self.languages.get(lang_name)
        query = language.query(self.queries.get(lang_name))
        
        definitions = []
        imports = []
        captures = query.captures(tree.root_node)
        
        for node, name in captures:
            if name in ['class', 'function']:
                def_type = name
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
            elif name in ['import', 'import_from']:
                # Basic import extraction
                # For TS/JS: source is the string literal
                # For Python: module_name is the dotted name
                
                module_name = ""
                if lang_name in ['typescript', 'javascript']:
                    source_node = node.child_by_field_name('source')
                    if source_node:
                        # Strip quotes
                        module_name = source_code[source_node.start_byte+1:source_node.end_byte-1]
                elif lang_name == 'python':
                    if name == 'import_from':
                        module_node = node.child_by_field_name('module_name')
                        if module_node:
                            module_name = source_code[module_node.start_byte:module_node.end_byte]
                    else:
                        # import x.y
                        # This is harder because it can be multiple names. 
                        # Simplified: just grab the first one for now
                        pass

                if module_name:
                    imports.append(Import(
                        module=module_name,
                        names=[], # TODO: Extract imported names
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        code=source_code[node.start_byte:node.end_byte]
                    ))
                
        return definitions, imports
