from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

def build_dependency_graph(file_content: str, filename: str) -> Dict[str, Any]:
    """
    Parses manifest files (package.json, requirements.txt) and extracts dependencies.
    """
    deps = []
    
    if filename.endswith('package.json'):
        try:
            data = json.loads(file_content)
            all_deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            for pkg, ver in all_deps.items():
                deps.append({"package": pkg, "version": ver, "ecosystem": "npm"})
        except Exception as e:
            logger.error(f"Failed to parse package.json: {e}")
            
    elif filename.endswith('requirements.txt'):
        for line in file_content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('==')
                pkg = parts[0]
                ver = parts[1] if len(parts) > 1 else "latest"
                deps.append({"package": pkg, "version": ver, "ecosystem": "pypi"})
                
    return {
        "filename": filename,
        "dependencies": deps
    }
