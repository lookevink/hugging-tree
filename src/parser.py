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

@dataclass
class Call:
    name: str
    start_line: int
    end_line: int
    context: str # The function name where this call happens, if any

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
                (call
                    function: (identifier) @call_name
                ) @call
                (call
                    function: (attribute
                        attribute: (identifier) @call_name
                    )
                ) @call_method
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
                (call_expression
                    function: (identifier) @call_name
                ) @call
                (call_expression
                    function: (member_expression
                        property: (property_identifier) @call_name
                    )
                ) @call_method
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
                (call_expression
                    function: (identifier) @call_name
                ) @call
                (call_expression
                    function: (member_expression
                        property: (property_identifier) @call_name
                    )
                ) @call_method
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

    def parse_file(self, filename: str, source_code: str) -> Tuple[List[Definition], List[Import], List[Call]]:
        lang_name = self._get_language_for_file(filename)
        if not lang_name:
            return [], [], []

        parser = self.parsers.get(lang_name)
        if not parser:
            return [], [], []

        tree = parser.parse(bytes(source_code, "utf8"))
        language = self.languages.get(lang_name)
        query = language.query(self.queries.get(lang_name))
        
        definitions = []
        imports = []
        calls = []
        captures = query.captures(tree.root_node)
        
        # Helper to find parent function context
        def get_context(node):
            curr = node
            while curr:
                if curr.type in ['function_definition', 'function_declaration', 'method_definition', 'arrow_function']:
                    # Try to find name
                    name_node = curr.child_by_field_name('name')
                    if name_node:
                        return source_code[name_node.start_byte:name_node.end_byte]
                    # If arrow function assigned to variable, could try to find variable name, but skipping for now
                curr = curr.parent
            return None

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
                module_name = ""
                if lang_name in ['typescript', 'javascript']:
                    source_node = node.child_by_field_name('source')
                    if source_node:
                        module_name = source_code[source_node.start_byte+1:source_node.end_byte-1]
                elif lang_name == 'python':
                    if name == 'import_from':
                        module_node = node.child_by_field_name('module_name')
                        if module_node:
                            module_name = source_code[module_node.start_byte:module_node.end_byte]
                    else:
                        pass

                if module_name:
                    imports.append(Import(
                        module=module_name,
                        names=[], 
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        code=source_code[node.start_byte:node.end_byte]
                    ))
            elif name == 'call_name':
                call_name = source_code[node.start_byte:node.end_byte]
                context = get_context(node)
                calls.append(Call(
                    name=call_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    context=context
                ))
                
        return definitions, imports, calls
