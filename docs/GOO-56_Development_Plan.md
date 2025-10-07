# GOO-56: Sistema Room Management e Lobby Multiplayer
## Detailed Development Plan

---

## 📋 Executive Summary

**Card ID**: GOO-56
**Priority**: High
**Milestone**: Milestone 2 - "Room & Lobby System" (Week 2)
**Dependencies**: GOO-54 ✅, GOO-55 ✅
**Frontend Card**: GOOUI-40 (updated with API specifications)
**Estimated Duration**: 6 days

### Current Status Analysis
The multiplayer infrastructure is **already 80% implemented**:
- ✅ WebSocket server with Flask-SocketIO (GOO-54)
- ✅ JWT authentication on WebSocket (GOO-55)
- ✅ Basic GameRoom model with room codes
- ✅ RoomManager service with CRUD operations
- ✅ REST API endpoints for room management
- ✅ WebSocket events for join/leave
- ✅ Room repository with MongoDB persistence

### What's Missing (20% Remaining Work)
- ❌ Advanced room privacy settings and metadata
- ❌ Player ready state system
- ❌ Room search and filtering capabilities
- ❌ Enhanced lobby listing with real-time updates
- ❌ Room invitation system
- ❌ Spectator mode support
- ❌ Comprehensive testing for new features
- ❌ OpenAPI documentation updates
- ❌ Postman collection updates

---

## 🎯 Objectives

1. **Enhance Room Model** - Add privacy, metadata, and player ready states
2. **Implement Lobby System** - Real-time room discovery and filtering
3. **Add Player Ready System** - Ready state management with auto-start
4. **Create Room Invitations** - Invite system for private rooms
5. **Add Spectator Mode** - Observer functionality for rooms
6. **Comprehensive Testing** - 90%+ test coverage
7. **Complete Documentation** - OpenAPI specs and Postman collections

---

## 🏗️ Technical Architecture

### Current Structure
```
app/games/multiplayer/
├── models/
│   ├── game_room.py              ✅ EXISTS - needs enhancement
│   ├── multiplayer_session.py    ✅ EXISTS
│   └── player_state.py            ✅ EXISTS
├── repositories/
│   ├── room_repository.py         ✅ EXISTS - needs enhancement
│   ├── multiplayer_session_repository.py  ✅ EXISTS
│   └── player_state_repository.py ✅ EXISTS
├── services/
│   ├── room_manager.py            ✅ EXISTS - needs enhancement
│   ├── connection_manager.py      ✅ EXISTS
│   └── state_manager.py           ✅ EXISTS
├── controllers/
│   ├── multiplayer_controller.py  ✅ EXISTS - needs enhancement
│   └── auth_controller.py         ✅ EXISTS
└── events/
    ├── connection_events.py       ✅ EXISTS - needs enhancement
    ├── base_handler.py            ✅ EXISTS
    └── decorators.py              ✅ EXISTS
```

### New Files to Create
```
app/games/multiplayer/
├── models/
│   └── room_invitation.py         ⭐ NEW
├── repositories/
│   └── invitation_repository.py   ⭐ NEW
└── services/
    ├── lobby_service.py            ⭐ NEW
    └── invitation_service.py       ⭐ NEW
```

---

## 📝 Detailed Implementation Tasks

### Task 1: Enhance GameRoom Model
**File**: `app/games/multiplayer/models/game_room.py`
**Estimated Time**: 2 hours

#### Changes Required:
1. Add new fields:
   ```python
   # Privacy settings
   privacy: str = 'public'  # public|private|friends_only
   password: Optional[str] = None

   # Room metadata
   room_name: Optional[str] = None
   description: Optional[str] = None
   tags: List[str] = []

   # Player ready states
   player_ready_states: Dict[str, bool] = {}  # {user_id: is_ready}

   # Spectator mode
   spectator_ids: List[str] = []
   allow_spectators: bool = False
   max_spectators: int = 10

   # Auto-start settings
   auto_start_when_ready: bool = False
   auto_start_timer: Optional[int] = None  # seconds
   ```

