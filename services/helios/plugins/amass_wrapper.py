import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.amass import parse_amass
import tempfile
import os

logger = logging.getLogger(__name__)

class AmassPlugin(BasePlugin):
    """
    Amass wrapper plugin to execute real Subdomain Enumeration scans.
    """

    @property
    def name(self) -> str:
        return "amass"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Amass for Subdomain Enumeration."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Amass scan.")
            
        args = payload.get("args", "")
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            command = ["amass", "enum", "-d", target, "-json", tmp_path] + args.split()
            
            logger.info(f"Executing real Amass scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_amass(content)
            except Exception as e:
                logger.error(f"Failed to read/parse Amass output file: {e}")
                parsed_data = {"subdomains": []}
                
            return {
                "status": "success",
                "message": f"Amass scan completed on {target}.",
                "findings_count": len(parsed_data.get("subdomains", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
