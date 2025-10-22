# GoodPlay Database Management Scripts

This directory contains utility scripts for managing the GoodPlay database during development and testing.

## Available Scripts

### 1. `verify_db.py` - Database Verification

Verifies the MongoDB connection, collections, indexes, and data integrity.

**Usage:**
```bash
# Basic verification
python scripts/verify_db.py

# Verbose output with detailed information
python scripts/verify_db.py --verbose
python scripts/verify_db.py -v
```

**What it checks:**
- ✅ MongoDB connection and version
- ✅ Database statistics (size, collections, indexes)
- ✅ Expected collections existence
- ✅ Required indexes on collections
- ✅ Games data (shows all games in DB)

**Exit codes:**
- `0` - All checks passed
- `1` - Some checks failed

---

### 2. `seed_db.py` - Database Seeding

Populates the database with initial test data for development and testing.

**Usage:**
```bash
# Seed database with test data
python scripts/seed_db.py

# Clean database and then seed
python scripts/seed_db.py --clean

# Verbose output
python scripts/seed_db.py --verbose
python scripts/seed_db.py -v

# Clean and seed with verbose output
python scripts/seed_db.py --clean --verbose
```

**What it seeds:**

1. **Tic Tac Toe Game**
   - Name: `TIC_TAC_TOE` (constant for UI translation)
   - Category: `strategy`
   - Players: 2-2 (multiplayer)
   - Plugin ID: `tic_tac_toe`
   - Status: Active

2. **Test Users** (3 users for multiplayer testing)
   - `player1@goodplay.test` - Password: `Test1234!`
   - `player2@goodplay.test` - Password: `Test1234!`
   - `player3@goodplay.test` - Password: `Test1234!`
   - All users have verified accounts and wallets

3. **Sample ONLUS Organization**
   - Example charity for testing donations
   - Status: Active and verified
   - Category: Education

**Options:**
- `--clean` - Delete all data before seeding
- `--verbose` - Show detailed output including IDs and passwords

**Notes:**
- If data already exists, it will show warnings and skip duplicates
- Use `--clean` flag to reset and re-seed from scratch
- All text uses constants (e.g., `TIC_TAC_TOE`) that will be translated by the UI

---

### 3. `reset_db.py` - Database Reset

⚠️ **DANGER:** Completely resets the database by dropping all collections.

**Usage:**
```bash
# Reset database (will prompt for confirmation)
python scripts/reset_db.py

# Reset and seed with test data
python scripts/reset_db.py --seed

# Skip confirmation prompt (use with caution!)
python scripts/reset_db.py --confirm

# Reset, seed, and skip confirmation
python scripts/reset_db.py --seed --confirm
```

**What it does:**
- Drops ALL collections in the database
- Deletes ALL data (users, games, sessions, wallets, everything)
- **Cannot be undone!**
- Optionally re-seeds the database if `--seed` flag is used

**Safety:**
- Requires typing `RESET` to confirm (unless `--confirm` flag is used)
- Shows warning about data loss
- Lists all collections that will be dropped

**Options:**
- `--seed` - Run seed script after reset
- `--confirm` - Skip confirmation prompt (dangerous!)

---

### 4. `show_seed_data.py` - View Seeded Data

Displays all seeded test data in a user-friendly format with IDs for API testing.

**Usage:**
```bash
# Show all seeded data
python scripts/show_seed_data.py
```

**What it shows:**
- ✅ All games with complete details
- ✅ Test users with credentials and wallet balances
- ✅ ONLUS organizations with verification info
- ✅ Quick reference IDs for API testing
- ✅ Example API calls with actual IDs

**Perfect for:**
- Quickly getting test credentials
- Finding IDs for Postman/API testing
- Verifying what data is in the database
- Reference when developing frontend

---

## Common Workflows

### Initial Setup (First Time)

```bash
# 1. Verify database connection
python scripts/verify_db.py

# 2. Seed database with test data
python scripts/seed_db.py

# 3. Verify seeding was successful
python scripts/verify_db.py

# 4. View seeded data and get test credentials
python scripts/show_seed_data.py
```

### Development Workflow

```bash
# Check database status
python scripts/verify_db.py

# View current data
python scripts/show_seed_data.py

# Reset and re-seed for clean state
python scripts/reset_db.py --seed --confirm

# Or just clean and seed
python scripts/seed_db.py --clean
```

### Testing Workflow

```bash
# Before running tests, ensure clean database
python scripts/reset_db.py --seed --confirm

# Run your tests
pytest

# Verify database state after tests
python scripts/verify_db.py
```

---

## Game Constants System

All user-facing text in seeded data uses **constants** instead of literal strings. These constants are defined in:

```
app/games/constants/game_constants.py
```

### Why Constants?

The UI will translate these constants into the user's preferred language at runtime.

