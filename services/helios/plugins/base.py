from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """Abstract Base Class for all HELIOS plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the plugin."""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """The version string of the plugin."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what the plugin does."""
        pass
        
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main execution block for the plugin.
        Accepts a dictionary payload and returns a dictionary of results.
        """
        pass

    def run_command(self, command: list[str], capture_output: bool = True, text: bool = True, timeout: int = 300) -> Dict[str, Any]:
        import subprocess
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Plugin {self.name} executing command: {' '.join(command)}")
        
        try:
            result = subprocess.run(command, capture_output=capture_output, text=text, timeout=timeout, check=False)
            if result.returncode != 0 and not result.stdout:
                logger.error(f"Execution failed: {result.stderr}")
                return {"error": f"Execution failed: {result.stderr}"}
            
            return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
            
        except FileNotFoundError:
            return {"error": f"Executable '{command[0]}' not found on system PATH."}
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds."}
        except Exception as e:
            return {"error": str(e)}
