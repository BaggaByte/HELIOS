import logging
import os
from typing import Dict, Any, Callable

# Import the analyzers we have
from helios.core.source_code.analyzers.python_analyzer import analyze_python_source
from helios.core.source_code.analyzers.js_analyzer import analyze_js_source
from helios.core.source_code.analyzers.php_analyzer import analyze_php_source

logger = logging.getLogger(__name__)

class SourceCodeLoader:
    """
    Detects language based on file extension and routes the source code
    to the appropriate AST/static analyzer.
    """
    def __init__(self):
        self.extension_map: Dict[str, Callable] = {
            '.py': analyze_python_source,
            '.js': analyze_js_source,
            '.php': analyze_php_source,
            # '.ts': analyze_ts_source,
            # '.go': analyze_go_source,
            # ... others mapped here as they are built
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reads a file from disk, detects language, and routes to the analyzer.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in self.extension_map:
            logger.warning(f"No specific analyzer for extension {ext}. Falling back to basic regex.")
            return {
                "language": "unknown",
                "filename": os.path.basename(file_path),
                "error": "Unsupported language extension"
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {
                "filename": os.path.basename(file_path),
                "error": f"Failed to read file: {e}"
            }

        analyzer_func = self.extension_map[ext]
        return analyzer_func(code, filename=os.path.basename(file_path))

    def analyze_code(self, code: str, language_hint: str, filename: str = "snippet") -> Dict[str, Any]:
        """
        Analyzes a raw string of code. Requires a language hint (e.g. '.py' or 'python').
        """
        ext = language_hint.lower()
        if not ext.startswith('.'):
            # Try to map common names to extensions
            lang_to_ext = {
                'python': '.py', 'javascript': '.js', 'typescript': '.ts', 
                'go': '.go', 'rust': '.rs', 'java': '.java'
            }
            ext = lang_to_ext.get(ext, f".{ext}")

        if ext not in self.extension_map:
            return {
                "language": "unknown",
                "filename": filename,
                "error": f"Unsupported language: {language_hint}"
            }

        analyzer_func = self.extension_map[ext]
        return analyzer_func(code, filename=filename)

loader = SourceCodeLoader()
