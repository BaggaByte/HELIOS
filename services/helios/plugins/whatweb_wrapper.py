import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.whatweb import parse_whatweb
import tempfile
import os

logger = logging.getLogger(__name__)

class WhatwebPlugin(BasePlugin):
    """
    Whatweb wrapper plugin to execute real Web Probes scans.
    """

    @property
    def name(self) -> str:
        return "whatweb"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Whatweb for Web Probes."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Whatweb scan.")
            
        args = payload.get("args", "-a 3")
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            command = ["whatweb", target, "--log-json", tmp_path] + args.split()
            
            logger.info(f"Executing real Whatweb scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_whatweb(content)
            except Exception as e:
                logger.error(f"Failed to read/parse Whatweb output file: {e}")
                parsed_data = {"hosts": []}
                
            return {
                "status": "success",
                "message": f"Whatweb scan completed on {target}.",
                "findings_count": len(parsed_data.get("hosts", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
