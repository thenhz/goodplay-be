#!/usr/bin/env python3
"""Test script for notification endpoints"""

import requests
import json
import sys

BASE_URL = "http://localhost:5004/api"

# Test credentials
import time
email = f"notification_test_{int(time.time())}@example.com"
password = "TestPassword123!"


def test_register():
    """Register a new test user"""
    print("1. Registering user...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": "Notification Test User"
        }
    )
    print(f"   Response: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"   Success: {data.get('message')}")
        # Extract token from nested structure
        tokens = data.get('data', {}).get('tokens', {})
        return tokens.get('access_token')
    else:
        print(f"   Error: {response.text}")
        return None


def test_login():
    """Login with test user"""
    print("2. Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    print(f"   Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data.get('message')}")
        return data.get('data', {}).get('access_token')
    else:
        print(f"   Error: {response.text}")
        return None


def test_device_management(token):
    """Test device management endpoints"""
    print("\n=== DEVICE MANAGEMENT TESTS ===")
    headers = {"Authorization": f"Bearer {token}"}

    # Register device
    print("\n3. Registering device...")
    response = requests.post(
        f"{BASE_URL}/devices/register",
        headers=headers,
        json={
            "device_token": "test_fcm_token_12345",
            "platform": "android",
            "device_id": "test_device_001",
            "device_info": {
                "model": "Pixel 6",
                "os_version": "Android 13",
                "app_version": "1.0.0"
            }
        }
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")

    # Unregister device
    print("\n4. Unregistering device...")
    response = requests.delete(
        f"{BASE_URL}/devices/unregister",
        headers=headers,
        json={"device_id": "test_device_001"}
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")


def test_notifications(token):
    """Test notification inbox endpoints"""
    print("\n=== NOTIFICATION INBOX TESTS ===")
    headers = {"Authorization": f"Bearer {token}"}

    # Get notifications
    print("\n5. Getting notifications...")
    response = requests.get(
        f"{BASE_URL}/notifications?limit=10&offset=0",
        headers=headers
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")

    # Get unread count
    print("\n6. Getting unread count...")
    response = requests.get(
        f"{BASE_URL}/notifications/unread-count",
        headers=headers
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")

    # Mark all as read
    print("\n7. Marking all as read...")
    response = requests.put(
        f"{BASE_URL}/notifications/read-all",
        headers=headers
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")

    # Clear all notifications
    print("\n8. Clearing all notifications...")
    response = requests.delete(
        f"{BASE_URL}/notifications",
        headers=headers
    )
    print(f"   Response: {response.status_code}")
    print(f"   Data: {json.dumps(response.json(), indent=2)}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("NOTIFICATION SYSTEM API TESTS")
    print("=" * 60)

    # Try to register or login
    token = test_register()
    if not token:
        token = test_login()

    if not token:
        print("\n❌ Failed to authenticate. Cannot continue tests.")
        sys.exit(1)

    print(f"\n✅ Authentication successful!")
    print(f"   Token: {token[:20]}...")

    # Run tests
    test_device_management(token)
    test_notifications(token)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()