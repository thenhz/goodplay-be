#!/usr/bin/env python3
"""
Show Seeded Data Script

Displays all seeded test data in a user-friendly format.

Usage:
    python scripts/show_seed_data.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from datetime import datetime, timezone


def load_config():
    """Load configuration from .env file"""
    from dotenv import load_dotenv
    load_dotenv()

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/goodplay_db')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'goodplay')

    return mongo_uri, mongo_db_name


def show_games(db):
    """Display seeded games"""
    print("\n" + "=" * 80)
    print("SEEDED GAMES")
    print("=" * 80)

    games = list(db.games.find({}))

    if not games:
        print("No games found in database")
        return

    for game in games:
        print(f"\n📱 {game.get('name', 'Unnamed')}")
        print(f"   ID: {game.get('_id')}")
        print(f"   Plugin ID: {game.get('plugin_id', 'N/A')}")
        print(f"   Description: {game.get('description', 'N/A')}")
        print(f"   Category: {game.get('category', 'N/A')}")
        print(f"   Version: {game.get('version', 'N/A')}")
        print(f"   Players: {game.get('min_players', 1)}-{game.get('max_players', 1)}")
        print(f"   Difficulty: {game.get('difficulty_level', 'N/A')}")
        print(f"   Duration: ~{game.get('estimated_duration_minutes', 0)} minutes")
        print(f"   Credit Rate: €{game.get('credit_rate', 0)}/minute")
        if 'thumbnail_url' in game:
            print(f"   Thumbnail: {game.get('thumbnail_url')}")
        print(f"   Active: {game.get('is_active', False)}")
        print(f"   Installs: {game.get('install_count', 0)}")
        print(f"   Rating: {game.get('rating', 0):.1f} ({game.get('total_ratings', 0)} ratings)")


def show_test_users(db):
    """Display seeded test users"""
    print("\n" + "=" * 80)
    print("TEST USERS")
    print("=" * 80)

    # Find test users by email pattern
    users = list(db.users.find({'email': {'$regex': '@goodplay.test$'}}))

    if not users:
        print("No test users found")
        return

    print(f"\nFound {len(users)} test user(s):\n")

    # Print header
    print(f"{'Username':<12} {'Email':<30} {'Full Name':<20} {'Balance':<12} {'User ID'}")
    print("-" * 100)

    for user in users:
        user_id = str(user.get('_id'))
        username = user.get('username', 'N/A')
        email = user.get('email', 'N/A')
        full_name = user.get('full_name', 'N/A')

        # Get wallet balance
        wallet = db.wallets.find_one({'user_id': user_id})
        balance = f"€{wallet.get('current_balance', 0):.2f}" if wallet else "No wallet"

        print(f"{username:<12} {email:<30} {full_name:<20} {balance:<12} {user_id[:12]}...")

    print(f"\n🔑 Default password for all test users: Test1234!")


def show_onlus(db):
    """Display seeded ONLUS organizations"""
    print("\n" + "=" * 80)
    print("ONLUS ORGANIZATIONS")
    print("=" * 80)

    orgs = list(db.onlus_organizations.find({}))

    if not orgs:
        print("No ONLUS organizations found")
        return

    for org in orgs:
        print(f"\n🏛️  {org.get('organization_name', 'Unnamed')}")
        print(f"   ID: {org.get('_id')}")
        print(f"   Legal Name: {org.get('legal_name', 'N/A')}")
        print(f"   Category: {org.get('category', 'N/A')}")
        print(f"   Mission: {org.get('mission_statement', 'N/A')}")
        print(f"   Contact: {org.get('contact_email', 'N/A')}")
        print(f"   Website: {org.get('website_url', 'N/A')}")
        print(f"   Tax ID: {org.get('tax_id', 'N/A')}")
        print(f"   Status: {org.get('status', 'N/A')}")
        print(f"   Verification: {org.get('verification_level', 'N/A')}")
        print(f"   Total Donations: €{org.get('total_donations_received', 0):.2f}")
        print(f"   Donors: {org.get('donors_count', 0)}")


def show_quick_reference(db):
    """Display quick reference for API testing"""
    print("\n" + "=" * 80)
    print("QUICK REFERENCE FOR API TESTING")
    print("=" * 80)

    # Get first game
    game = db.games.find_one({})
    game_id = str(game.get('_id')) if game else 'N/A'

    # Get first test user
    user = db.users.find_one({'email': {'$regex': '@goodplay.test$'}})
    user_id = str(user.get('_id')) if user else 'N/A'
    user_email = user.get('email') if user else 'N/A'

    # Get ONLUS
    onlus = db.onlus_organizations.find_one({})
    onlus_id = str(onlus.get('_id')) if onlus else 'N/A'

    print("\n📋 IDs for API Testing:\n")
    print(f"   Game ID: {game_id}")
    print(f"   User ID: {user_id}")
    print(f"   ONLUS ID: {onlus_id}")

    print("\n🔐 Test Credentials:\n")
    print(f"   Email: {user_email}")
    print(f"   Password: Test1234!")

    print("\n📡 Example API Calls:\n")
    print(f"   # Login")
    print(f"   POST /api/auth/login")
    print(f"   {{\"email\": \"{user_email}\", \"password\": \"Test1234!\"}}")
    print()
    print(f"   # Get Game")
    print(f"   GET /api/games/{game_id}")
    print()
    print(f"   # Create Multiplayer Room")
    print(f"   POST /api/multiplayer/rooms")
    print(f"   {{\"game_id\": \"{game_id}\", \"max_players\": 2}}")


def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("GOODPLAY SEEDED DATA VIEWER")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Load configuration
    mongo_uri, mongo_db_name = load_config()

    # Connect to MongoDB
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[mongo_db_name]

        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to: {mongo_db_name}")
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB: {str(e)}")
        sys.exit(1)

    # Show all seeded data
    show_games(db)
    show_test_users(db)
    show_onlus(db)
    show_quick_reference(db)

    print("\n" + "=" * 80)
    print()

    # Cleanup
    client.close()


if __name__ == "__main__":
    main()
