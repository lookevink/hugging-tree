import subprocess
import os
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class FileInfo:
    path: str
    hash: str

def scan_repo(repo_path: str) -> List[FileInfo]:
    """
    Scans the git repository at the given path and returns a list of files with their git hashes.
    Uses `git ls-files --stage` to get the inventory.
    """
    if not os.path.exists(repo_path):
        raise ValueError(f"Repository path does not exist: {repo_path}")

    # Check if it's a git repo
    if not os.path.exists(os.path.join(repo_path, ".git")):
        # Try to see if it's inside a git repo (e.g. subdirectory)
        try:
            subprocess.check_call(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=repo_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
             raise ValueError(f"Path is not a git repository: {repo_path}")

    try:
        # Run git ls-files --stage
        # Output format: <mode> <object> <stage>\t<file>
        # Example: 100644 e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 0	src/main.py
        result = subprocess.check_output(
            ["git", "ls-files", "--stage"],
            cwd=repo_path,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to run git ls-files: {e}")

    files = []
    for line in result.splitlines():
        if not line.strip():
            continue
        
        parts = line.split()
        if len(parts) < 4:
            continue
            
        # parts[1] is the hash
        # parts[3:] is the filename (can contain spaces, so we join)
        # However, ls-files output is tab-separated between metadata and filename
        # <mode> <object> <stage>\t<file>
        
        meta, filename = line.split('\t', 1)
        meta_parts = meta.split()
        file_hash = meta_parts[1]
        
        files.append(FileInfo(path=filename, hash=file_hash))

    return files
