from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime

from ..repositories.game_repository import GameRepository
from ..models.game import Game
from ..core.plugin_manager import plugin_manager
from ..core.plugin_registry import plugin_registry

class GameService:
    """Service for game management operations"""

    def __init__(self):
        self.game_repository = GameRepository()

    def get_all_games(self, active_only: bool = True, category: str = None,
                     page: int = 1, limit: int = 20, sort_by: str = "created_at") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get all games with pagination and filtering.

        Args:
            active_only: If True, only return active games
            category: Optional category filter
            page: Page number (1-based)
            limit: Number of games per page
            sort_by: Sort field (created_at, rating, install_count, name)

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            skip = (page - 1) * limit

            if category:
                games = self.game_repository.get_games_by_category(category, active_only)
            else:
                games = self.game_repository.get_all_games(active_only, limit, skip, sort_by)

            # Get total count for pagination
            total_count = self.game_repository.count(
                {"is_active": True} if active_only else {}
            )

            total_pages = (total_count + limit - 1) // limit

            games_data = [game.to_api_dict() for game in games]

            result = {
                "games": games_data,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }

            current_app.logger.info(f"Retrieved {len(games)} games")
            return True, "GAMES_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get games: {str(e)}")
            return False, "GAMES_RETRIEVAL_FAILED", None

    def get_game_by_id(self, game_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get a game by its ID.

        Args:
            game_id: The game ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            # Get plugin info if available
            plugin_info = None
            if game.plugin_id:
                plugin = plugin_registry.get_plugin(game.plugin_id)
                if plugin:
                    plugin_info = plugin.get_plugin_info()

            result = {
                "game": game.to_api_dict(),
                "plugin_info": plugin_info
            }

            current_app.logger.info(f"Retrieved game {game_id}")
            return True, "GAME_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get game {game_id}: {str(e)}")
            return False, "GAME_RETRIEVAL_FAILED", None

    def install_game_plugin(self, plugin_data: bytes, plugin_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Install a new game plugin.

        Args:
            plugin_data: The plugin zip file data
            plugin_id: Optional custom plugin ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Install plugin using plugin manager
            success, message, final_plugin_id = plugin_manager.install_plugin(plugin_data, plugin_id)

            if not success:
                return False, message, None

            # Get the installed plugin
            plugin = plugin_registry.get_plugin(final_plugin_id)
            if not plugin:
                return False, "PLUGIN_NOT_FOUND_AFTER_INSTALL", None

            # Create game record in database
            game = Game(
                name=plugin.name,
                description=plugin.description,
                category=plugin.category,
                version=plugin.version,
                author=plugin.author,
                plugin_id=final_plugin_id,
                credit_rate=plugin.credit_rate
            )

            # Get game rules for additional metadata
            try:
                rules = plugin.get_rules()
                game.min_players = rules.min_players
                game.max_players = rules.max_players
                game.estimated_duration_minutes = rules.estimated_duration_minutes
                game.difficulty_level = rules.difficulty_level
                game.requires_internet = rules.requires_internet
                game.instructions = rules.instructions
            except Exception as e:
                current_app.logger.warning(f"Failed to get rules for plugin {final_plugin_id}: {str(e)}")

            game_id = self.game_repository.create_game(game)
            if not game_id:
                # Rollback plugin installation
                plugin_manager.uninstall_plugin(final_plugin_id)
                return False, "GAME_CREATION_FAILED", None

            game._id = game_id
            self.game_repository.increment_install_count(game_id)

            result = {
                "game": game.to_api_dict(),
                "plugin_id": final_plugin_id
            }

            current_app.logger.info(f"Game plugin {final_plugin_id} installed successfully")
            return True, "GAME_PLUGIN_INSTALLED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to install game plugin: {str(e)}")
            return False, "GAME_PLUGIN_INSTALLATION_FAILED", None

    def uninstall_game_plugin(self, game_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Uninstall a game plugin.

        Args:
            game_id: The game ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get game record
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            # Uninstall plugin
            if game.plugin_id:
                plugin_success, plugin_message = plugin_manager.uninstall_plugin(game.plugin_id)
                if not plugin_success:
                    current_app.logger.warning(f"Plugin uninstall failed: {plugin_message}")

            # Remove game record
            if not self.game_repository.delete_game(game_id):
                return False, "GAME_DELETION_FAILED", None

            current_app.logger.info(f"Game {game_id} uninstalled successfully")
            return True, "GAME_PLUGIN_UNINSTALLED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Failed to uninstall game {game_id}: {str(e)}")
            return False, "GAME_PLUGIN_UNINSTALLATION_FAILED", None

    def validate_game_plugin(self, game_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate a game plugin.

        Args:
            game_id: The game ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            if not game.plugin_id:
                return False, "GAME_HAS_NO_PLUGIN", None

            validation_result = plugin_manager.validate_plugin(game.plugin_id)
            dependency_check = plugin_manager.check_dependencies(game.plugin_id)

            result = {
                "game_id": game_id,
                "plugin_id": game.plugin_id,
                "validation": validation_result,
                "dependencies": dependency_check
            }

            current_app.logger.info(f"Game plugin {game.plugin_id} validated")
            return True, "GAME_PLUGIN_VALIDATED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to validate game plugin {game_id}: {str(e)}")
            return False, "GAME_PLUGIN_VALIDATION_FAILED", None

    def search_games(self, query: str, active_only: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Search games by name or description.

        Args:
            query: Search query
            active_only: If True, only search active games

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            if not query or len(query.strip()) < 2:
                return False, "SEARCH_QUERY_TOO_SHORT", None

            games = self.game_repository.search_games(query.strip(), active_only)
            games_data = [game.to_api_dict() for game in games]

            result = {
                "games": games_data,
                "query": query.strip(),
                "count": len(games_data)
            }

            current_app.logger.info(f"Search for '{query}' returned {len(games)} results")
            return True, "GAMES_SEARCH_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to search games: {str(e)}")
            return False, "GAMES_SEARCH_FAILED", None

    def get_game_info(self, game_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get detailed information about a game including plugin details.

        Args:
            game_id: The game ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            result = {
                "game": game.to_api_dict()
            }

            # Add plugin information if available
            if game.plugin_id:
                plugin_info = plugin_manager.get_plugin_info(game.plugin_id)
                if plugin_info:
                    result["plugin_info"] = plugin_info

                # Get plugin rules
                plugin = plugin_registry.get_plugin(game.plugin_id)
                if plugin:
                    try:
                        rules = plugin.get_rules()
                        result["rules"] = {
                            "min_players": rules.min_players,
                            "max_players": rules.max_players,
                            "estimated_duration_minutes": rules.estimated_duration_minutes,
                            "difficulty_level": rules.difficulty_level,
                            "requires_internet": rules.requires_internet,
                            "description": rules.description,
                            "instructions": rules.instructions
                        }
                    except Exception as e:
                        current_app.logger.warning(f"Failed to get rules for plugin {game.plugin_id}: {str(e)}")

            current_app.logger.info(f"Retrieved detailed info for game {game_id}")
            return True, "GAME_INFO_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get game info {game_id}: {str(e)}")
            return False, "GAME_INFO_RETRIEVAL_FAILED", None

    def get_game_categories(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get available game categories.

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            stats = self.game_repository.get_games_stats()
            categories = stats.get("categories", [])

            result = {
                "categories": categories,
                "total_categories": len(categories)
            }

            current_app.logger.info(f"Retrieved {len(categories)} game categories")
            return True, "GAME_CATEGORIES_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get game categories: {str(e)}")
            return False, "GAME_CATEGORIES_RETRIEVAL_FAILED", None

    def get_games_stats(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get statistics about games.

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            stats = self.game_repository.get_games_stats()
            plugin_stats = plugin_registry.get_registry_stats()

            result = {
                "database_stats": stats,
                "plugin_stats": plugin_stats
            }

            current_app.logger.info("Retrieved games statistics")
            return True, "GAMES_STATS_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get games stats: {str(e)}")
            return False, "GAMES_STATS_RETRIEVAL_FAILED", None

    def rate_game(self, game_id: str, rating: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Rate a game.

        Args:
            game_id: The game ID
            rating: Rating value (1.0 to 5.0)

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            if not (1.0 <= rating <= 5.0):
                return False, "INVALID_RATING_VALUE", None

            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            # Update rating
            old_rating = game.rating
            old_total = game.total_ratings

            game.update_rating(rating)

            # Update in database
            if not self.game_repository.update_game_rating(game_id, game.rating, game.total_ratings):
                return False, "GAME_RATING_UPDATE_FAILED", None

            result = {
                "game_id": game_id,
                "new_rating": game.rating,
                "total_ratings": game.total_ratings,
                "previous_rating": old_rating
            }

            current_app.logger.info(f"Game {game_id} rated {rating}, new average: {game.rating}")
            return True, "GAME_RATING_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to rate game {game_id}: {str(e)}")
            return False, "GAME_RATING_FAILED", None