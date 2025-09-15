from typing import Dict, List, Optional, Any
from datetime import datetime
import importlib
import inspect
from flask import current_app

from .game_plugin import GamePlugin

class PluginRegistry:
    """Registry for managing game plugins"""

    def __init__(self):
        self._plugins: Dict[str, GamePlugin] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}

    def register_plugin(self, plugin_id: str, plugin_class: type, metadata: Dict[str, Any] = None) -> bool:
        """
        Register a new plugin in the registry.

        Args:
            plugin_id: Unique identifier for the plugin
            plugin_class: The plugin class (must inherit from GamePlugin)
            metadata: Optional metadata about the plugin

        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            if not issubclass(plugin_class, GamePlugin):
                current_app.logger.error(f"Plugin {plugin_id} does not inherit from GamePlugin")
                return False

            if plugin_id in self._plugins:
                current_app.logger.warning(f"Plugin {plugin_id} already registered, updating...")

            plugin_instance = plugin_class()

            # Validate plugin
            validation_result = plugin_instance.validate_plugin()
            if not validation_result["is_valid"]:
                current_app.logger.error(f"Plugin {plugin_id} validation failed: {validation_result['errors']}")
                return False

            # Initialize plugin
            if not plugin_instance.initialize():
                current_app.logger.error(f"Plugin {plugin_id} initialization failed")
                return False

            self._plugins[plugin_id] = plugin_instance

            # Store metadata
            self._plugin_metadata[plugin_id] = {
                **(metadata or {}),
                "plugin_id": plugin_id,
                "class_name": plugin_class.__name__,
                "module_name": plugin_class.__module__,
                "registered_at": datetime.utcnow(),
                "validation_result": validation_result,
                **plugin_instance.get_plugin_info()
            }

            current_app.logger.info(f"Plugin {plugin_id} registered successfully")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to register plugin {plugin_id}: {str(e)}")
            return False

    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        Unregister a plugin from the registry.

        Args:
            plugin_id: The ID of the plugin to unregister

        Returns:
            bool: True if unregistration successful, False otherwise
        """
        try:
            if plugin_id not in self._plugins:
                current_app.logger.warning(f"Plugin {plugin_id} not found in registry")
                return False

            del self._plugins[plugin_id]
            del self._plugin_metadata[plugin_id]

            current_app.logger.info(f"Plugin {plugin_id} unregistered successfully")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to unregister plugin {plugin_id}: {str(e)}")
            return False

    def get_plugin(self, plugin_id: str) -> Optional[GamePlugin]:
        """
        Get a plugin instance by ID.

        Args:
            plugin_id: The ID of the plugin

        Returns:
            Optional[GamePlugin]: The plugin instance or None if not found
        """
        return self._plugins.get(plugin_id)

    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin metadata by ID.

        Args:
            plugin_id: The ID of the plugin

        Returns:
            Optional[Dict[str, Any]]: The plugin metadata or None if not found
        """
        return self._plugin_metadata.get(plugin_id)

    def list_plugins(self, category: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List all registered plugins.

        Args:
            category: Optional category filter
            active_only: If True, only return initialized plugins

        Returns:
            List[Dict[str, Any]]: List of plugin metadata
        """
        plugins = []

        for plugin_id, metadata in self._plugin_metadata.items():
            plugin = self._plugins.get(plugin_id)

            if active_only and (not plugin or not plugin.is_initialized):
                continue

            if category and metadata.get("category") != category:
                continue

            plugins.append(metadata)

        return plugins

    def get_plugin_by_name(self, name: str) -> Optional[GamePlugin]:
        """
        Get a plugin instance by name.

        Args:
            name: The name of the plugin

        Returns:
            Optional[GamePlugin]: The plugin instance or None if not found
        """
        for plugin_id, plugin in self._plugins.items():
            if plugin.name == name:
                return plugin
        return None

    def validate_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all registered plugins.

        Returns:
            Dict[str, Dict[str, Any]]: Validation results for all plugins
        """
        results = {}

        for plugin_id, plugin in self._plugins.items():
            results[plugin_id] = plugin.validate_plugin()

        return results

    def get_plugins_by_category(self, category: str) -> List[GamePlugin]:
        """
        Get all plugins in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List[GamePlugin]: List of plugin instances in the category
        """
        plugins = []

        for plugin in self._plugins.values():
            if plugin.category == category:
                plugins.append(plugin)

        return plugins

    def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """
        Search plugins by name or description.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching plugin metadata
        """
        results = []
        query_lower = query.lower()

        for metadata in self._plugin_metadata.values():
            name = metadata.get("name", "").lower()
            description = metadata.get("description", "").lower()

            if query_lower in name or query_lower in description:
                results.append(metadata)

        return results

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the plugin registry.

        Returns:
            Dict[str, Any]: Registry statistics
        """
        total_plugins = len(self._plugins)
        active_plugins = sum(1 for p in self._plugins.values() if p.is_initialized)
        categories = set(p.category for p in self._plugins.values() if p.category)

        return {
            "total_plugins": total_plugins,
            "active_plugins": active_plugins,
            "inactive_plugins": total_plugins - active_plugins,
            "categories": list(categories),
            "category_count": len(categories)
        }

    def load_plugin_from_module(self, module_path: str, plugin_id: str = None) -> bool:
        """
        Load a plugin from a Python module.

        Args:
            module_path: Path to the module containing the plugin
            plugin_id: Optional custom plugin ID

        Returns:
            bool: True if loading successful, False otherwise
        """
        try:
            module = importlib.import_module(module_path)

            # Find GamePlugin subclasses in the module
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, GamePlugin) and
                    obj != GamePlugin and
                    obj.__module__ == module_path):
                    plugin_classes.append(obj)

            if not plugin_classes:
                current_app.logger.error(f"No GamePlugin subclasses found in module {module_path}")
                return False

            if len(plugin_classes) > 1:
                current_app.logger.warning(f"Multiple GamePlugin subclasses found in {module_path}, using first one")

            plugin_class = plugin_classes[0]
            plugin_id = plugin_id or plugin_class.__name__.lower()

            return self.register_plugin(plugin_id, plugin_class, {
                "module_path": module_path,
                "loaded_from_module": True
            })

        except Exception as e:
            current_app.logger.error(f"Failed to load plugin from module {module_path}: {str(e)}")
            return False


# Global registry instance
plugin_registry = PluginRegistry()