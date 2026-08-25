import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.gau import parse_gau

logger = logging.getLogger(__name__)

class GauPlugin(BasePlugin):
    """
    GAU wrapper plugin to execute real URL Discovery scans.
    """

    @property
    def name(self) -> str:
        return "gau"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes GAU for URL Discovery."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for GAU scan.")
            
        args = payload.get("args", "")
        
        command = ["gau", target, "--json"] + args.split()
        
        logger.info(f"Executing real GAU scan on target: {target}")
        
        result = self.run_command(command, timeout=300)
        
        if "error" in result:
            return result
            
        parsed_data = parse_gau(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"GAU scan completed on {target}.",
            "findings_count": len(parsed_data.get("directories", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