2. Add new methods:
   ```python
   def set_player_ready(self, user_id: str, is_ready: bool) -> bool
   def all_players_ready(self) -> bool
   def add_spectator(self, user_id: str) -> bool
   def remove_spectator(self, user_id: str) -> bool
   def can_spectate(self, user_id: str) -> bool
   def is_private(self) -> bool
   def validate_password(self, password: str) -> bool
   ```

3. Update `to_dict()` method to include new fields
4. Update `from_dict()` method to parse new fields
5. Add validation for privacy settings

**Testing**:
- Unit tests for all new methods
- Test ready state transitions
- Test spectator management
- Test privacy validation

---

### Task 2: Create Room Invitation Model
**File**: `app/games/multiplayer/models/room_invitation.py` ⭐ NEW
**Estimated Time**: 1 hour

#### Implementation:
```python
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from app.core.utils.json_encoder import serialize_model_dates

class RoomInvitation:
    """
    Model for room invitations.

    Attributes:
        invitation_id: Unique invitation identifier
        room_id: ID of the room
        sender_user_id: ID of user sending invitation
        recipient_user_id: ID of user receiving invitation
        status: pending|accepted|declined|expired
        created_at: Invitation creation timestamp
        expires_at: Invitation expiry timestamp
        accepted_at: Acceptance timestamp
        metadata: Additional invitation data
    """

    COLLECTION_NAME = 'room_invitations'

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_EXPIRED = 'expired'

    def __init__(
        self,
        invitation_id: str,
        room_id: str,
        sender_user_id: str,
        recipient_user_id: str,
        status: str = STATUS_PENDING,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        accepted_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.invitation_id = invitation_id
        self.room_id = room_id
        self.sender_user_id = sender_user_id
        self.recipient_user_id = recipient_user_id
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at or (self.created_at + timedelta(hours=24))
        self.accepted_at = accepted_at
        self.metadata = metadata or {}

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def can_accept(self) -> bool:
        return self.status == self.STATUS_PENDING and not self.is_expired()

    def accept(self) -> bool:
        if self.can_accept():
            self.status = self.STATUS_ACCEPTED
            self.accepted_at = datetime.now(timezone.utc)
            return True
        return False

    def decline(self) -> bool:
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_DECLINED
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        invitation_dict = {
            'invitation_id': self.invitation_id,
            'room_id': self.room_id,
            'sender_user_id': self.sender_user_id,
            'recipient_user_id': self.recipient_user_id,
            'status': self.status,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'accepted_at': self.accepted_at,
            'metadata': self.metadata
        }
        return serialize_model_dates(invitation_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'RoomInvitation':
        return RoomInvitation(
            invitation_id=data['invitation_id'],
            room_id=data['room_id'],
            sender_user_id=data['sender_user_id'],
            recipient_user_id=data['recipient_user_id'],
            status=data.get('status', RoomInvitation.STATUS_PENDING),
            created_at=data.get('created_at'),
            expires_at=data.get('expires_at'),
            accepted_at=data.get('accepted_at'),
            metadata=data.get('metadata', {})
        )
```

**Testing**:
- Unit tests for invitation lifecycle
- Test expiry logic
- Test accept/decline transitions

---

### Task 3: Enhance Room Repository
**File**: `app/games/multiplayer/repositories/room_repository.py`
**Estimated Time**: 3 hours

#### New Methods to Add:
```python
def search_rooms(
    self,
    game_id: Optional[str] = None,
    privacy: Optional[str] = None,
    min_players: Optional[int] = None,
    max_players: Optional[int] = None,
    tags: Optional[List[str]] = None,
    search_query: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[GameRoom], int]:
    """Advanced room search with filters and pagination"""

def update_player_ready_state(
    self,
    room_id: str,
    user_id: str,
    is_ready: bool
) -> bool:
    """Update player ready state"""

def add_spectator(self, room_id: str, user_id: str) -> bool:
    """Add spectator to room"""

def remove_spectator(self, room_id: str, user_id: str) -> bool:
    """Remove spectator from room"""

def get_rooms_by_tag(self, tag: str, limit: int = 20) -> List[GameRoom]:
    """Find rooms by tag"""

def get_user_hosted_rooms(self, user_id: str) -> List[GameRoom]:
    """Get rooms hosted by user"""

def update_room_settings(
    self,
    room_id: str,
    settings: Dict[str, Any]
) -> bool:
    """Update room configuration settings"""
```

