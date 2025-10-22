#!/usr/bin/env python3
"""
Database Reset Script

Completely resets the database by dropping all collections.
Optionally re-seeds the database with initial test data.

⚠️  WARNING: This will delete ALL data in the database!

Usage:
    python scripts/reset_db.py                # Reset only (no seed)
    python scripts/reset_db.py --seed         # Reset and seed
    python scripts/reset_db.py --confirm      # Skip confirmation prompt
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from datetime import datetime
import argparse
import subprocess


def load_config():
    """Load configuration from .env file"""
    from dotenv import load_dotenv
    load_dotenv()

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/goodplay_db')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'goodplay')

    return mongo_uri, mongo_db_name


def confirm_reset():
    """Prompt user to confirm reset operation"""
    print("\n" + "!" * 60)
    print("⚠️  WARNING: DATABASE RESET OPERATION")
    print("!" * 60)
    print("\nThis will DELETE ALL DATA from the database, including:")
    print("  - All games and game sessions")
    print("  - All users and authentication data")
    print("  - All wallets and transactions")
    print("  - All ONLUS organizations")
    print("  - All multiplayer rooms and sessions")
    print("  - Everything else in the database")
    print("\n⚠️  THIS OPERATION CANNOT BE UNDONE!")

    response = input("\nType 'RESET' to confirm: ").strip()

    return response == 'RESET'


def reset_database(db, verbose=False):
    """Drop all collections in the database"""
    print("\n" + "=" * 60)
    print("RESETTING DATABASE")
    print("=" * 60)

    try:
        # Get list of all collections
        collections = db.list_collection_names()

        if not collections:
            print("⚠️  Database is already empty")
            return True

        print(f"Found {len(collections)} collection(s) to drop:")

        # Drop each collection
        dropped_count = 0
        for collection_name in collections:
            try:
                # Get document count before dropping
                count = db[collection_name].count_documents({})

                # Drop the collection
                db[collection_name].drop()

                print(f"   ✅ Dropped {collection_name} ({count} documents)")
                dropped_count += 1

            except Exception as e:
                print(f"   ❌ Failed to drop {collection_name}: {str(e)}")

        print(f"\n✅ Dropped {dropped_count}/{len(collections)} collection(s)")
        print("✅ Database reset complete")

        return dropped_count == len(collections)

    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")
        return False


def run_seed_script():
    """Run the seed script to populate database"""
    print("\n" + "=" * 60)
    print("RUNNING SEED SCRIPT")
    print("=" * 60)

    script_path = Path(__file__).parent / "seed_db.py"

    try:
        # Run seed script as subprocess
        result = subprocess.run(
            [sys.executable, str(script_path), "--verbose"],
            capture_output=False,
            text=True
        )

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Failed to run seed script: {str(e)}")
        return False


def main():
    """Main reset function"""
    parser = argparse.ArgumentParser(
        description='Reset GoodPlay database (delete all data)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/reset_db.py              # Reset only
  python scripts/reset_db.py --seed       # Reset and seed with test data
  python scripts/reset_db.py --confirm    # Skip confirmation prompt
        """
    )
    parser.add_argument('--seed', action='store_true',
                       help='Seed database after reset')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt (use with caution!)')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("GOODPLAY DATABASE RESET SCRIPT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Load configuration
    mongo_uri, mongo_db_name = load_config()
    print(f"MongoDB URI: {mongo_uri}")
    print(f"Database: {mongo_db_name}")

    # Confirm operation unless --confirm flag is used
    if not args.confirm:
        if not confirm_reset():
            print("\n❌ Reset operation cancelled by user")
            sys.exit(0)

    # Connect to MongoDB
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[mongo_db_name]

        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB: {str(e)}")
        sys.exit(1)

    # Perform reset
    reset_success = reset_database(db, verbose=True)

    # Run seed script if requested
    seed_success = True
    if args.seed and reset_success:
        seed_success = run_seed_script()

    # Summary
    print("\n" + "=" * 60)
    print("RESET SUMMARY")
    print("=" * 60)

    if reset_success:
        print("✅ Database reset: SUCCESS")
        if args.seed:
            if seed_success:
                print("✅ Database seeding: SUCCESS")
                print("\nDatabase has been reset and populated with test data!")
            else:
                print("❌ Database seeding: FAILED")
                print("\nDatabase was reset but seeding failed.")
                print("Run manually: python scripts/seed_db.py")
        else:
            print("\nDatabase has been completely reset (empty).")
            print("To populate with test data, run: python scripts/seed_db.py")

        exit_code = 0 if (seed_success or not args.seed) else 1
    else:
        print("❌ Database reset: FAILED")
        exit_code = 1

    print("=" * 60)

    # Cleanup
    client.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
