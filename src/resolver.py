import os
from typing import Optional

class ImportResolver:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def resolve(self, current_file_path: str, import_path: str) -> Optional[str]:
        """
        Resolves an import path to a file path relative to the project root.
        
        Args:
            current_file_path: The path of the file containing the import (relative to project root).
            import_path: The string found in the import statement (e.g. './utils', 'react').
            
        Returns:
            The resolved file path relative to project root, or None if not found/external.
        """
        
        # 1. Ignore external imports (node_modules, pip packages)
        if not import_path.startswith('.'):
            # TODO: Handle alias paths (tsconfig paths) later
            return None

        # 2. Construct absolute path on disk
        # current_file_path is relative to project_root, e.g. "src/main.ts"
        # We need the directory of the current file
        current_dir = os.path.dirname(os.path.join(self.project_root, current_file_path))
        
        # Resolve the import path relative to the current directory
        # e.g. current_dir=/app/src, import_path=./utils -> /app/src/utils
        target_abs_path = os.path.normpath(os.path.join(current_dir, import_path))
        
        # 3. Try extensions
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.py']
        
        # Case A: Exact match (rare for imports, but possible)
        if os.path.isfile(target_abs_path):
             return os.path.relpath(target_abs_path, self.project_root)

        # Case B: Try adding extensions
        for ext in extensions:
            candidate = target_abs_path + ext
            if os.path.isfile(candidate):
                return os.path.relpath(candidate, self.project_root)
                
        # Case C: Directory index (index.ts, index.js)
        if os.path.isdir(target_abs_path):
            for ext in extensions:
                candidate = os.path.join(target_abs_path, f"index{ext}")
                if os.path.isfile(candidate):
                    return os.path.relpath(candidate, self.project_root)

        return None