#### New Indexes to Create:
```python
def create_indexes(self):
    # Existing indexes...

    # New indexes for GOO-56
    self.collection.create_index('privacy')
    self.collection.create_index('tags')
    self.collection.create_index([('game_id', 1), ('privacy', 1), ('status', 1)])
    self.collection.create_index([('status', 1), ('created_at', -1)])
    self.collection.create_index('player_ready_states')
```

**Testing**:
- Test search with multiple filters
- Test pagination
- Test ready state updates
- Test spectator management
- Verify index performance

---

### Task 4: Create Invitation Repository
**File**: `app/games/multiplayer/repositories/invitation_repository.py` ⭐ NEW
**Estimated Time**: 2 hours

#### Implementation:
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.shared.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.room_invitation import RoomInvitation

class InvitationRepository(BaseRepository):
    """Repository for room invitation operations"""

    def __init__(self):
        super().__init__(RoomInvitation.COLLECTION_NAME)

    def create_indexes(self):
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        self.collection.create_index('invitation_id', unique=True)
        self.collection.create_index('room_id')
        self.collection.create_index('sender_user_id')
        self.collection.create_index('recipient_user_id')
        self.collection.create_index([('recipient_user_id', 1), ('status', 1)])
        self.collection.create_index('expires_at')
        self.collection.create_index('created_at')

    def create_invitation(self, invitation: RoomInvitation) -> bool:
        """Create new invitation"""

    def get_invitation(self, invitation_id: str) -> Optional[RoomInvitation]:
        """Get invitation by ID"""

    def get_user_invitations(
        self,
        user_id: str,
        status: Optional[str] = None,
        include_expired: bool = False
    ) -> List[RoomInvitation]:
        """Get invitations for user"""

    def update_invitation_status(
        self,
        invitation_id: str,
        status: str
    ) -> bool:
        """Update invitation status"""

    def get_room_invitations(self, room_id: str) -> List[RoomInvitation]:
        """Get all invitations for room"""

    def cleanup_expired_invitations(self) -> int:
        """Remove expired invitations"""
```

**Testing**:
- Test invitation CRUD operations
- Test user invitation queries
- Test expiry cleanup

---

### Task 5: Create Lobby Service
**File**: `app/games/multiplayer/services/lobby_service.py` ⭐ NEW
**Estimated Time**: 3 hours

#### Implementation:
```python
from typing import Optional, Dict, List, Any, Tuple
from flask import current_app
from app.games.multiplayer.repositories.room_repository import RoomRepository
from app.games.multiplayer.models.game_room import GameRoom

