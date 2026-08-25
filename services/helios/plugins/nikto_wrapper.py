import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.nikto import parse_nikto
import tempfile
import os

logger = logging.getLogger(__name__)

class NiktoPlugin(BasePlugin):
    """
    Nikto wrapper plugin to execute real DAST scans.
    """

    @property
    def name(self) -> str:
        return "nikto"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Nikto for DAST."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Nikto scan.")
            
        args = payload.get("args", "")
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            command = ["nikto", "-h", target, "-Format", "json", "-o", tmp_path] + args.split()
            
            logger.info(f"Executing real Nikto scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_nikto(content)
            except Exception as e:
                logger.error(f"Failed to read/parse Nikto output file: {e}")
                parsed_data = {"findings": []}
                
            return {
                "status": "success",
                "message": f"Nikto scan completed on {target}.",
                "findings_count": len(parsed_data.get("findings", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
