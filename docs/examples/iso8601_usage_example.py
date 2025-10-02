"""
ISO 8601 DateTime Serialization - Practical Usage Examples

This file demonstrates how to properly use ISO 8601 datetime serialization
across models, services, and controllers.
"""
from datetime import datetime, timezone
from flask import Blueprint, request
from app.core.utils.json_encoder import serialize_model_dates, serialize_datetime
from app.core.utils.responses import success_response, error_response
from app.core.models.base_model import BaseModel


# ============================================================================
# EXAMPLE 1: Model with ISO 8601 Serialization
# ============================================================================

class GameSession(BaseModel):
    """Example game session model with proper datetime serialization"""

    def __init__(self, user_id, game_id, score=0):
        self.user_id = user_id
        self.game_id = game_id
        self.score = score
        self.started_at = datetime.now(timezone.utc)
        self.ended_at = None
        self.last_updated = datetime.now(timezone.utc)

    def end_session(self):
        """Mark session as ended"""
        self.ended_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)

    def to_dict(self):
        """
        Convert model to dictionary with ISO 8601 datetime serialization.

        ✅ CORRECT APPROACH: Use serialize_dates() from BaseModel
        """
        data = {
            "user_id": self.user_id,
            "game_id": self.game_id,
            "score": self.score,
            "started_at": self.started_at,  # datetime object
            "ended_at": self.ended_at,      # datetime object or None
            "last_updated": self.last_updated  # datetime object
        }
        # Automatically converts all datetime fields to ISO 8601
        return self.serialize_dates(data)


# ============================================================================
# EXAMPLE 2: Alternative Model (without BaseModel)
# ============================================================================

class Achievement:
    """Example achievement model using manual serialization"""

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.unlocked_at = datetime.now(timezone.utc)
        self.progress_milestones = [
            {"reached_at": datetime.now(timezone.utc), "level": 1}
        ]

    def to_dict(self):
        """
        ✅ CORRECT APPROACH: Use serialize_model_dates() for manual serialization
        """
        data = {
            "title": self.title,
            "description": self.description,
            "unlocked_at": self.unlocked_at,
            "progress_milestones": self.progress_milestones  # List with nested dates
        }
        # Recursively serializes all datetime fields (including nested)
        return serialize_model_dates(data)


# ============================================================================
# EXAMPLE 3: Service Layer
# ============================================================================

class GameSessionService:
    """Example service with datetime handling"""

    def create_session(self, user_id, game_id):
        """
        Create a new game session.

        ✅ CORRECT: Return datetime objects from service layer.
        The controller will handle serialization via success_response()
        """
        session = GameSession(user_id=user_id, game_id=game_id)

        # Service returns data with datetime objects
        return True, "SESSION_CREATED", {
            "session_id": "12345",
            "started_at": session.started_at,  # datetime object
            "status": "active"
        }

    def end_session(self, session_id):
        """
        End a game session.

        ✅ CORRECT: Service layer works with datetime objects.
        """
        session = GameSession(user_id="user123", game_id="game456")
        session.end_session()

        return True, "SESSION_ENDED", {
            "session_id": session_id,
            "started_at": session.started_at,  # datetime object
            "ended_at": session.ended_at,      # datetime object
            "duration_seconds": 3600
        }


# ============================================================================
# EXAMPLE 4: Controller Layer
# ============================================================================

game_session_bp = Blueprint('game_sessions', __name__)
game_session_service = GameSessionService()


@game_session_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new game session.

    ✅ CORRECT: Use success_response() which automatically serializes dates
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        user_id = data.get('user_id')
        game_id = data.get('game_id')

        success, message, result = game_session_service.create_session(
            user_id, game_id
        )

        if success:
            # success_response() automatically serializes all datetime fields
            # Result will have ISO 8601 formatted dates
            return success_response(message, result, 201)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@game_session_bp.route('/sessions/<session_id>/end', methods=['PUT'])
def end_session(session_id):
    """
    End a game session.

    ✅ CORRECT: Automatic datetime serialization via success_response()
    """
    try:
        success, message, result = game_session_service.end_session(session_id)

        if success:
            # All datetime fields in result will be ISO 8601 formatted
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# ============================================================================
# EXAMPLE 5: Complex Nested Data
# ============================================================================

