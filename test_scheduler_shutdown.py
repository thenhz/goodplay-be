#!/usr/bin/env python3
"""Test script to verify scheduler shutdown works without errors"""

import os
import time
import signal
import subprocess
import sys

def test_shutdown():
    """Start app and gracefully shut it down to test scheduler shutdown"""
    print("=" * 60)
    print("TESTING SCHEDULER SHUTDOWN")
    print("=" * 60)

    # Start the app in a subprocess
    print("\n1. Starting Flask app...")
    env = os.environ.copy()
    env['PORT'] = '5010'

    process = subprocess.Popen(
        ['python', 'app.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for app to start
    print("2. Waiting for app to initialize (5 seconds)...")
    time.sleep(5)

    # Send SIGTERM to gracefully shut down
    print("3. Sending SIGTERM to gracefully shut down...")
    process.send_signal(signal.SIGTERM)

    # Wait for process to finish
    print("4. Waiting for shutdown to complete...")
    try:
        stdout, stderr = process.communicate(timeout=10)

        print("\n" + "=" * 60)
        print("SHUTDOWN COMPLETED")
        print("=" * 60)

        # Check for the error we're trying to fix
        error_found = False
        if "RuntimeError: Working outside of application context" in stderr:
            print("\n❌ FAILED: Scheduler shutdown error still present!")
            error_found = True
        else:
            print("\n✅ SUCCESS: No scheduler shutdown errors!")

        # Show last 20 lines of stderr
        print("\n" + "-" * 60)
        print("Last 20 lines of STDERR:")
        print("-" * 60)
        stderr_lines = stderr.split('\n')
        for line in stderr_lines[-20:]:
            if line.strip():
                print(line)

        return not error_found

    except subprocess.TimeoutExpired:
        print("\n❌ FAILED: Process did not shut down within 10 seconds")
        process.kill()
        return False

if __name__ == "__main__":
    success = test_shutdown()
    sys.exit(0 if success else 1)