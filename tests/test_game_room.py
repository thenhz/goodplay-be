"""
Tests for GameRoom model and room code generation.
"""
import pytest
import re
from app.games.multiplayer.models.game_room import GameRoom


class TestGameRoomCodeGeneration:
    """Tests for room code generation with ambiguity-free characters"""

    def test_room_code_format(self):
        """Test that generated room code uses only allowed characters [A-HJ-NP-Z2-9]"""
        room = GameRoom(
            room_id="test_room_id",
            game_id="test_game",
            host_user_id="test_user"
        )

        # Verify room code exists and is 6 characters
        assert room.room_code is not None
        assert len(room.room_code) == 6

        # Verify room code contains only allowed characters (no 0, 1, I, O)
        allowed_pattern = re.compile(r'^[A-HJ-NP-Z2-9]{6}$')
        assert allowed_pattern.match(room.room_code), \
            f"Room code '{room.room_code}' contains invalid characters"

    def test_room_code_no_ambiguous_characters(self):
        """Test that room code never contains ambiguous characters"""
        # Generate multiple room codes to test randomness
        ambiguous_chars = {'0', '1', 'I', 'O'}

        for _ in range(100):
            room = GameRoom(
                room_id=f"test_room_{_}",
                game_id="test_game",
                host_user_id="test_user"
            )

            # Ensure no ambiguous characters in room code
            for char in room.room_code:
                assert char not in ambiguous_chars, \
                    f"Room code '{room.room_code}' contains ambiguous character '{char}'"

    def test_room_code_custom_value(self):
        """Test that custom room codes can be provided"""
        custom_code = "ABCD23"
        room = GameRoom(
            room_id="test_room_id",
            game_id="test_game",
            host_user_id="test_user",
            room_code=custom_code
        )

        assert room.room_code == custom_code

    def test_room_code_uniqueness(self):
        """Test that generated room codes are reasonably unique"""
        codes = set()
        iterations = 100

        for i in range(iterations):
            room = GameRoom(
                room_id=f"test_room_{i}",
                game_id="test_game",
                host_user_id="test_user"
            )
            codes.add(room.room_code)

        # Should have very high uniqueness (allow for rare collisions)
        uniqueness_ratio = len(codes) / iterations
        assert uniqueness_ratio > 0.95, \
            f"Room code uniqueness too low: {uniqueness_ratio:.2%} (expected > 95%)"
