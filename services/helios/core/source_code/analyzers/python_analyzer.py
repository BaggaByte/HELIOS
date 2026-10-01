import ast
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = []
        self.imports = []
        self.functions = []
        self.classes = []

        # Heuristic signatures for Python
        self.dangerous_functions = {
            "eval": "Code execution via eval()",
            "exec": "Code execution via exec()",
            "system": "Command injection via os.system()",
            "Popen": "Command injection via subprocess.Popen()",
            "loads": "Insecure deserialization via pickle.loads()",
        }

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        decorators = [
            ast.unparse(d) if hasattr(ast, "unparse") else "decorator"
            for d in node.decorator_list
        ]
        self.functions.append(
            {"name": node.name, "line": node.lineno, "decorators": decorators}
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.dangerous_functions:
                self.findings.append(
                    {
                        "type": "VULNERABILITY",
                        "severity": "HIGH",
                        "line": node.lineno,
                        "description": self.dangerous_functions[func_name],
                    }
                )
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if func_name in self.dangerous_functions:
                self.findings.append(
                    {
                        "type": "VULNERABILITY",
                        "severity": "HIGH",
                        "line": node.lineno,
                        "description": self.dangerous_functions[func_name],
                    }
                )

        self.generic_visit(node)


def analyze_python_source(code: str, filename: str = "unknown.py") -> Dict[str, Any]:
    """
    Parses Python source code using AST and extracts intelligence.
    """
    try:
        tree = ast.parse(code, filename=filename)
        visitor = SecurityASTVisitor()
        visitor.visit(tree)

        return {
            "language": "python",
            "filename": filename,
            "imports": list(set(visitor.imports)),
            "functions": visitor.functions,
            "classes": visitor.classes,
            "security_findings": visitor.findings,
        }
    except SyntaxError as e:
        logger.error(f"Syntax error parsing {filename}: {e}")
        return {
            "language": "python",
            "filename": filename,
            "error": f"Syntax error: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to analyze {filename}: {e}")
        return {"language": "python", "filename": filename, "error": str(e)}
