"""
Flow Tiles Message Constants

All message constants used in Flow Tiles game for UI translation.
"""

# ============================================================
# API Response Messages
# ============================================================

# Success messages
ACTION_PROCESSED = "ACTION_PROCESSED"
STATE_SYNCED = "STATE_SYNCED"
RESULT_SAVED = "RESULT_SAVED"
EVENTS_RETRIEVED = "EVENTS_RETRIEVED"
WEBSOCKET_TOKEN_GENERATED = "WEBSOCKET_TOKEN_GENERATED"
WEBSOCKET_TOKEN_REFRESHED = "WEBSOCKET_TOKEN_REFRESHED"

# Action validation messages
MOVE_VALID = "MOVE_VALID"
CONFIG_VALID = "CONFIG_VALID"

# Error messages
ACTION_REQUIRED = "ACTION_REQUIRED"
INDEX_REQUIRED = "INDEX_REQUIRED"
INVALID_ACTION_TYPE = "INVALID_ACTION_TYPE"
GAME_ALREADY_COMPLETE = "GAME_ALREADY_COMPLETE"
INVALID_TILE_INDEX = "INVALID_TILE_INDEX"
INDEX_OUT_OF_BOUNDS = "INDEX_OUT_OF_BOUNDS"
TILE_EMPTY = "TILE_EMPTY"
TILE_LOCKED = "TILE_LOCKED"
NOT_YOUR_TURN = "NOT_YOUR_TURN"
CANNOT_PLACE_IN_THIS_MODE = "CANNOT_PLACE_IN_THIS_MODE"
TILE_ALREADY_EXISTS = "TILE_ALREADY_EXISTS"
TILE_DATA_REQUIRED = "TILE_DATA_REQUIRED"
INVALID_GAME_MODE = "INVALID_GAME_MODE"
INVALID_GRID_SIZE = "INVALID_GRID_SIZE"
HARMONIC_MODE_REQUIRES_2_PLAYERS = "HARMONIC_MODE_REQUIRES_2_PLAYERS"
COLLABORATIVE_MODE_REQUIRES_2_TO_4_PLAYERS = "COLLABORATIVE_MODE_REQUIRES_2_TO_4_PLAYERS"

# General errors
DATA_REQUIRED = "DATA_REQUIRED"
ACTION_TYPE_AND_PAYLOAD_REQUIRED = "ACTION_TYPE_AND_PAYLOAD_REQUIRED"
ROOM_NOT_FOUND = "ROOM_NOT_FOUND"
NOT_IN_ROOM = "NOT_IN_ROOM"
GAME_STATE_REQUIRED = "GAME_STATE_REQUIRED"
RESULT_TYPE_REQUIRED = "RESULT_TYPE_REQUIRED"
ONLY_HOST_CAN_SUBMIT_RESULT = "ONLY_HOST_CAN_SUBMIT_RESULT"
ROOM_ID_REQUIRED = "ROOM_ID_REQUIRED"
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

# ============================================================
# WebSocket Event Messages
# ============================================================

ACTION_RECEIVED = "ACTION_RECEIVED"
INVALID_ACTION = "INVALID_ACTION"
GAME_STARTED = "GAME_STARTED"
GAME_ENDED = "GAME_ENDED"
STATE_SYNCHRONIZED = "STATE_SYNCHRONIZED"

# ============================================================
# Achievement Constants
# ============================================================

FLOW_TILES_COMPLETED = "FLOW_TILES_COMPLETED"
FLOW_MASTER = "FLOW_MASTER"
BEAUTY_ARTIST = "BEAUTY_ARTIST"
EFFICIENCY_EXPERT = "EFFICIENCY_EXPERT"
PERFECT_HARMONY = "PERFECT_HARMONY"

# ============================================================
# UI Translation Mapping (for reference/documentation)
# ============================================================

"""
Expected UI translations (example for Italian):

# Success Messages
ACTION_PROCESSED = "Azione elaborata con successo"
STATE_SYNCED = "Stato sincronizzato"
RESULT_SAVED = "Risultato salvato"

# Validation Errors
MOVE_VALID = "Mossa valida"
INVALID_ACTION_TYPE = "Tipo di azione non valido"
GAME_ALREADY_COMPLETE = "Partita già completata"
INVALID_TILE_INDEX = "Indice tessera non valido"
TILE_LOCKED = "Tessera bloccata"
NOT_YOUR_TURN = "Non è il tuo turno"
CANNOT_PLACE_IN_THIS_MODE = "Non puoi piazzare tessere in questa modalità"
TILE_ALREADY_EXISTS = "La tessera esiste già"

# Achievements
FLOW_TILES_COMPLETED = "Flow Tiles Completato"
FLOW_MASTER = "Maestro dei Flussi"
BEAUTY_ARTIST = "Artista della Bellezza"
EFFICIENCY_EXPERT = "Esperto di Efficienza"
PERFECT_HARMONY = "Armonia Perfetta"
"""
