import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.masscan import parse_masscan
import tempfile
import os

logger = logging.getLogger(__name__)

class MasscanPlugin(BasePlugin):
    """
    Masscan wrapper plugin to execute real Port Scanning.
    """

    @property
    def name(self) -> str:
        return "masscan"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Masscan for Port Scanning."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Masscan scan.")
            
        args = payload.get("args", "-p0-65535 --rate 1000")
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            command = ["masscan", target, "-oJ", tmp_path] + args.split()
            
            logger.info(f"Executing real Masscan scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_masscan(content)
            except Exception as e:
                logger.error(f"Failed to read/parse Masscan output file: {e}")
                parsed_data = {"hosts": []}
                
            return {
                "status": "success",
                "message": f"Masscan scan completed on {target}.",
                "findings_count": len(parsed_data.get("hosts", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
