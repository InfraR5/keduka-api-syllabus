import requests
import sys
import os

BASE_URL = "http://localhost:8004"

def identify_service():
    try:
        resp = requests.get(f"{BASE_URL}/api/course/program/openapi.json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("info", {}).get("title", "Unknown")
            print(f"ℹ️  Service Identity: '{title}'")
            return title
        else:
            print(f"⚠️ Could not fetch openapi.json: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Identity Check Failed: {e}")
        return None

def test_health():
    print(f"Checking Health at {BASE_URL}/health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Service is UP and HEALTHY.")
            return True
        else:
            print(f"❌ Service returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Service is NOT REACHABLE (Connection Error).")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_structure_validation():
    print("\nChecking API Validation (Dry Run)...")
    # Payload missing required fields to trigger 422
    try:
        resp = requests.post(f"{BASE_URL}/api/course/program/sections/create", json={})
        if resp.status_code == 422:
            print("✅ API Validation is WORKING (Received expected 422).")
        else:
            print(f"⚠️ Unexpected status {resp.status_code} for empty payload.")
    except Exception as e:
        print(f"❌ API Verification Failed: {e}")

if __name__ == "__main__":
    if test_health():
        identify_service()
        test_structure_validation()
    else:
        sys.exit(1)
