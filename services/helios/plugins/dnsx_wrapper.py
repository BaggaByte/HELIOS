import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.dnsx import parse_dnsx

logger = logging.getLogger(__name__)

class DnsxPlugin(BasePlugin):
    """
    DNSx wrapper plugin to execute real DNS Resolution scans.
    """

    @property
    def name(self) -> str:
        return "dnsx"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes DNSx for DNS Resolution."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            raise ValueError("Target is required for DNSx scan.")
            
        args = payload.get("args", "")
        
        command = ["dnsx", "-d", target, "-json", "-silent"] + args.split()
        
        logger.info(f"Executing real DNSx scan on target: {target}")
        
        result = self.run_command(command, timeout=300)
        
        if "error" in result:
            return result
            
        parsed_data = parse_dnsx(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"DNSx scan completed on {target}.",
            "findings_count": len(parsed_data.get("subdomains", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
