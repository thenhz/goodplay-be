#!/usr/bin/env python3
"""
Migration Script: Add User Extensions for GOO-5
Adds gaming_stats, impact_score, preferences, social_profile, and wallet_credits to existing users
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.core.repositories.user_repository import UserRepository
from flask import current_app

def run_migration():
    """Run the user extensions migration"""
    app = create_app('development')

    with app.app_context():
        try:
            user_repo = UserRepository()

            # Check if migration is needed
            sample_user = user_repo.collection.find_one()
            if not sample_user:
                print("No users found in database. Migration not needed.")
                return True

            # Check if any user is missing the new fields
            users_needing_migration = user_repo.collection.count_documents({
                "$or": [
                    {"gaming_stats": {"$exists": False}},
                    {"preferences": {"$exists": False}},
                    {"wallet_credits": {"$exists": False}},
                    {"impact_score": {"$exists": False}},
                    {"social_profile": {"$exists": False}}
                ]
            })

            if users_needing_migration == 0:
                print("All users already have the new fields. Migration not needed.")
                return True

            print(f"Found {users_needing_migration} users that need migration.")

            # Run migration
            migrated_count = user_repo.migrate_existing_users()

            print(f"✅ Successfully migrated {migrated_count} users")
            print(f"Added fields: gaming_stats, impact_score, preferences, social_profile, wallet_credits")

            # Verify migration
            remaining_users = user_repo.collection.count_documents({
                "$or": [
                    {"gaming_stats": {"$exists": False}},
                    {"preferences": {"$exists": False}},
                    {"wallet_credits": {"$exists": False}},
                    {"impact_score": {"$exists": False}},
                    {"social_profile": {"$exists": False}}
                ]
            })

            if remaining_users == 0:
                print("✅ Migration verification successful - all users have new fields")
                return True
            else:
                print(f"❌ Migration incomplete - {remaining_users} users still missing fields")
                return False

        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            current_app.logger.error(f"User migration failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🔄 Starting GOO-5 User Extensions Migration...")
    success = run_migration()

    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)