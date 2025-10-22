"""
Game Constants Module

Contains all constant strings used in game data that will be translated by the UI.
ALL user-facing text in game models must use these constants.

Usage:
    from app.games.constants.game_constants import GAME_TIC_TAC_TOE_NAME
"""

# ============================================================
# GAME NAMES - Used in Game.name field
# ============================================================

GAME_TIC_TAC_TOE_NAME = "TIC_TAC_TOE"
GAME_MEMORY_NAME = "MEMORY_GAME"
GAME_PUZZLE_NAME = "PUZZLE_GAME"
GAME_QUIZ_NAME = "QUIZ_GAME"

# ============================================================
# GAME DESCRIPTIONS - Used in Game.description field
# ============================================================

GAME_TIC_TAC_TOE_DESC = "TIC_TAC_TOE_DESCRIPTION"
GAME_MEMORY_DESC = "MEMORY_GAME_DESCRIPTION"
GAME_PUZZLE_DESC = "PUZZLE_GAME_DESCRIPTION"
GAME_QUIZ_DESC = "QUIZ_GAME_DESCRIPTION"

# ============================================================
# GAME INSTRUCTIONS - Used in Game.instructions field
# ============================================================

GAME_TIC_TAC_TOE_INSTRUCTIONS = "TIC_TAC_TOE_INSTRUCTIONS"
GAME_MEMORY_INSTRUCTIONS = "MEMORY_GAME_INSTRUCTIONS"
GAME_PUZZLE_INSTRUCTIONS = "PUZZLE_GAME_INSTRUCTIONS"
GAME_QUIZ_INSTRUCTIONS = "QUIZ_GAME_INSTRUCTIONS"

# ============================================================
# CATEGORIES - Fixed values, not translated
# ============================================================

CATEGORY_STRATEGY = "strategy"
CATEGORY_PUZZLE = "puzzle"
CATEGORY_ARCADE = "arcade"
CATEGORY_CASUAL = "casual"
CATEGORY_EDUCATIONAL = "educational"

# ============================================================
# DIFFICULTY LEVELS - Fixed values, not translated
# ============================================================

DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

# ============================================================
# SEED DATA CONSTANTS - For initial game data
# ============================================================

TIC_TAC_TOE_SEED_DATA = {
    "name": GAME_TIC_TAC_TOE_NAME,
    "description": GAME_TIC_TAC_TOE_DESC,
    "category": CATEGORY_STRATEGY,
    "version": "1.0.0",
    "plugin_id": "tic_tac_toe",
    "min_players": 2,
    "max_players": 2,
    "is_active": True,
    "credit_rate": 1.0,
    "difficulty_level": DIFFICULTY_EASY,
    "estimated_duration_minutes": 5,
    "requires_internet": False,
    "instructions": GAME_TIC_TAC_TOE_INSTRUCTIONS,
    "author": "GoodPlay Team"
}

# ============================================================
# UI TRANSLATION MAPPING (for reference/documentation)
# ============================================================

"""
Expected UI translations (example for Italian):

TIC_TAC_TOE = "Tris"
TIC_TAC_TOE_DESCRIPTION = "Classico gioco di strategia su griglia 3x3 - allinea tre simboli per vincere"
TIC_TAC_TOE_INSTRUCTIONS = "A turno, piazza il tuo simbolo (X o O) in una cella vuota. Vince chi allinea tre simboli in orizzontale, verticale o diagonale."

MEMORY_GAME = "Gioco di Memoria"
MEMORY_GAME_DESCRIPTION = "Trova le coppie di carte uguali girando le carte"
MEMORY_GAME_INSTRUCTIONS = "Gira due carte alla volta. Se sono uguali, restano scoperte. Vince chi trova più coppie."

PUZZLE_GAME = "Puzzle"
PUZZLE_GAME_DESCRIPTION = "Risolvi il puzzle spostando i pezzi"
PUZZLE_GAME_INSTRUCTIONS = "Sposta i pezzi per completare l'immagine."

QUIZ_GAME = "Quiz"
QUIZ_GAME_DESCRIPTION = "Rispondi alle domande per guadagnare punti"
QUIZ_GAME_INSTRUCTIONS = "Scegli la risposta corretta tra le opzioni disponibili."
"""
