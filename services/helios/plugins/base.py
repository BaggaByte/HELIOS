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
