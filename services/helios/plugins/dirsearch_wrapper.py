import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.dirsearch import parse_dirsearch
import tempfile
import os

logger = logging.getLogger(__name__)

class DirsearchPlugin(BasePlugin):
    """
    Dirsearch wrapper plugin to execute real Directory Brute-Forcing scans.
    """

    @property
    def name(self) -> str:
        return "dirsearch"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Dirsearch for Directory Brute-Forcing."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        wordlist = payload.get("wordlist")
        if not target or not wordlist:
            raise ValueError("Target and wordlist are required for Dirsearch scan.")
            
        args = payload.get("args", "")
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            # Command: dirsearch -u target -w wordlist --format json -o tmp_path
            command = ["dirsearch", "-u", target, "-w", wordlist, "--format", "json", "-o", tmp_path] + args.split()
            
            logger.info(f"Executing real Dirsearch scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_dirsearch(content)
            except Exception as e:
                logger.error(f"Failed to read/parse Dirsearch output file: {e}")
                parsed_data = {"directories": []}
                
            return {
                "status": "success",
                "message": f"Dirsearch scan completed on {target}.",
                "findings_count": len(parsed_data.get("directories", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
