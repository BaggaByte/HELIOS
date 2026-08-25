import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.katana import parse_katana

logger = logging.getLogger(__name__)

class KatanaPlugin(BasePlugin):
    """
    Katana wrapper plugin to execute real URL Crawling scans.
    """

    @property
    def name(self) -> str:
        return "katana"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Katana for Crawlers."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Katana scan.")
            
        args = payload.get("args", "")
        
        command = ["katana", "-u", target, "-jsonl"] + args.split()
        
        logger.info(f"Executing real Katana scan on target: {target}")
        
        result = self.run_command(command, timeout=600)
        
        if "error" in result:
            return result
            
        parsed_data = parse_katana(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"Katana scan completed on {target}.",
            "findings_count": len(parsed_data.get("directories", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