**Example:**
```python
# In database
{
  "name": "TIC_TAC_TOE",
  "description": "TIC_TAC_TOE_DESCRIPTION"
}

# In UI (Italian)
{
  "name": "Tris",
  "description": "Classico gioco di strategia su griglia 3x3"
}

# In UI (English)
{
  "name": "Tic Tac Toe",
  "description": "Classic 3x3 grid strategy game"
}
```

### Available Game Constants

- `GAME_TIC_TAC_TOE_NAME` → `"TIC_TAC_TOE"`
- `GAME_TIC_TAC_TOE_DESC` → `"TIC_TAC_TOE_DESCRIPTION"`
- `GAME_TIC_TAC_TOE_INSTRUCTIONS` → `"TIC_TAC_TOE_INSTRUCTIONS"`

See `app/games/constants/game_constants.py` for the full list.

---

## Seeded Test Data Reference

### Test Users

All test users have the same password: `Test1234!`

| Username | Email | Full Name | Purpose |
|----------|-------|-----------|---------|
| player1 | player1@goodplay.test | Test Player One | Multiplayer testing |
| player2 | player2@goodplay.test | Test Player Two | Multiplayer testing |
| player3 | player3@goodplay.test | Test Player Three | Multiplayer testing |

Each user has:
- ✅ Verified email
- ✅ Active account
- ✅ Virtual wallet with €0.00 balance
- ✅ Default preferences set

### Seeded Game

**Tic Tac Toe**
- Plugin ID: `tic_tac_toe`
- Category: Strategy
- Min/Max Players: 2-2
- Difficulty: Easy
- Duration: ~5 minutes
- Credits: 1.0 credits/minute
- Status: Active

### Seeded ONLUS

**Example Charity Foundation**
- Tax ID: IT12345678901
- Category: Education
- Status: Active, Verified
- Compliance: Compliant
- Bank details included for testing donations

---

## Database Initialization Notes

### Automatic Index Creation

MongoDB collections and indexes are created automatically when the Flask app starts:

1. **On App Startup** (`app/__init__.py`):
   - `init_db()` function creates database connection
   - All repository `create_indexes()` methods are called
   - Indexes are created for all collections

2. **Collections Are Auto-Created**:
   - MongoDB creates collections automatically on first insert
   - No need for explicit CREATE TABLE statements
   - Collections appear when you insert the first document

### Manual Index Creation

If you need to manually trigger index creation without starting the app:

```bash
# Start Python shell
python

# Import and initialize
from app import create_app
app = create_app()
with app.app_context():
    from app.games.repositories.game_repository import GameRepository
    repo = GameRepository()
    repo.create_indexes()
```

---

## Troubleshooting

### Connection Refused

**Problem:** `Failed to connect to MongoDB: Connection refused`

**Solutions:**
1. Check MongoDB is running: `sudo systemctl status mongod`
2. Start MongoDB: `sudo systemctl start mongod`
3. Verify `MONGO_URI` in `.env` file

### Duplicate Key Error

**Problem:** `DuplicateKeyError` when seeding

**Solution:**
```bash
# Clean database first
python scripts/seed_db.py --clean
```

### Missing Collections

**Problem:** Verification shows missing collections

**Solution:**
Collections are auto-created on first insert. Either:
1. Run seed script: `python scripts/seed_db.py`
2. Start the app: `python app.py` (creates indexes)

### Missing Indexes

**Problem:** Indexes not found on collections

**Solution:**
```bash
# Start the app to auto-create indexes
python app.py

# Or manually trigger index creation
python -c "from app import create_app; app = create_app()"
```

---

## Environment Configuration

Scripts use environment variables from `.env` file:

```env
MONGO_URI=mongodb://localhost:27017/goodplay_db
MONGO_DB_NAME=goodplay
```

Make sure your `.env` file is properly configured before running scripts.

---

## Additional Resources

- **Main Documentation**: `/docs/` directory
- **Game Engine Guide**: `/GAME_ENGINE_GUIDE.md`
- **Development Guide**: `/CLAUDE.md`
- **API Documentation**: `/docs/openapi/`

---

## Safety Reminders

⚠️ **IMPORTANT:**
- `reset_db.py` permanently deletes ALL data
- Always backup production data before running scripts
- Test scripts in development environment first
- Use `--confirm` flag carefully in production

💡 **TIP:**
Use `--verbose` flag to see detailed output and debug issues.

---

## Script Maintenance

When adding new seed data:

1. **Add constants** to `app/games/constants/game_constants.py`
2. **Update seed script** in `seed_db.py`
3. **Update this README** with new data documentation
4. **Test thoroughly** with `--clean` flag

When adding new collections:

1. **Add to expected list** in `verify_db.py` → `EXPECTED_COLLECTIONS`
2. **Add indexes** to `EXPECTED_INDEXES` if applicable
3. **Update reset script** if special cleanup needed
4. **Document** in this README
