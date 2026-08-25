import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.httpx import parse_httpx

logger = logging.getLogger(__name__)

class HttpxPlugin(BasePlugin):
    """
    HTTPx wrapper plugin to execute real Web Probes scans.
    """

    @property
    def name(self) -> str:
        return "httpx"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes HTTPx for Web Probes."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for HTTPx scan.")
            
        args = payload.get("args", "-tech-detect -status-code -title -web-server")
        
        command = ["httpx", "-u", target, "-json", "-silent"] + args.split()
        
        logger.info(f"Executing real HTTPx scan on target: {target}")
        
        result = self.run_command(command, timeout=300)
        
        if "error" in result:
            return result
            
        parsed_data = parse_httpx(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"HTTPx scan completed on {target}.",
            "findings_count": len(parsed_data.get("hosts", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
