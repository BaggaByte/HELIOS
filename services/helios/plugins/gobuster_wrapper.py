import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.gobuster import parse_gobuster

logger = logging.getLogger(__name__)

class GobusterPlugin(BasePlugin):
    """
    Gobuster wrapper plugin to execute real Directory Brute-Forcing scans.
    """

    @property
    def name(self) -> str:
        return "gobuster"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes Gobuster for Directory Brute-Forcing."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        wordlist = payload.get("wordlist")
        if not target or not wordlist:
            raise ValueError("Target and wordlist are required for Gobuster scan.")
            
        args = payload.get("args", "")
        
        command = ["gobuster", "dir", "-u", target, "-w", wordlist, "-q", "--no-color"] + args.split()
        
        logger.info(f"Executing real Gobuster scan on target: {target}")
        
        result = self.run_command(command, timeout=600)
        
        if "error" in result and result["error"].startswith("Executable"):
            return result
            
        parsed_data = parse_gobuster(result.get("stdout", ""))
        
        return {
            "status": "success",
            "message": f"Gobuster scan completed on {target}.",
            "findings_count": len(parsed_data.get("directories", [])),
            "target": target,
            "parsed_data": parsed_data,
            "raw_output": result.get("stdout", "")
        }