class LobbyService:
    """
    Service for lobby and room discovery.

    Handles:
    - Room browsing and filtering
    - Quick match functionality
    - Room recommendations
    - Lobby statistics
    """

    def __init__(self):
        self.room_repository = RoomRepository()

    def browse_rooms(
        self,
        game_id: Optional[str] = None,
        privacy: str = 'public',
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Browse available rooms with filters"""

    def quick_match(
        self,
        user_id: str,
        game_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """Find and join best available room for quick match"""

    def get_recommended_rooms(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[GameRoom]:
        """Get recommended rooms based on user preferences"""

    def get_lobby_statistics(
        self,
        game_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get lobby statistics"""
```

**Testing**:
- Test room browsing with filters
- Test quick match algorithm
- Test room recommendations
- Test statistics calculation

---

### Task 6: Create Invitation Service
**File**: `app/games/multiplayer/services/invitation_service.py` ⭐ NEW
**Estimated Time**: 2 hours

#### Implementation:
```python
import uuid
from typing import Tuple, Optional, List
from flask import current_app
from app.games.multiplayer.models.room_invitation import RoomInvitation
from app.games.multiplayer.repositories.invitation_repository import InvitationRepository
from app.games.multiplayer.repositories.room_repository import RoomRepository

class InvitationService:
    """Service for managing room invitations"""

    def __init__(self):
        self.invitation_repository = InvitationRepository()
        self.room_repository = RoomRepository()

    def send_invitation(
        self,
        room_id: str,
        sender_user_id: str,
        recipient_user_id: str
    ) -> Tuple[bool, str, Optional[RoomInvitation]]:
        """Send room invitation"""

    def accept_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Accept invitation and return room_id"""

    def decline_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """Decline invitation"""

    def get_user_invitations(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> List[RoomInvitation]:
        """Get user's pending invitations"""

    def cleanup_expired(self) -> int:
        """Cleanup expired invitations"""
```

**Testing**:
- Test invitation flow
- Test authorization checks
- Test expiry handling

---

### Task 7: Enhance Room Manager Service
**File**: `app/games/multiplayer/services/room_manager.py`
**Estimated Time**: 3 hours

#### New Methods to Add:
```python
def set_player_ready(
    self,
    room_id: str,
    user_id: str,
    is_ready: bool
) -> Tuple[bool, str, Optional[GameRoom]]:
    """Set player ready state"""

def update_room_settings(
    self,
    room_id: str,
    host_user_id: str,
    settings: Dict[str, Any]
) -> Tuple[bool, str, Optional[GameRoom]]:
    """Update room settings (host only)"""

def add_spectator(
    self,
    room_id: str,
    user_id: str
) -> Tuple[bool, str, Optional[GameRoom]]:
    """Add spectator to room"""

def remove_spectator(
    self,
    room_id: str,
    user_id: str
) -> Tuple[bool, str]:
    """Remove spectator from room"""

def check_auto_start(
    self,
    room_id: str
) -> Tuple[bool, str]:
    """Check if room should auto-start"""
```

**Testing**:
- Test ready state management
- Test auto-start logic
- Test spectator operations
- Test settings updates

---

### Task 8: Enhance Multiplayer Controller
**File**: `app/games/multiplayer/controllers/multiplayer_controller.py`
**Estimated Time**: 3 hours

#### New Endpoints to Add:

1. **POST /api/multiplayer/rooms/search** - Advanced room search
2. **POST /api/multiplayer/rooms/{room_id}/ready** - Toggle ready state
3. **PUT /api/multiplayer/rooms/{room_id}/settings** - Update settings
4. **POST /api/multiplayer/rooms/{room_id}/spectate** - Join as spectator
5. **POST /api/multiplayer/rooms/{room_id}/invitations** - Send invitation
6. **GET /api/multiplayer/invitations** - Get user invitations
7. **POST /api/multiplayer/invitations/{invitation_id}/accept** - Accept invitation
8. **POST /api/multiplayer/invitations/{invitation_id}/decline** - Decline invitation
9. **POST /api/multiplayer/quick-match** - Quick match functionality
10. **GET /api/multiplayer/lobby** - Get lobby data

**Testing**:
- Integration tests for all new endpoints
- Test authorization
- Test error handling

---

### Task 9: Enhance WebSocket Events
**File**: `app/games/multiplayer/events/connection_events.py`
**Estimated Time**: 2 hours

#### New Events to Add:

**Server → Room: `player_ready_changed`**
```python
@socketio.on('toggle_ready')
@authenticated
def handle_toggle_ready(data):
    """Handle player ready state change"""
    # Emit to room: player_ready_changed
```

**Server → Room: `room_settings_updated`**
```python
# When room settings change, broadcast to all players
```

**Server → Room: `spectator_joined`**
```python
# When spectator joins room
```

**Server → Room: `game_starting`**
```python
# When game is about to start (countdown)
```

**Server → User: `invitation_received`**
```python
# When user receives room invitation
```

**Testing**:
- Test WebSocket event broadcasting
- Test event authorization
- Test room-specific events

---

### Task 10: Update OpenAPI Documentation
**File**: `docs/openapi/games.yaml`
**Estimated Time**: 2 hours

#### Sections to Add:

1. Room search endpoint specification
2. Ready state endpoints
3. Room settings endpoints
4. Spectator endpoints
5. Invitation endpoints
6. Lobby endpoints
7. Quick match endpoint
8. All new response message constants
9. Updated room schema with new fields
10. Invitation schema

**New Message Constants**:
```yaml
- PLAYER_READY_UPDATED
- PLAYER_NOT_READY
- ALL_PLAYERS_READY
- ROOM_SETTINGS_UPDATED
- SETTINGS_UPDATE_FAILED
- NOT_ROOM_HOST
- SPECTATOR_JOINED
- SPECTATOR_LEFT
- SPECTATOR_LIMIT_REACHED
- SPECTATORS_NOT_ALLOWED
- INVITATION_SENT
- INVITATION_ACCEPTED
- INVITATION_DECLINED
- INVITATION_EXPIRED
- INVITATION_NOT_FOUND
- QUICK_MATCH_FOUND
- NO_ROOMS_AVAILABLE
- LOBBY_DATA_RETRIEVED
```

---

### Task 11: Update Postman Collection
**File**: `docs/postman/games_collection.json`
**Estimated Time**: 1 hour

#### Requests to Add:

1. Search Rooms (POST /api/multiplayer/rooms/search)
2. Toggle Ready (POST /api/multiplayer/rooms/{room_id}/ready)
3. Update Room Settings (PUT /api/multiplayer/rooms/{room_id}/settings)
4. Join as Spectator (POST /api/multiplayer/rooms/{room_id}/spectate)
5. Send Invitation (POST /api/multiplayer/rooms/{room_id}/invitations)
6. Get My Invitations (GET /api/multiplayer/invitations)
7. Accept Invitation (POST /api/multiplayer/invitations/{id}/accept)
8. Decline Invitation (POST /api/multiplayer/invitations/{id}/decline)
9. Quick Match (POST /api/multiplayer/quick-match)
10. Get Lobby Data (GET /api/multiplayer/lobby)

---

### Task 12: Comprehensive Testing
**File**: `tests/test_multiplayer_enhanced.py` ⭐ NEW
**Estimated Time**: 4 hours

#### Test Coverage:

**Unit Tests** (50+ tests):
- GameRoom model enhancements (15 tests)
- RoomInvitation model (10 tests)
- Room repository enhancements (20 tests)
- Invitation repository (10 tests)
- Lobby service (15 tests)
- Invitation service (10 tests)
- Room manager enhancements (15 tests)

**Integration Tests** (30+ tests):
- Room search and filtering (10 tests)
- Ready state system (8 tests)
- Spectator functionality (5 tests)
- Invitation flow (10 tests)
- Quick match (5 tests)
- Lobby browsing (5 tests)

**WebSocket Tests** (10+ tests):
- Ready state events (3 tests)
- Invitation events (3 tests)
- Spectator events (2 tests)
- Settings update events (2 tests)

**Target Coverage**: 90%+ for all new code

---

## 📊 Database Schema Changes

### game_rooms Collection (Enhanced)
```javascript
{
  // Existing fields...
  room_id: String (indexed),
  room_code: String (indexed, unique),
  game_id: String (indexed),
  host_user_id: String (indexed),
  player_ids: [String] (indexed),
  max_players: Number,
  status: String (indexed),
  created_at: Date (indexed),
  started_at: Date,
  finished_at: Date,
  game_config: Object,
  metadata: Object,

  // NEW FIELDS
  privacy: String (indexed),          // 'public'|'private'|'friends_only'
  password: String,                    // Hashed password for private rooms
  room_name: String,                   // Custom room name
  description: String,                 // Room description
  tags: [String] (indexed),           // Searchable tags
  player_ready_states: Object,         // {user_id: boolean}
  spectator_ids: [String],            // List of spectator user IDs
  allow_spectators: Boolean,           // Spectator mode enabled
  max_spectators: Number,              // Max spectator count
  auto_start_when_ready: Boolean,      // Auto-start when all ready
  auto_start_timer: Number             // Auto-start delay (seconds)
}
```

### room_invitations Collection (New)
```javascript
{
  invitation_id: String (indexed, unique),
  room_id: String (indexed),
  sender_user_id: String (indexed),
  recipient_user_id: String (indexed),
  status: String (indexed),         // 'pending'|'accepted'|'declined'|'expired'
  created_at: Date (indexed),
  expires_at: Date (indexed),
  accepted_at: Date,
  metadata: Object
}

// Compound Index
Index: {recipient_user_id: 1, status: 1}
```

---

## 🔧 Configuration Updates

### Environment Variables to Add
```env
# Room Management
MAX_ROOM_DESCRIPTION_LENGTH=500
ROOM_INVITE_EXPIRY_HOURS=24
AUTO_START_DELAY_SECONDS=5
SPECTATOR_MODE_ENABLED=true
MAX_SPECTATORS_PER_ROOM=10

# Lobby Settings
LOBBY_ROOMS_PER_PAGE=20
QUICK_MATCH_TIMEOUT_SECONDS=30
RECOMMENDED_ROOMS_COUNT=10

# Search Settings
MAX_SEARCH_RESULTS=100
```

---

## 🎨 Frontend Integration Guide

### REST API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/multiplayer/rooms` | Create room |
| GET | `/api/multiplayer/rooms/{room_id}` | Get room |
| GET | `/api/multiplayer/rooms/code/{code}` | Get room by code |
| POST | `/api/multiplayer/rooms/{room_id}/join` | Join room |
| POST | `/api/multiplayer/rooms/{room_id}/leave` | Leave room |
| POST | `/api/multiplayer/rooms/{room_id}/start` | Start game |
| GET | `/api/multiplayer/rooms/available` | Get available rooms |
| GET | `/api/multiplayer/rooms/my-rooms` | Get user's rooms |
| **POST** | **`/api/multiplayer/rooms/search`** | **⭐ Search rooms** |
| **POST** | **`/api/multiplayer/rooms/{room_id}/ready`** | **⭐ Toggle ready** |
| **PUT** | **`/api/multiplayer/rooms/{room_id}/settings`** | **⭐ Update settings** |
| **POST** | **`/api/multiplayer/rooms/{room_id}/spectate`** | **⭐ Join as spectator** |
| **POST** | **`/api/multiplayer/rooms/{room_id}/invitations`** | **⭐ Send invitation** |
| **GET** | **`/api/multiplayer/invitations`** | **⭐ Get invitations** |
| **POST** | **`/api/multiplayer/invitations/{id}/accept`** | **⭐ Accept invitation** |
| **POST** | **`/api/multiplayer/invitations/{id}/decline`** | **⭐ Decline invitation** |
| **POST** | **`/api/multiplayer/quick-match`** | **⭐ Quick match** |
| **GET** | **`/api/multiplayer/lobby`** | **⭐ Get lobby data** |

### WebSocket Events Summary

| Direction | Event | Description |
|-----------|-------|-------------|
| Client → Server | `authenticate` | Authenticate connection |
| Server → Client | `authenticated` | Auth success |
| Client → Server | `join_room` | Join room |
| Server → Client | `room_joined` | Join success |
| Server → Room | `player_joined` | Player joined |
| Client → Server | `leave_room` | Leave room |
| Server → Client | `room_left` | Leave success |
| Server → Room | `player_left` | Player left |
| Client → Server | `game_action` | Send action |
| Server → Room | `game_action` | Broadcast action |
| Client → Server | `update_state` | Update state |
| Server → Room | `state_updated` | Broadcast state |
| Client → Server | `ping` | Ping server |
| Server → Client | `pong` | Pong response |
| **Client → Server** | **`toggle_ready`** | **⭐ Toggle ready** |
| **Server → Room** | **`player_ready_changed`** | **⭐ Ready state changed** |
| **Server → Room** | **`room_settings_updated`** | **⭐ Settings changed** |
| **Server → Room** | **`spectator_joined`** | **⭐ Spectator joined** |
| **Server → Room** | **`spectator_left`** | **⭐ Spectator left** |
| **Server → Room** | **`game_starting`** | **⭐ Game starting** |
| **Server → User** | **`invitation_received`** | **⭐ Invitation received** |
| Server → Client | `error` | Error occurred |

### Key Frontend Integration Points

1. **Room Search Page**
   - Call: `POST /api/multiplayer/rooms/search`
   - Filters: game_id, privacy, tags, search_query
   - Pagination: page, per_page

2. **Lobby Page**
   - Listen to: `player_joined`, `player_left`, `player_ready_changed`
   - Display: Player list with ready states
   - Show: Ready count (e.g., "3/4 players ready")
   - Host controls: Settings button, Start button (disabled until all ready)

3. **Ready System**
   - Toggle via: `POST /api/multiplayer/rooms/{room_id}/ready`
   - Listen to: `player_ready_changed` WebSocket event
   - UI: Checkbox or button for each player
   - Auto-start: Show countdown when all ready

4. **Invitations**
   - Send: `POST /api/multiplayer/rooms/{room_id}/invitations`
   - Receive: Listen to `invitation_received` WebSocket event
   - List: `GET /api/multiplayer/invitations`
   - Accept: `POST /api/multiplayer/invitations/{id}/accept`
   - Show: Badge with invitation count

5. **Quick Match**
   - Call: `POST /api/multiplayer/quick-match`
   - Show: Loading spinner while searching
   - Timeout: 30 seconds max
   - Redirect: Auto-join found room

---

## ✅ Acceptance Criteria Checklist

### Room Management
- [x] Room creation with unique codes works *(already implemented)*
- [x] Players can join/leave rooms *(already implemented)*
- [x] Room capacity limits enforced *(already implemented)*
- [x] Host migration on host leave works *(already implemented)*
- [ ] Room privacy settings work (public/private/friends_only)
- [x] Public room listing works *(already implemented)*
- [x] Room cleanup for stale rooms *(already implemented)*
- [x] Game start validation works *(already implemented)*

### New Features (GOO-56)
- [ ] Player ready status tracking
- [ ] All players ready check before start
- [ ] Auto-start when all ready (optional)
- [ ] Room search with filters (game, privacy, tags)
- [ ] Room metadata (name, description, tags)
- [ ] Private room password protection
- [ ] Spectator mode functionality
- [ ] Room invitation system
- [ ] Quick match algorithm
- [ ] Enhanced lobby with real-time updates

### Quality & Documentation
- [ ] 90%+ test coverage for new features
- [ ] OpenAPI documentation updated
- [ ] Postman collection updated
- [ ] All response constants documented
- [ ] WebSocket events documented

---

## 📅 Development Timeline

### Day 1: Models & Repositories (6 hours)
- ✅ Morning (3h): Enhance GameRoom model
- ✅ Afternoon (3h): Create RoomInvitation model + Enhance Room Repository

### Day 2: Repositories & Services (6 hours)
- ✅ Morning (3h): Create Invitation Repository + Start Lobby Service
- ✅ Afternoon (3h): Complete Lobby Service + Invitation Service

### Day 3: Services & Controllers (6 hours)
- ✅ Morning (3h): Enhance Room Manager Service
- ✅ Afternoon (3h): Enhance Multiplayer Controller (part 1)

### Day 4: Controllers & WebSocket (6 hours)
- ✅ Morning (3h): Complete Controller enhancements
- ✅ Afternoon (3h): Enhance WebSocket events

### Day 5: Documentation (6 hours)
- ✅ Morning (3h): Update OpenAPI documentation
- ✅ Afternoon (3h): Update Postman collection

### Day 6: Testing (6 hours)
- ✅ Morning (3h): Write unit tests
- ✅ Afternoon (3h): Write integration + WebSocket tests

**Total Estimated Time**: 36 hours (6 working days)

---

## 🧪 Testing Strategy

### Unit Tests (50+ tests)
```bash
# Test new models
pytest tests/test_multiplayer_enhanced.py::TestGameRoomEnhancements -v
pytest tests/test_multiplayer_enhanced.py::TestRoomInvitation -v

# Test repositories
pytest tests/test_multiplayer_enhanced.py::TestRoomRepositoryEnhancements -v
pytest tests/test_multiplayer_enhanced.py::TestInvitationRepository -v

# Test services
pytest tests/test_multiplayer_enhanced.py::TestLobbyService -v
pytest tests/test_multiplayer_enhanced.py::TestInvitationService -v
pytest tests/test_multiplayer_enhanced.py::TestRoomManagerEnhancements -v
```

### Integration Tests (30+ tests)
```bash
# Test complete flows
pytest tests/test_multiplayer_enhanced.py::TestRoomSearchIntegration -v
pytest tests/test_multiplayer_enhanced.py::TestReadySystemIntegration -v
pytest tests/test_multiplayer_enhanced.py::TestInvitationFlowIntegration -v
pytest tests/test_multiplayer_enhanced.py::TestQuickMatchIntegration -v
```

### WebSocket Tests (10+ tests)
```bash
# Test WebSocket events
pytest tests/test_multiplayer_enhanced.py::TestWebSocketEvents -v
```

### Run All Tests
```bash
make test
make test-coverage  # Verify 90%+ coverage
```

---

## 🚨 Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing functionality | High | Comprehensive regression testing |
| WebSocket event conflicts | Medium | Careful event naming and documentation |
| Performance with many rooms | Medium | Proper indexing and pagination |
| Race conditions in ready states | Medium | Optimistic locking in repository |
| Invitation spam | Low | Rate limiting on invitation creation |

---

## 🔄 Migration Plan

### Database Migration Steps
1. **Phase 1**: Add new fields to existing rooms (default values)
2. **Phase 2**: Create room_invitations collection
3. **Phase 3**: Create new indexes
4. **Phase 4**: Backfill privacy='public' for existing rooms

### Migration Script
```python
# scripts/migrate_goo56.py
def migrate_rooms():
    """Add new fields to existing rooms"""
    db = get_db()
    db.game_rooms.update_many(
        {'privacy': {'$exists': False}},
        {'$set': {
            'privacy': 'public',
            'player_ready_states': {},
            'spectator_ids': [],
            'allow_spectators': False,
            'max_spectators': 10,
            'auto_start_when_ready': False,
            'tags': []
        }}
    )
```

---

## 📚 Reference Documentation

### Related Cards
- **GOO-54**: WebSocket Infrastructure (✅ Complete)
- **GOO-55**: JWT WebSocket Authentication (✅ Complete)
- **GOO-56**: Room Management & Lobby System (🚧 In Progress)
- **GOO-57**: Matchmaking Service (⏳ Next)
- **GOOUI-40**: Frontend Matchmaking & Lobby UI (⏳ Waiting for GOO-56)

### Key Files Reference
- Models: `app/games/multiplayer/models/`
- Repositories: `app/games/multiplayer/repositories/`
- Services: `app/games/multiplayer/services/`
- Controllers: `app/games/multiplayer/controllers/`
- Events: `app/games/multiplayer/events/`
- Tests: `tests/test_multiplayer_enhanced.py`
- Docs: `docs/openapi/games.yaml`, `docs/postman/games_collection.json`

### External Documentation
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [MongoDB Indexing Best Practices](https://docs.mongodb.com/manual/indexes/)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)

---

## 🎯 Success Metrics

### Technical Metrics
- ✅ 90%+ test coverage for new code
- ✅ All acceptance criteria met
- ✅ Zero breaking changes to existing APIs
- ✅ API response time < 200ms (95th percentile)
- ✅ WebSocket latency < 50ms

### Business Metrics
- 📊 Room creation rate
- 📊 Average players per room
- 📊 Quick match success rate
- 📊 Invitation acceptance rate
- 📊 Spectator engagement

---

## 📞 Support & Communication

### Questions or Issues?
- **Backend Lead**: Check with team lead for architectural decisions
- **Frontend Team**: GOOUI-40 card updated with all API specs
- **Testing Issues**: Refer to existing test patterns in `tests/`
- **Documentation**: This plan + OpenAPI specs + Postman collection

### Status Updates
- Daily standup: Report progress against timeline
- Blockers: Escalate immediately
- Completion: Update Linear card and notify frontend team

---

**Last Updated**: 2025-10-07
**Plan Version**: 1.0
**Status**: Ready for Implementation
**Estimated Completion**: Day 6 (6 working days)
