import logging
from typing import Dict, List

from helios.plugins.base import BasePlugin
from helios.plugins.loader import discover_plugins

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Singleton registry holding all active HELIOS plugins."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance._plugins = {}
            cls._instance._is_loaded = False
        return cls._instance

    def load_all(self):
        """Discovers and initializes all valid plugins."""
        if self._is_loaded:
            return

        logger.info("Initializing Plugin Registry...")
        plugin_classes = discover_plugins()

        for cls in plugin_classes:
            try:
                instance = cls()
                name = instance.name

                if name in self._plugins:
                    logger.warning(
                        f"Plugin '{name}' is already registered. Overwriting."
                    )

                self._plugins[name] = instance
                logger.info(f"Successfully loaded plugin: {name} v{instance.version}")
            except Exception as e:
                logger.error(f"Failed to instantiate plugin class {cls.__name__}: {e}")

        self._is_loaded = True
        logger.info(f"Plugin Registry loaded {len(self._plugins)} plugins.")

    def get_plugin(self, name: str) -> BasePlugin:
        """Retrieve a specific plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, str]]:
        """List metadata for all active plugins."""
        return [
            {"name": p.name, "version": p.version, "description": p.description}
            for p in self._plugins.values()
        ]


# Global singleton instance
plugin_registry = PluginRegistry()
