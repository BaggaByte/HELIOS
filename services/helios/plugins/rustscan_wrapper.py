import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.nmap import parse_nmap_xml
import tempfile
import os

logger = logging.getLogger(__name__)

class RustscanPlugin(BasePlugin):
    """
    Rustscan wrapper plugin to execute real Port Scanning.
    """

    @property
    def name(self) -> str:
        return "rustscan"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Rustscan for Port Scanning."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Rustscan scan.")
            
        args = payload.get("args", "-a")
        
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            # Command: rustscan -a target -- -sV -oX tmp_path
            command = ["rustscan"] + args.split() + [target, "--", "-sV", "-oX", tmp_path]
            
            logger.info(f"Executing real Rustscan scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                # We can reuse the nmap XML parser!
                parsed_data = parse_nmap_xml(content)
                # Ensure the return matches our expected format
                if not isinstance(parsed_data, dict):
                    parsed_data = {"hosts": parsed_data}
            except Exception as e:
                logger.error(f"Failed to read/parse Rustscan output file: {e}")
                parsed_data = {"hosts": []}
                
            return {
                "status": "success",
                "message": f"Rustscan scan completed on {target}.",
                "findings_count": len(parsed_data.get("hosts", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
