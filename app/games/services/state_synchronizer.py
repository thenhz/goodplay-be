from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta
import logging

from ..repositories.game_session_repository import GameSessionRepository
from ..models.game_session import GameSession

class StateSynchronizer:
    """Service for synchronizing game session state across devices"""

    def __init__(self):
        self.session_repository = GameSessionRepository()

    def _get_logger(self):
        """Get logger safely, handling cases where no application context exists"""
        try:
            return current_app.logger
        except RuntimeError:
            # Fallback to standard logger when no app context exists (e.g., in tests)
            return logging.getLogger(__name__)

    def sync_session_state(self, session_id: str, device_state: Dict[str, Any],
                          device_info: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Synchronize session state from a device.

        Args:
            session_id: The session ID
            device_state: Current state from the device
            device_info: Information about the device

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get current session
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if session.is_ended():
                return False, "SESSION_ALREADY_ENDED", None

            # Check sync version for conflict resolution
            device_sync_version = device_state.get("sync_version", 0)

            if device_sync_version < session.sync_version:
                # Device is behind, send server state
                self._get_logger().info(f"Device sync conflict for session {session_id}: device version {device_sync_version} < server version {session.sync_version}")
                return True, "SYNC_CONFLICT_SERVER_WINS", {
                    "session": session.to_api_dict(),
                    "conflict_resolution": "server_wins",
                    "server_sync_version": session.sync_version,
                    "device_sync_version": device_sync_version
                }

            # Update session with device state
            session.update_state(device_state.get("current_state", {}))

            # Update device info
            session.update_device_info(device_info)

            # Update score if provided
            if "score" in device_state and device_state["score"] is not None:
                session.update_score(device_state["score"])

            # Add any new moves
            if "new_moves" in device_state and device_state["new_moves"]:
                for move in device_state["new_moves"]:
                    session.add_move(move)

            # Update play duration if provided
            if "play_duration_ms" in device_state:
                session.play_duration = device_state["play_duration_ms"]

            # Update achievements
            if "new_achievements" in device_state and device_state["new_achievements"]:
                for achievement in device_state["new_achievements"]:
                    session.add_achievement(achievement)

            # Update statistics
            if "statistics" in device_state:
                session.update_statistics(device_state["statistics"])

            # Update sync info
            session.update_sync_info()

            # Save to database
            if not self.session_repository.update_session(session_id, session):
                return False, "SYNC_UPDATE_FAILED", None

            # Get updated session
            updated_session = self.session_repository.get_session_by_session_id(session_id)

            result = {
                "session": updated_session.to_api_dict() if updated_session else session.to_api_dict(),
                "sync_version": updated_session.sync_version if updated_session else session.sync_version,
                "last_sync_at": updated_session.last_sync_at.isoformat() if updated_session and updated_session.last_sync_at else None
            }

            self._get_logger().info(f"Synchronized session {session_id} from device {device_info.get('device_id', 'unknown')}")
            return True, "SESSION_SYNC_SUCCESS", result

        except Exception as e:
            self._get_logger().error(f"Failed to sync session {session_id}: {str(e)}")
            return False, "SESSION_SYNC_FAILED", None

    def get_session_for_device(self, session_id: str, device_info: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get session state optimized for a specific device.

        Args:
            session_id: The session ID
            device_info: Information about the requesting device

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            # Update device tracking
            session.update_device_info(device_info)
            session.update_sync_info()

            # Save device tracking
            self.session_repository.update_session(session_id, session)

            result = {
                "session": session.to_api_dict(),
                "sync_version": session.sync_version,
                "device_specific_data": self._get_device_specific_data(session, device_info)
            }

            self._get_logger().info(f"Provided session {session_id} to device {device_info.get('device_id', 'unknown')}")
            return True, "SESSION_PROVIDED_SUCCESS", result

        except Exception as e:
            self._get_logger().error(f"Failed to provide session {session_id} to device: {str(e)}")
            return False, "SESSION_PROVISION_FAILED", None

    def resolve_sync_conflict(self, session_id: str, device_state: Dict[str, Any],
                             resolution_strategy: str = "server_wins") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Resolve synchronization conflicts between device and server state.

        Args:
            session_id: The session ID
            device_state: State from the device
            resolution_strategy: Strategy for conflict resolution ('server_wins', 'device_wins', 'merge')

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if resolution_strategy == "server_wins":
                # Return server state
                result = {
                    "session": session.to_api_dict(),
                    "resolution": "server_wins",
                    "conflict_data": device_state
                }

            elif resolution_strategy == "device_wins":
                # Accept device state
                session.update_state(device_state.get("current_state", {}))
                if "score" in device_state:
                    session.update_score(device_state["score"])
                if "play_duration_ms" in device_state:
                    session.play_duration = device_state["play_duration_ms"]

                session.update_sync_info()
                self.session_repository.update_session(session_id, session)

                result = {
                    "session": session.to_api_dict(),
                    "resolution": "device_wins"
                }

            elif resolution_strategy == "merge":
                # Intelligent merge of states
                result = self._merge_session_states(session, device_state)

            else:
                return False, "INVALID_RESOLUTION_STRATEGY", None

            self._get_logger().info(f"Resolved sync conflict for session {session_id} using strategy: {resolution_strategy}")
            return True, "SYNC_CONFLICT_RESOLVED", result

        except Exception as e:
            self._get_logger().error(f"Failed to resolve sync conflict for session {session_id}: {str(e)}")
            return False, "SYNC_CONFLICT_RESOLUTION_FAILED", None

    def check_session_conflicts(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check for active sessions with potential synchronization conflicts.

        Args:
            user_id: The user ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get active sessions for user
            active_sessions = self.session_repository.get_user_sessions(user_id, "active")
            paused_sessions = self.session_repository.get_user_sessions(user_id, "paused")

            all_sessions = active_sessions + paused_sessions
            conflicts = []

            for session in all_sessions:
                # Check for sessions that haven't synced recently
                if session.last_sync_at:
                    time_since_sync = datetime.utcnow() - session.last_sync_at
                    if time_since_sync > timedelta(minutes=5):  # 5 minutes threshold
                        conflicts.append({
                            "session_id": session.session_id,
                            "game_id": session.game_id,
                            "last_sync_minutes_ago": int(time_since_sync.total_seconds() / 60),
                            "device_info": session.device_info,
                            "status": session.status
                        })

            result = {
                "conflicts_count": len(conflicts),
                "conflicts": conflicts,
                "total_active_sessions": len(all_sessions)
            }

            if conflicts:
                self._get_logger().warning(f"Found {len(conflicts)} potential sync conflicts for user {user_id}")
                return True, "SYNC_CONFLICTS_DETECTED", result
            else:
                return True, "NO_SYNC_CONFLICTS", result

        except Exception as e:
            self._get_logger().error(f"Failed to check sync conflicts for user {user_id}: {str(e)}")
            return False, "SYNC_CONFLICT_CHECK_FAILED", None

    def _get_device_specific_data(self, session: GameSession, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get device-specific optimizations for the session data"""
        device_type = device_info.get("type", "unknown")

        optimizations = {}

        if device_type == "mobile":
            # Optimize for mobile devices
            optimizations["reduce_state_size"] = True
            optimizations["compress_moves"] = True

        elif device_type == "web":
            # Web-specific optimizations
            optimizations["include_debug_info"] = True

        return {
            "device_type": device_type,
            "optimizations": optimizations,
            "recommended_sync_interval": self._get_recommended_sync_interval(device_type)
        }

    def _get_recommended_sync_interval(self, device_type: str) -> int:
        """Get recommended sync interval in seconds based on device type"""
        intervals = {
            "mobile": 30,  # More frequent for mobile due to connectivity issues
            "web": 60,     # Standard interval for web
            "desktop": 90, # Less frequent for stable desktop connections
        }
        return intervals.get(device_type, 60)

    def _merge_session_states(self, server_session: GameSession, device_state: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently merge server and device session states"""
        # Use the higher score
        final_score = max(
            server_session.score or 0,
            device_state.get("score", 0) or 0
        )

        # Use the longer play duration
        final_duration = max(
            server_session.play_duration,
            device_state.get("play_duration_ms", 0)
        )

        # Merge achievements (union)
        server_achievements = set(server_session.achievements_unlocked)
        device_achievements = set(device_state.get("new_achievements", []))
        merged_achievements = list(server_achievements.union(device_achievements))

        # Merge moves (combine and sort by timestamp)
        all_moves = server_session.moves.copy()
        if "new_moves" in device_state:
            all_moves.extend(device_state["new_moves"])

        # Sort moves by timestamp
        all_moves.sort(key=lambda x: x.get("timestamp", datetime.min))

        # Update session
        server_session.score = final_score
        server_session.play_duration = final_duration
        server_session.achievements_unlocked = merged_achievements
        server_session.moves = all_moves
        server_session.moves_count = len(all_moves)

        # Merge statistics
        if "statistics" in device_state:
            merged_stats = server_session.statistics.copy()
            merged_stats.update(device_state["statistics"])
            server_session.statistics = merged_stats

        # Use the most recent state
        if "current_state" in device_state:
            server_session.current_state = device_state["current_state"]

        server_session.update_sync_info()
        self.session_repository.update_session(server_session.session_id, server_session)

        return {
            "session": server_session.to_api_dict(),
            "resolution": "merge",
            "merge_summary": {
                "score_source": "max",
                "duration_source": "max",
                "achievements_merged": len(merged_achievements),
                "moves_merged": len(all_moves)
            }
        }