def get_user_statistics():
    """
    Example with complex nested data containing multiple datetime fields.

    ✅ CORRECT: serialize_model_dates() handles nested structures
    """
    stats = {
        "user_id": "user123",
        "overall_stats": {
            "first_game": datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            "last_game": datetime.now(timezone.utc),
            "total_sessions": 150
        },
        "recent_sessions": [
            {
                "game_id": "game1",
                "started_at": datetime(2025, 10, 1, 9, 0, 0, tzinfo=timezone.utc),
                "ended_at": datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
            },
            {
                "game_id": "game2",
                "started_at": datetime(2025, 10, 2, 9, 0, 0, tzinfo=timezone.utc),
                "ended_at": datetime(2025, 10, 2, 11, 0, 0, tzinfo=timezone.utc)
            }
        ],
        "achievements": {
            "latest_unlock": datetime(2025, 10, 2, 8, 0, 0, tzinfo=timezone.utc)
        }
    }

    # Recursively serializes ALL datetime fields, including deeply nested ones
    return serialize_model_dates(stats)


# ============================================================================
# EXAMPLE 6: What NOT to Do
# ============================================================================

# ❌ WRONG: Manual string conversion
def wrong_approach_manual_formatting():
    session = GameSession(user_id="user123", game_id="game456")

    # DON'T DO THIS - Manual datetime to string conversion
    return {
        "started_at": session.started_at.strftime("%Y-%m-%d %H:%M:%S"),  # WRONG
        "ended_at": str(session.ended_at)  # WRONG
    }


# ❌ WRONG: Missing serialization in to_dict()
class BadModel:
    def __init__(self):
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        # WRONG - Returns datetime object without serialization
        return {
            "created_at": self.created_at  # Will be in HTTP date format!
        }


# ❌ WRONG: Using naive datetime (no timezone)
def wrong_approach_naive_datetime():
    # WRONG - Creates naive datetime without timezone
    session_start = datetime.now()  # Missing timezone!

    # Should be:
    session_start = datetime.now(timezone.utc)  # CORRECT


# ============================================================================
# EXAMPLE 7: Testing ISO 8601 Format
# ============================================================================

def test_iso8601_format():
    """
    Example test to verify ISO 8601 format in responses.
    """
    import re

    session = GameSession(user_id="user123", game_id="game456")
    data = session.to_dict()

    # ISO 8601 format pattern: YYYY-MM-DDTHH:MM:SS.ffffff+TZ
    iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}$'

    assert isinstance(data["started_at"], str), "started_at should be string"
    assert re.match(iso8601_pattern, data["started_at"]), "Should match ISO 8601"
    assert "T" in data["started_at"], "Should contain T separator"
    assert "+" in data["started_at"], "Should contain timezone offset"

    print(f"✅ Valid ISO 8601 format: {data['started_at']}")


# ============================================================================
# EXAMPLE 8: API Response Example
# ============================================================================

"""
Example API Response with ISO 8601 dates:

POST /api/sessions

Request:
{
  "user_id": "user123",
  "game_id": "game456"
}

Response (200 OK):
{
  "success": true,
  "message": "SESSION_CREATED",
  "data": {
    "session_id": "12345",
    "started_at": "2025-10-02T09:36:40.123456+00:00",  ✅ ISO 8601
    "status": "active"
  }
}

Frontend Usage (JavaScript):
const response = await fetch('/api/sessions', {
  method: 'POST',
  body: JSON.stringify({ user_id: 'user123', game_id: 'game456' })
});
const json = await response.json();

// Convert ISO 8601 string to Date object
const startedAt = new Date(json.data.started_at);
console.log(startedAt); // Date object
"""


# ============================================================================
# SUMMARY OF BEST PRACTICES
# ============================================================================

"""
✅ DO:
1. Extend BaseModel and use serialize_dates() in to_dict()
2. Use serialize_model_dates() for manual serialization
3. Always use timezone-aware datetime: datetime.now(timezone.utc)
4. Use success_response() and error_response() in controllers
5. Return datetime objects from service layer
6. Test that API responses contain ISO 8601 formatted dates

❌ DON'T:
1. Manually convert datetime to string with strftime() or str()
2. Forget to call serialize_dates() in to_dict()
3. Use naive datetime without timezone
4. Create custom date formatters
5. Skip serialization and return raw datetime objects from to_dict()

📚 References:
- See docs/ISO8601_SERIALIZATION.md for complete guide
- Run tests/test_iso8601_serialization.py for examples
- Check app/core/models/user.py for working implementation
"""

if __name__ == "__main__":
    # Run examples
    print("=" * 70)
    print("ISO 8601 Serialization Examples")
    print("=" * 70)

    # Example 1: Model serialization
    print("\n1. GameSession Model:")
    session = GameSession(user_id="user123", game_id="game456", score=1500)
    print(session.to_dict())

    # Example 2: Achievement serialization
    print("\n2. Achievement Model:")
    achievement = Achievement("First Win", "Win your first game")
    print(achievement.to_dict())

    # Example 3: Complex nested data
    print("\n3. Complex Nested Data:")
    print(get_user_statistics())

    # Example 4: Test ISO 8601 format
    print("\n4. ISO 8601 Format Validation:")
    test_iso8601_format()

    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
