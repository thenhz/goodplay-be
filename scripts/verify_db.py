#!/usr/bin/env python3
"""
Database Verification Script

Verifies MongoDB connection, collections, and indexes.
Provides a comprehensive report of database status.

Usage:
    python scripts/verify_db.py
    python scripts/verify_db.py --verbose
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime, timezone
import argparse


# Expected collections in the database
EXPECTED_COLLECTIONS = [
    'users',
    'games',
    'game_sessions',
    'game_rooms',
    'multiplayer_sessions',
    'player_states',
    'wallets',
    'transactions',
    'onlus_organizations',
    'achievements',
    'leaderboards',
]

# Expected indexes per collection
EXPECTED_INDEXES = {
    'users': ['email_1', 'username_1'],
    'games': ['name_1', 'plugin_id_1', 'category_1', 'is_active_1'],
    'game_sessions': ['user_id_1', 'game_id_1', 'status_1'],
    'game_rooms': ['room_code_1', 'game_id_1', 'status_1'],
    'wallets': ['user_id_1'],
    'transactions': ['user_id_1', 'type_1', 'status_1'],
}


def load_config():
    """Load configuration from .env file"""
    from dotenv import load_dotenv
    load_dotenv()

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/goodplay_db')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'goodplay')

    return mongo_uri, mongo_db_name


def verify_connection(client):
    """Verify MongoDB connection"""
    print("=" * 60)
    print("DATABASE CONNECTION VERIFICATION")
    print("=" * 60)

    try:
        # The ping command is cheap and does not require auth
        client.admin.command('ping')
        print("✅ MongoDB connection: SUCCESS")

        # Get server info
        server_info = client.server_info()
        print(f"✅ MongoDB version: {server_info.get('version', 'unknown')}")
        return True
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection: FAILED - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ MongoDB connection: ERROR - {str(e)}")
        return False


def verify_database(db, verbose=False):
    """Verify database existence and stats"""
    print("\n" + "=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)

    try:
        stats = db.command('dbstats')
        print(f"✅ Database name: {db.name}")
        print(f"✅ Collections: {stats.get('collections', 0)}")
        print(f"✅ Data size: {stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
        print(f"✅ Storage size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        print(f"✅ Indexes: {stats.get('indexes', 0)}")
        print(f"✅ Index size: {stats.get('indexSize', 0) / 1024 / 1024:.2f} MB")

        if verbose:
            print(f"\nFull stats: {stats}")

        return True
    except OperationFailure as e:
        print(f"❌ Database stats: FAILED - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Database stats: ERROR - {str(e)}")
        return False


def verify_collections(db, verbose=False):
    """Verify expected collections exist"""
    print("\n" + "=" * 60)
    print("COLLECTIONS VERIFICATION")
    print("=" * 60)

    existing_collections = db.list_collection_names()

    missing_collections = []
    for collection_name in EXPECTED_COLLECTIONS:
        if collection_name in existing_collections:
            count = db[collection_name].count_documents({})
            print(f"✅ {collection_name:<30} (documents: {count})")
        else:
            print(f"⚠️  {collection_name:<30} (MISSING)")
            missing_collections.append(collection_name)

    # List extra collections not in expected list
    extra_collections = [c for c in existing_collections if c not in EXPECTED_COLLECTIONS]
    if extra_collections and verbose:
        print(f"\n📋 Additional collections found:")
        for collection_name in extra_collections:
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name:<30} (documents: {count})")

    if missing_collections:
        print(f"\n⚠️  Missing collections: {len(missing_collections)}")
        print(f"   Note: Collections are auto-created on first insert")

    return len(missing_collections) == 0


def verify_indexes(db, verbose=False):
    """Verify indexes exist for collections"""
    print("\n" + "=" * 60)
    print("INDEXES VERIFICATION")
    print("=" * 60)

    missing_indexes = []

    for collection_name, expected_indexes in EXPECTED_INDEXES.items():
        if collection_name not in db.list_collection_names():
            print(f"⚠️  {collection_name:<30} (collection missing, skipping indexes)")
            continue

        collection = db[collection_name]
        existing_indexes = list(collection.list_indexes())
        existing_index_names = [idx['name'] for idx in existing_indexes]

        print(f"\n📂 {collection_name}:")
        for expected_index in expected_indexes:
            if expected_index in existing_index_names:
                print(f"   ✅ {expected_index}")
            else:
                print(f"   ❌ {expected_index} (MISSING)")
                missing_indexes.append(f"{collection_name}.{expected_index}")

        if verbose:
            # Show all indexes for this collection
            extra_indexes = [name for name in existing_index_names
                           if name not in expected_indexes and name != '_id_']
            if extra_indexes:
                print(f"   📋 Additional indexes: {', '.join(extra_indexes)}")

    if missing_indexes:
        print(f"\n⚠️  Missing indexes: {len(missing_indexes)}")
        print(f"   Run `python app.py` to create missing indexes automatically")

    return len(missing_indexes) == 0


def verify_games(db):
    """Verify games collection and show game data"""
    print("\n" + "=" * 60)
    print("GAMES VERIFICATION")
    print("=" * 60)

    if 'games' not in db.list_collection_names():
        print("⚠️  Games collection not found - run seed script to create initial games")
        return False

    games = list(db.games.find({}))

    if not games:
        print("⚠️  No games found in database")
        print("   Run: python scripts/seed_db.py")
        return False

    print(f"✅ Found {len(games)} game(s):\n")
    for game in games:
        print(f"   • {game.get('name', 'Unnamed')} (v{game.get('version', '?')})")
        print(f"     - Plugin ID: {game.get('plugin_id', 'N/A')}")
        print(f"     - Category: {game.get('category', 'N/A')}")
        print(f"     - Players: {game.get('min_players', 1)}-{game.get('max_players', 1)}")
        print(f"     - Active: {game.get('is_active', False)}")
        print()

    return True


def main():
    """Main verification function"""
    parser = argparse.ArgumentParser(description='Verify GoodPlay database status')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("GOODPLAY DATABASE VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Load configuration
    mongo_uri, mongo_db_name = load_config()
    print(f"MongoDB URI: {mongo_uri}")
    print(f"Database: {mongo_db_name}")

    # Connect to MongoDB
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[mongo_db_name]
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB: {str(e)}")
        sys.exit(1)

    # Run verifications
    results = []
    results.append(verify_connection(client))
    results.append(verify_database(db, verbose=args.verbose))
    results.append(verify_collections(db, verbose=args.verbose))
    results.append(verify_indexes(db, verbose=args.verbose))
    results.append(verify_games(db))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\nDatabase is properly configured and ready to use!")
        exit_code = 0
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total} passed)")
        print("\nRecommendations:")
        if not results[0]:  # Connection failed
            print("  1. Check MongoDB is running")
            print("  2. Verify MONGO_URI in .env file")
        if not results[4]:  # No games
            print("  3. Run seed script: python scripts/seed_db.py")
        if not results[2] or not results[3]:  # Missing collections/indexes
            print("  4. Start the app to auto-create indexes: python app.py")
        exit_code = 1

    print("=" * 60)

    # Cleanup
    client.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
