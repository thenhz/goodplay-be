# Database Initialization Guide

## Overview

This guide explains how the GoodPlay database is initialized and how to populate it with test data.

## Automatic Initialization

### On Application Start

The database is **automatically initialized** when you start the Flask application:

```bash
python app.py
```

**What happens automatically:**

1. **MongoDB Connection**: Connects to MongoDB using `MONGO_URI` from `.env`
2. **Collections Created**: Collections are auto-created on first document insert
3. **Indexes Created**: All repository `create_indexes()` methods are called
4. **System Initialized**: Game modes, teams, and other system data

**Location:** `app/__init__.py` → `init_db()` function

### Collections Auto-Creation

MongoDB creates collections automatically when you insert the first document. **No manual CREATE TABLE statements needed.**

Expected collections:
- `users` - User accounts
- `games` - Game catalog
- `game_sessions` - Game play sessions
- `game_rooms` - Multiplayer rooms
- `multiplayer_sessions` - Multiplayer session state
- `player_states` - Player state in multiplayer
- `wallets` - Virtual wallets
- `transactions` - Financial transactions
- `onlus_organizations` - Verified charities
- `achievements` - User achievements
- `leaderboards` - Leaderboard data
- And many more...

---

## Game Constants System

### Why Constants?

All user-facing text uses **constants** instead of literal strings. The UI translates these at runtime based on user language preference.

**Example:**

```python
# In Database
{
  "name": "TIC_TAC_TOE",
  "description": "TIC_TAC_TOE_DESCRIPTION"
}

# UI Translation (Italian)
TIC_TAC_TOE = "Tris"
TIC_TAC_TOE_DESCRIPTION = "Classico gioco di strategia su griglia 3x3"

# UI Translation (English)
TIC_TAC_TOE = "Tic Tac Toe"
TIC_TAC_TOE_DESCRIPTION = "Classic 3x3 grid strategy game"
```

### Available Constants

**Location:** `app/games/constants/game_constants.py`

```python
from app.games.constants import (
    GAME_TIC_TAC_TOE_NAME,
    GAME_TIC_TAC_TOE_DESC,
    TIC_TAC_TOE_SEED_DATA
)
```

### Game Data Structure

```python
{
    "name": "TIC_TAC_TOE",              # ← Constant (will be translated)
    "description": "TIC_TAC_TOE_DESCRIPTION",  # ← Constant
    "category": "strategy",              # ← Fixed value (not translated)
    "version": "1.0.0",
    "plugin_id": "tic_tac_toe",         # ← Technical ID (not translated)
    "min_players": 2,
    "max_players": 2,
    "is_active": true,
    "credit_rate": 1.0,
    "difficulty_level": "easy",
    "estimated_duration_minutes": 5,
    "requires_internet": false,
    "instructions": "TIC_TAC_TOE_INSTRUCTIONS",  # ← Constant
    "author": "GoodPlay Team"
}
```

---

## Database Management Scripts

### Quick Start

```bash
# 1. Verify database
python scripts/verify_db.py

# 2. Seed with Tic Tac Toe game
python scripts/seed_db.py

# 3. View seeded data
python scripts/show_seed_data.py
```

### Script Overview

| Script | Purpose | Safe? |
|--------|---------|-------|
| `verify_db.py` | Check DB status | ✅ Read-only |
| `seed_db.py` | Add test data | ✅ Safe (no delete) |
| `show_seed_data.py` | View test data | ✅ Read-only |
| `reset_db.py` | **Delete all data** | ⚠️ Destructive! |

**Full documentation:** `scripts/README.md`

---

## Seeded Test Data

### Tic Tac Toe Game

```
Name: TIC_TAC_TOE (constant)
Plugin ID: tic_tac_toe
Category: strategy
Players: 2-2 (multiplayer)
Difficulty: easy
Duration: ~5 minutes
Credit Rate: €1.0/minute
Status: Active
```

### Test Users (3 accounts)

| Username | Email | Password |
|----------|-------|----------|
| player1 | player1@goodplay.test | Test1234! |
| player2 | player2@goodplay.test | Test1234! |
| player3 | player3@goodplay.test | Test1234! |

**Features:**
- ✅ Verified accounts
- ✅ Virtual wallets with €0.00 balance
- ✅ Ready for multiplayer testing

### Sample ONLUS Organization

```
Name: ONLUS_EXAMPLE_NAME (constant)
Legal Name: Example Charity Foundation
Tax ID: IT12345678901
Category: education
Status: active (verified)
Bank Details: IBAN included
```

---

## Common Workflows

### First Time Setup

```bash
# Start MongoDB (if not running)
sudo systemctl start mongod

# Start the app (creates indexes)
python app.py

# Seed database with test data
python scripts/seed_db.py

# View seeded data
python scripts/show_seed_data.py
```

