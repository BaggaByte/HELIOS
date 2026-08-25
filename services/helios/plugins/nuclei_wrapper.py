import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.nuclei import parse_nuclei

logger = logging.getLogger(__name__)

class NucleiPlugin(BasePlugin):
    """
    Nuclei wrapper plugin to execute real DAST scans.
    """

    @property
    def name(self) -> str:
        return "nuclei"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Nuclei for Dynamic Application Security Testing (DAST) scans."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target URL is required for Nuclei scan.")
            
        args = payload.get("args", "-t cves/")
        
        # Build command: Use -jsonl for easy parsing
        command = ["nuclei", "-u", target, "-jsonl"] + args.split()
        
        logger.info(f"Executing real Nuclei scan on target: {target}")
        
        result = self.run_command(command, timeout=600)
        
        if "error" in result:
            return result
            
        # Parse the JSONL output
        parsed_data = parse_nuclei(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"Nuclei scan completed on {target}.",
            "findings_count": len(parsed_data.get("findings", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
