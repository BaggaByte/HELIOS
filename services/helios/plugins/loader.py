import importlib
import inspect
import logging
import pkgutil

from helios.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


def discover_plugins(package_name: str = "helios.plugins") -> list[type[BasePlugin]]:
    """
    Dynamically discover all classes inheriting from BasePlugin in the given package.
    """
    plugins = []

    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error(f"Failed to import plugin package {package_name}: {e}")
        return plugins

    # Ensure package has __path__ for pkgutil
    if not hasattr(package, "__path__"):
        return plugins

    for _, module_name, is_pkg in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        if is_pkg:
            continue

        try:
            module = importlib.import_module(module_name)
            for item_name, item in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BasePlugin but NOT BasePlugin itself
                if issubclass(item, BasePlugin) and item is not BasePlugin:
                    plugins.append(item)
                    logger.debug(f"Discovered plugin: {item_name} in {module_name}")
        except Exception as e:
            logger.error(f"Error loading plugin module {module_name}: {e}")

    return plugins
