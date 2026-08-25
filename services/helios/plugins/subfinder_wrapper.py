import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.subfinder import parse_subfinder

logger = logging.getLogger(__name__)

class SubfinderPlugin(BasePlugin):
    """
    Subfinder wrapper plugin to execute real Subdomain Enumeration.
    """

    @property
    def name(self) -> str:
        return "subfinder"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Subfinder for Subdomain Enumeration."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Subfinder scan.")
            
        args = payload.get("args", "")
        
        # Build command: Use -json for easy parsing
        command = ["subfinder", "-d", target, "-json", "-silent"] + args.split()
        
        logger.info(f"Executing real Subfinder scan on target: {target}")
        
        result = self.run_command(command, timeout=300)
        
        if "error" in result:
            return result
            
        # Parse the JSONL output
        parsed_data = parse_subfinder(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"Subfinder scan completed on {target}.",
            "findings_count": len(parsed_data.get("subdomains", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
