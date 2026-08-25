import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.naabu import parse_naabu

logger = logging.getLogger(__name__)

class NaabuPlugin(BasePlugin):
    """
    Naabu wrapper plugin to execute real Port Scanning.
    """

    @property
    def name(self) -> str:
        return "naabu"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Naabu for Port Scanning."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for Naabu scan.")
            
        args = payload.get("args", "")
        
        command = ["naabu", "-host", target, "-json", "-silent"] + args.split()
        
        logger.info(f"Executing real Naabu scan on target: {target}")
        
        result = self.run_command(command, timeout=600)
        
        if "error" in result:
            return result
            
        parsed_data = parse_naabu(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"Naabu scan completed on {target}.",
            "findings_count": len(parsed_data.get("hosts", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