### Daily Development

```bash
# Get test credentials
python scripts/show_seed_data.py

# Check database status
python scripts/verify_db.py
```

### Reset for Testing

```bash
# Clean slate + test data
python scripts/reset_db.py --seed --confirm

# Verify
python scripts/verify_db.py
```

---

## Adding New Games

### 1. Add Constants

**File:** `app/games/constants/game_constants.py`

```python
# Game name constant
GAME_MEMORY_NAME = "MEMORY_GAME"

# Description constant
GAME_MEMORY_DESC = "MEMORY_GAME_DESCRIPTION"

# Instructions constant
GAME_MEMORY_INSTRUCTIONS = "MEMORY_GAME_INSTRUCTIONS"

# Seed data
MEMORY_GAME_SEED_DATA = {
    "name": GAME_MEMORY_NAME,
    "description": GAME_MEMORY_DESC,
    "category": CATEGORY_PUZZLE,
    "version": "1.0.0",
    "plugin_id": "memory_game",
    "min_players": 1,
    "max_players": 4,
    "is_active": True,
    "credit_rate": 1.0,
    "difficulty_level": DIFFICULTY_MEDIUM,
    "estimated_duration_minutes": 10,
    "requires_internet": False,
    "instructions": GAME_MEMORY_INSTRUCTIONS,
    "author": "GoodPlay Team"
}
```

### 2. Update Seed Script

**File:** `scripts/seed_db.py`

```python
from app.games.constants import MEMORY_GAME_SEED_DATA

def seed_memory_game(db, verbose=False):
    game_doc = {
        **MEMORY_GAME_SEED_DATA,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
        'install_count': 0,
        'rating': 0.0,
        'total_ratings': 0
    }

    result = db.games.insert_one(game_doc)
    print(f"✅ Memory game created (ID: {result.inserted_id})")
```

### 3. UI Translation Files

**Frontend** (example for Italian):

```javascript
// it.json
{
  "MEMORY_GAME": "Gioco di Memoria",
  "MEMORY_GAME_DESCRIPTION": "Trova le coppie di carte uguali",
  "MEMORY_GAME_INSTRUCTIONS": "Gira due carte alla volta..."
}
```

---

## Environment Configuration

### Required Variables

```env
# .env file
MONGO_URI=mongodb://localhost:27017/goodplay_db
MONGO_DB_NAME=goodplay
```

### Connection String Formats

**Local MongoDB:**
```
MONGO_URI=mongodb://localhost:27017/goodplay_db
```

**MongoDB with Authentication:**
```
MONGO_URI=mongodb://username:password@localhost:27017/goodplay_db
```

**MongoDB Atlas (Cloud):**
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/goodplay_db
```

**Docker Compose:**
```
MONGO_URI=mongodb://admin:password@mongo:27017/admin
```

---

## Troubleshooting

### Connection Refused

**Problem:** Can't connect to MongoDB

**Solutions:**
1. Check MongoDB is running: `sudo systemctl status mongod`
2. Start MongoDB: `sudo systemctl start mongod`
3. Verify `MONGO_URI` in `.env`

### No Games Found

**Problem:** Database is empty

**Solution:**
```bash
python scripts/seed_db.py
```

### Duplicate Key Error

**Problem:** Game already exists

**Solutions:**
```bash
# Option 1: Clean and re-seed
python scripts/seed_db.py --clean

# Option 2: Full reset
python scripts/reset_db.py --seed --confirm
```

### Missing Indexes

**Problem:** Indexes not created

**Solution:**
```bash
# Start app to auto-create indexes
python app.py
```

---

## Best Practices

### ✅ DO

- Use constants for all user-facing text
- Run `verify_db.py` before and after changes
- Use test users for development/testing
- Keep seed data simple and minimal
- Document new constants in code comments

### ❌ DON'T

- Never use literal strings for game names/descriptions
- Don't use `reset_db.py` in production
- Don't commit test credentials to git
- Don't manually create collections
- Don't bypass the seed scripts

---

## References

- **Scripts Documentation:** `scripts/README.md`
- **Game Constants:** `app/games/constants/game_constants.py`
- **Database Models:** `app/*/models/`
- **Repository Pattern:** `app/*/repositories/`
- **Development Guide:** `CLAUDE.md`

---

## Summary

✅ **Database auto-initializes** when app starts
✅ **Use constants** for all translatable text
✅ **Seed scripts** provide test data
✅ **Verify scripts** check DB health
✅ **No manual SQL** needed (MongoDB handles it)

**Quick Start:**
```bash
python app.py                    # Initialize
python scripts/seed_db.py        # Populate
python scripts/show_seed_data.py # View
```
