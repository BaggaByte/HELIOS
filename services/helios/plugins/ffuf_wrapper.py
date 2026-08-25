import logging
from typing import Dict, Any
from helios.plugins.base import BasePlugin
from helios.core.recon.parsers.ffuf import parse_ffuf
import json
import tempfile
import os

logger = logging.getLogger(__name__)

class FfufPlugin(BasePlugin):
    """
    FFUF wrapper plugin to execute real fuzzing and directory brute-forcing.
    """

    @property
    def name(self) -> str:
        return "ffuf"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Executes FFUF for fast web fuzzer capabilities."
        
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        wordlist = payload.get("wordlist")
        
        if not target or not wordlist:
            raise ValueError("Target and wordlist are required for FFUF scan.")
            
        args = payload.get("args", "")
        
        # FFUF doesn't easily output JSON to stdout, it prefers a file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            # Build command: Use -o for JSON output
            command = ["ffuf", "-u", f"{target}/FUZZ", "-w", wordlist, "-o", tmp_path, "-of", "json"] + args.split()
            
            logger.info(f"Executing real FFUF scan on target: {target}")
            
            result = self.run_command(command, timeout=600)
            
            if "error" in result and result["error"].startswith("Executable"):
                return result
                
            # Parse the JSON output from the temp file
            try:
                with open(tmp_path, 'r') as f:
                    content = f.read()
                parsed_data = parse_ffuf(content)
            except Exception as e:
                logger.error(f"Failed to read/parse FFUF output file: {e}")
                parsed_data = {"directories": []}
                
            return {
                "status": "success",
                "message": f"FFUF scan completed on {target}.",
                "findings_count": len(parsed_data.get("directories", [])),
                "target": target,
                "parsed_data": parsed_data,
                "raw_output": result.get("stdout", "")
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
