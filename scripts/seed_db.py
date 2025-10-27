#!/usr/bin/env python3
"""
Database Seed Script

Populates the database with initial test data:
- Games (Tic Tac Toe, Flow Tiles) using constants for UI translation
- Test users for multiplayer testing
- Sample ONLUS organization for donation testing

Usage:
    python scripts/seed_db.py              # Seed database
    python scripts/seed_db.py --clean      # Clean and seed
    python scripts/seed_db.py --verbose    # Verbose output
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
import argparse
from bson import ObjectId
import bcrypt


def load_config():
    """Load configuration from .env file"""
    from dotenv import load_dotenv
    load_dotenv()

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/goodplay_db')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'goodplay')

    return mongo_uri, mongo_db_name


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def seed_games(db, verbose=False):
    """Seed all games using constants"""
    print("\n" + "=" * 60)
    print("SEEDING GAMES")
    print("=" * 60)

    # Import constants
    from app.games.constants import TIC_TAC_TOE_SEED_DATA, FLOW_TILES_SEED_DATA

    games_to_seed = [
        TIC_TAC_TOE_SEED_DATA,
        FLOW_TILES_SEED_DATA
    ]

    created_count = 0
    for game_data in games_to_seed:
        try:
            # Create game document with current timestamps
            game_doc = {
                **game_data,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'install_count': 0,
                'rating': 0.0,
                'total_ratings': 0
            }

            # Try to insert
            result = db.games.insert_one(game_doc)
            game_name = game_data.get('name', 'Unknown')
            print(f"✅ {game_name} game created (ID: {result.inserted_id})")

            if verbose:
                print(f"   Name constant: {game_doc['name']}")
                print(f"   Plugin ID: {game_doc['plugin_id']}")
                print(f"   Category: {game_doc['category']}")
                print(f"   Players: {game_doc['min_players']}-{game_doc['max_players']}")
                if 'thumbnail_url' in game_doc:
                    print(f"   Thumbnail: {game_doc['thumbnail_url']}")

            created_count += 1

        except DuplicateKeyError:
            game_name = game_data.get('name', 'Unknown')
            print(f"⚠️  {game_name} game already exists (duplicate plugin_id or name)")
        except Exception as e:
            game_name = game_data.get('name', 'Unknown')
            print(f"❌ Failed to create {game_name} game: {str(e)}")

    if created_count > 0:
        print(f"\n✅ Created {created_count} game(s)")
        return True

    return False


def seed_test_users(db, verbose=False):
    """Seed test users for multiplayer testing"""
    print("\n" + "=" * 60)
    print("SEEDING TEST USERS")
    print("=" * 60)

    # Test users with simple credentials
    test_users = [
        {
            'username': 'player1',
            'email': 'player1@goodplay.test',
            'password': 'Test1234!',
            'full_name': 'Test Player One'
        },
        {
            'username': 'player2',
            'email': 'player2@goodplay.test',
            'password': 'Test1234!',
            'full_name': 'Test Player Two'
        },
        {
            'username': 'player3',
            'email': 'player3@goodplay.test',
            'password': 'Test1234!',
            'full_name': 'Test Player Three'
        }
    ]

    created_count = 0
    for user_data in test_users:
        try:
            # Create user document
            user_doc = {
                'username': user_data['username'],
                'email': user_data['email'],
                'password_hash': hash_password(user_data['password']),
                'full_name': user_data['full_name'],
                'is_active': True,
                'is_verified': True,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'preferences': {
                    'language': 'en',
                    'notifications_enabled': True
                }
            }

            result = db.users.insert_one(user_doc)
            print(f"✅ User created: {user_data['username']} ({user_data['email']})")

            if verbose:
                print(f"   User ID: {result.inserted_id}")
                print(f"   Password: {user_data['password']}")

            # Create wallet for user
            wallet_doc = {
                'user_id': str(result.inserted_id),
                'current_balance': 0.0,
                'total_earned': 0.0,
                'total_donated': 0.0,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'auto_donation_enabled': False,
                'version': 0
            }
            db.wallets.insert_one(wallet_doc)

            created_count += 1

        except DuplicateKeyError:
            print(f"⚠️  User {user_data['username']} already exists")
        except Exception as e:
            print(f"❌ Failed to create user {user_data['username']}: {str(e)}")

    if created_count > 0:
        print(f"\n✅ Created {created_count} test user(s)")
        print(f"   Default password for all users: Test1234!")

    return created_count > 0


def seed_onlus(db, verbose=False):
    """Seed sample ONLUS organization for donation testing"""
    print("\n" + "=" * 60)
    print("SEEDING ONLUS ORGANIZATION")
    print("=" * 60)

    try:
        # Create sample ONLUS organization
        onlus_doc = {
            'application_id': str(ObjectId()),  # Fake application ID
            'organization_name': 'ONLUS_EXAMPLE_NAME',  # Constant for UI translation
            'legal_name': 'Example Charity Foundation',
            'category': 'education',
            'mission_statement': 'ONLUS_EXAMPLE_MISSION',  # Constant
            'description': 'ONLUS_EXAMPLE_DESCRIPTION',  # Constant
            'contact_email': 'contact@example-charity.org',
            'contact_phone': '+39 02 1234567',
            'website_url': 'https://example-charity.org',
            'logo_url': None,
            'address': {
                'street': 'Via Roma 123',
                'city': 'Milano',
                'state': 'MI',
                'postal_code': '20100',
                'country': 'Italy'
            },
            'legal_entity_type': 'nonprofit',
            'tax_id': 'IT12345678901',
            'incorporation_date': datetime(2020, 1, 1, tzinfo=timezone.utc),
            'verification_date': datetime.now(timezone.utc),
            'verification_level': 'standard',
            'status': 'active',
            'compliance_status': 'compliant',
            'documents': [],
            'bank_details': {
                'iban': 'IT60X0542811101000000123456',
                'bank_name': 'Banca Esempio',
                'account_holder': 'Example Charity Foundation'
            },
            'total_donations_received': 0.0,
            'donors_count': 0,
            'impact_metrics': {},
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        result = db.onlus_organizations.insert_one(onlus_doc)
        print(f"✅ ONLUS organization created (ID: {result.inserted_id})")

        if verbose:
            print(f"   Name constant: {onlus_doc['organization_name']}")
            print(f"   Legal name: {onlus_doc['legal_name']}")
            print(f"   Category: {onlus_doc['category']}")
            print(f"   Status: {onlus_doc['status']}")

        return True

    except DuplicateKeyError:
        print("⚠️  ONLUS organization already exists")
        return False
    except Exception as e:
        print(f"❌ Failed to create ONLUS: {str(e)}")
        return False


def clean_database(db, verbose=False):
    """Clean all collections"""
    print("\n" + "=" * 60)
    print("CLEANING DATABASE")
    print("=" * 60)
    print("⚠️  This will delete ALL data from the database!")

    # Collections to clean
    collections_to_clean = [
        'games',
        'users',
        'wallets',
        'onlus_organizations',
        'game_sessions',
        'game_rooms',
        'multiplayer_sessions',
        'player_states',
        'transactions',
    ]

    for collection_name in collections_to_clean:
        try:
            result = db[collection_name].delete_many({})
            count = result.deleted_count
            if count > 0 or verbose:
                print(f"   Deleted {count} document(s) from {collection_name}")
        except Exception as e:
            print(f"❌ Error cleaning {collection_name}: {str(e)}")

    print("✅ Database cleaned")


def main():
    """Main seeding function"""
    parser = argparse.ArgumentParser(description='Seed GoodPlay database with test data')
    parser.add_argument('--clean', action='store_true',
                       help='Clean database before seeding')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("GOODPLAY DATABASE SEED SCRIPT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Load configuration
    mongo_uri, mongo_db_name = load_config()
    print(f"MongoDB URI: {mongo_uri}")
    print(f"Database: {mongo_db_name}")

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

    # Clean database if requested
    if args.clean:
        clean_database(db, verbose=args.verbose)

    # Run seeding operations
    results = []
    results.append(seed_games(db, verbose=args.verbose))
    results.append(seed_test_users(db, verbose=args.verbose))
    results.append(seed_onlus(db, verbose=args.verbose))

    # Summary
    print("\n" + "=" * 60)
    print("SEEDING SUMMARY")
    print("=" * 60)

    successful = sum(results)
    total = len(results)

    if successful == total:
        print(f"✅ ALL SEEDING OPERATIONS SUCCESSFUL ({successful}/{total})")
        print("\nDatabase is ready to use!")
        print("\nTest accounts:")
        print("  Email: player1@goodplay.test, Password: Test1234!")
        print("  Email: player2@goodplay.test, Password: Test1234!")
        print("  Email: player3@goodplay.test, Password: Test1234!")
        exit_code = 0
    elif successful > 0:
        print(f"⚠️  PARTIAL SUCCESS ({successful}/{total} operations succeeded)")
        print("\nSome items may already exist in the database.")
        print("Use --clean flag to reset and re-seed: python scripts/seed_db.py --clean")
        exit_code = 0
    else:
        print(f"❌ ALL SEEDING OPERATIONS FAILED")
        exit_code = 1

    print("=" * 60)

    # Cleanup
    client.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
