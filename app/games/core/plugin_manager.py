import os
import json
import zipfile
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from flask import current_app

from .plugin_registry import plugin_registry, PluginRegistry
from .game_plugin import GamePlugin

class PluginManager:
    """Manages plugin lifecycle: install, uninstall, update, discovery"""

    def __init__(self, registry: PluginRegistry = None):
        self.registry = registry or plugin_registry
        self.plugins_directory = Path("app/games/plugins")
        self.plugins_directory.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> List[str]:
        """
        Discover and load all plugins from the plugins directory.

        Returns:
            List[str]: List of discovered plugin IDs
        """
        discovered_plugins = []

        try:
            for plugin_dir in self.plugins_directory.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    plugin_id = plugin_dir.name

                    # Check for plugin.json manifest
                    manifest_path = plugin_dir / "plugin.json"
                    if manifest_path.exists():
                        if self._load_plugin_from_directory(plugin_dir):
                            discovered_plugins.append(plugin_id)
                    else:
                        current_app.logger.warning(f"Plugin directory {plugin_id} missing plugin.json manifest")

            current_app.logger.info(f"Discovered {len(discovered_plugins)} plugins")
            return discovered_plugins

        except Exception as e:
            current_app.logger.error(f"Plugin discovery failed: {str(e)}")
            return []

    def install_plugin(self, plugin_data: bytes, plugin_id: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Install a plugin from zip data.

        Args:
            plugin_data: The plugin zip file data
            plugin_id: Optional custom plugin ID

        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, plugin_id)
        """
        temp_dir = None

        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()

            # Extract zip file
            zip_path = os.path.join(temp_dir, "plugin.zip")
            with open(zip_path, 'wb') as f:
                f.write(plugin_data)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find plugin.json manifest
            manifest_path = None
            for root, dirs, files in os.walk(temp_dir):
                if "plugin.json" in files:
                    manifest_path = os.path.join(root, "plugin.json")
                    break

            if not manifest_path:
                return False, "PLUGIN_MANIFEST_NOT_FOUND", None

            # Validate manifest
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            validation_result = self._validate_plugin_manifest(manifest)
            if not validation_result[0]:
                return False, validation_result[1], None

            # Use provided plugin_id or get from manifest
            final_plugin_id = plugin_id or manifest.get("id") or manifest.get("name", "").lower().replace(" ", "_")

            if not final_plugin_id:
                return False, "PLUGIN_ID_REQUIRED", None

            # Check if plugin already exists
            if self.registry.get_plugin(final_plugin_id):
                return False, "PLUGIN_ALREADY_EXISTS", None

            # Copy plugin to plugins directory
            plugin_dir = self.plugins_directory / final_plugin_id
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            shutil.copytree(os.path.dirname(manifest_path), plugin_dir)

            # Load the plugin
            if self._load_plugin_from_directory(plugin_dir):
                current_app.logger.info(f"Plugin {final_plugin_id} installed successfully")
                return True, "PLUGIN_INSTALLED_SUCCESS", final_plugin_id
            else:
                # Cleanup on failure
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir)
                return False, "PLUGIN_LOAD_FAILED", None

        except zipfile.BadZipFile:
            return False, "PLUGIN_INVALID_ZIP", None
        except json.JSONDecodeError:
            return False, "PLUGIN_INVALID_MANIFEST", None
        except Exception as e:
            current_app.logger.error(f"Plugin installation failed: {str(e)}")
            return False, "PLUGIN_INSTALLATION_FAILED", None

        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def uninstall_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Uninstall a plugin.

        Args:
            plugin_id: The ID of the plugin to uninstall

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check if plugin exists
            if not self.registry.get_plugin(plugin_id):
                return False, "PLUGIN_NOT_FOUND"

            # Unregister from registry
            if not self.registry.unregister_plugin(plugin_id):
                return False, "PLUGIN_UNREGISTER_FAILED"

            # Remove plugin directory
            plugin_dir = self.plugins_directory / plugin_id
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            current_app.logger.info(f"Plugin {plugin_id} uninstalled successfully")
            return True, "PLUGIN_UNINSTALLED_SUCCESS"

        except Exception as e:
            current_app.logger.error(f"Plugin uninstallation failed: {str(e)}")
            return False, "PLUGIN_UNINSTALLATION_FAILED"

    def update_plugin(self, plugin_id: str, plugin_data: bytes) -> Tuple[bool, str]:
        """
        Update an existing plugin.

        Args:
            plugin_id: The ID of the plugin to update
            plugin_data: The new plugin zip file data

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check if plugin exists
            if not self.registry.get_plugin(plugin_id):
                return False, "PLUGIN_NOT_FOUND"

            # Backup current plugin
            plugin_dir = self.plugins_directory / plugin_id
            backup_dir = self.plugins_directory / f"{plugin_id}_backup_{int(datetime.utcnow().timestamp())}"

            if plugin_dir.exists():
                shutil.copytree(plugin_dir, backup_dir)

            try:
                # Uninstall current version
                uninstall_result = self.uninstall_plugin(plugin_id)
                if not uninstall_result[0]:
                    return False, f"PLUGIN_UPDATE_FAILED: {uninstall_result[1]}"

                # Install new version
                install_result = self.install_plugin(plugin_data, plugin_id)
                if not install_result[0]:
                    # Restore backup on failure
                    if backup_dir.exists():
                        if plugin_dir.exists():
                            shutil.rmtree(plugin_dir)
                        shutil.move(backup_dir, plugin_dir)
                        self._load_plugin_from_directory(plugin_dir)
                    return False, f"PLUGIN_UPDATE_FAILED: {install_result[1]}"

                # Remove backup on success
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)

                current_app.logger.info(f"Plugin {plugin_id} updated successfully")
                return True, "PLUGIN_UPDATED_SUCCESS"

            except Exception as e:
                # Restore backup on error
                if backup_dir.exists():
                    if plugin_dir.exists():
                        shutil.rmtree(plugin_dir)
                    shutil.move(backup_dir, plugin_dir)
                    self._load_plugin_from_directory(plugin_dir)
                raise e

        except Exception as e:
            current_app.logger.error(f"Plugin update failed: {str(e)}")
            return False, "PLUGIN_UPDATE_FAILED"

    def validate_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Validate a specific plugin.

        Args:
            plugin_id: The ID of the plugin to validate

        Returns:
            Dict[str, Any]: Validation result
        """
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin:
            return {
                "is_valid": False,
                "errors": ["Plugin not found"],
                "warnings": []
            }

        return plugin.validate_plugin()

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a plugin.

        Args:
            plugin_id: The ID of the plugin

        Returns:
            Optional[Dict[str, Any]]: Plugin information or None if not found
        """
        metadata = self.registry.get_plugin_metadata(plugin_id)
        if not metadata:
            return None

        plugin = self.registry.get_plugin(plugin_id)
        validation = plugin.validate_plugin() if plugin else {"is_valid": False}

        # Load manifest if available
        manifest = self._load_plugin_manifest(plugin_id)

        return {
            **metadata,
            "validation": validation,
            "manifest": manifest,
            "directory_path": str(self.plugins_directory / plugin_id),
            "status": "active" if plugin and plugin.is_initialized else "inactive"
        }

    def list_available_plugins(self) -> List[Dict[str, Any]]:
        """
        List all available plugins in the plugins directory.

        Returns:
            List[Dict[str, Any]]: List of available plugins
        """
        available_plugins = []

        try:
            for plugin_dir in self.plugins_directory.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                    plugin_id = plugin_dir.name
                    manifest = self._load_plugin_manifest(plugin_id)

                    is_loaded = self.registry.get_plugin(plugin_id) is not None

                    plugin_info = {
                        "plugin_id": plugin_id,
                        "directory_path": str(plugin_dir),
                        "is_loaded": is_loaded,
                        "manifest": manifest
                    }

                    if is_loaded:
                        metadata = self.registry.get_plugin_metadata(plugin_id)
                        if metadata:
                            plugin_info.update(metadata)

                    available_plugins.append(plugin_info)

        except Exception as e:
            current_app.logger.error(f"Failed to list available plugins: {str(e)}")

        return available_plugins

    def check_dependencies(self, plugin_id: str) -> Dict[str, Any]:
        """
        Check plugin dependencies.

        Args:
            plugin_id: The ID of the plugin

        Returns:
            Dict[str, Any]: Dependency check result
        """
        manifest = self._load_plugin_manifest(plugin_id)
        if not manifest:
            return {"dependencies_met": False, "missing_dependencies": [], "error": "Manifest not found"}

        dependencies = manifest.get("dependencies", {})
        missing_dependencies = []

        # Check Python packages
        python_packages = dependencies.get("python_packages", [])
        for package in python_packages:
            try:
                __import__(package)
            except ImportError:
                missing_dependencies.append(f"python:{package}")

        # Check other plugins
        plugin_dependencies = dependencies.get("plugins", [])
        for dep_plugin in plugin_dependencies:
            if not self.registry.get_plugin(dep_plugin):
                missing_dependencies.append(f"plugin:{dep_plugin}")

        return {
            "dependencies_met": len(missing_dependencies) == 0,
            "missing_dependencies": missing_dependencies,
            "total_dependencies": len(python_packages) + len(plugin_dependencies)
        }

    def _load_plugin_from_directory(self, plugin_dir: Path) -> bool:
        """Load a plugin from a directory."""
        try:
            plugin_id = plugin_dir.name

            # Load manifest
            manifest = self._load_plugin_manifest(plugin_id)
            if not manifest:
                return False

            # Construct module path
            module_path = f"app.games.plugins.{plugin_id}.{manifest.get('main_module', 'main')}"

            return self.registry.load_plugin_from_module(module_path, plugin_id)

        except Exception as e:
            current_app.logger.error(f"Failed to load plugin from directory {plugin_dir}: {str(e)}")
            return False

    def _load_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Load plugin manifest from plugin.json."""
        try:
            manifest_path = self.plugins_directory / plugin_id / "plugin.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Failed to load manifest for plugin {plugin_id}: {str(e)}")

        return None

    def _validate_plugin_manifest(self, manifest: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate plugin manifest structure."""
        required_fields = ["name", "version", "main_module"]

        for field in required_fields:
            if field not in manifest:
                return False, f"PLUGIN_MANIFEST_MISSING_FIELD: {field}"

        # Validate version format
        version = manifest.get("version", "")
        if not version or not isinstance(version, str):
            return False, "PLUGIN_MANIFEST_INVALID_VERSION"

        return True, "PLUGIN_MANIFEST_VALID"


# Global plugin manager instance
plugin_manager = PluginManager()