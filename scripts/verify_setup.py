#!/usr/bin/env python3
"""
Backend self-check: run this whenever something seems broken, before
suspecting the frontend. It talks to your running backend directly over
HTTP (no browser, no CORS, no frontend code involved), so it tells you
definitively whether the problem is in the backend or somewhere else.

Usage:
    1. Start the backend:  uvicorn app.main:app --reload   (from backend/)
    2. In another terminal, from the repo root:
           python scripts/verify_setup.py

Exits non-zero and prints exactly what failed if anything is wrong.
"""
import sys
import time
import uuid

import requests

BASE_URL = "http://localhost:8000"


def check(label, fn):
    print(f"  {label} ... ", end="", flush=True)
    try:
        fn()
        print("OK")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {e}")
        return False


def main():
    print(f"Talkify backend self-check against {BASE_URL}\n")
    results = []

    # 1. Is the package versions actually what requirements.txt pins?
    def check_versions():
        import fastapi
        if fastapi.__version__ != "0.115.0":
            raise AssertionError(
                f"Installed FastAPI is {fastapi.__version__}, expected 0.115.0. "
                f"A mismatched version can cause routes to silently 404. "
                f"Fix with: pip install fastapi==0.115.0 starlette==0.38.6"
            )
    results.append(check("FastAPI version matches requirements.txt", check_versions))

    # 2. Is the server even reachable?
    def check_health():
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if r.status_code != 200:
            raise AssertionError(f"Expected 200, got {r.status_code}: {r.text}")
    results.append(check("Server is reachable (/api/health)", check_health))

    # 3. Does the OpenAPI schema actually list the auth routes?
    #    (This directly answers "is my running server's code the code I
    #    think it is" — if these are missing, you're not running the code
    #    in this repo, or a mismatched FastAPI version is hiding routes.)
    def check_routes_exist():
        r = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        paths = r.json().get("paths", {})
        required = ["/api/auth/register", "/api/auth/login", "/api/documents", "/api/chat/conversations"]
        missing = [p for p in required if p not in paths]
        if missing:
            raise AssertionError(
                f"These routes are missing from the running server: {missing}. "
                f"Restart the backend, and if it persists, check the FastAPI "
                f"version check above."
            )
    results.append(check("Expected routes are registered", check_routes_exist))

    # 4. Full register -> login -> me round trip with a throwaway account.
    def check_auth_roundtrip():
        email = f"selfcheck-{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Self Check", "email": email, "password": "password123",
        }, timeout=10)
        if r.status_code != 201:
            raise AssertionError(f"Register failed: {r.status_code} {r.text}")
        token = r.json()["access_token"]

        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email, "password": "password123",
        }, timeout=10)
        if r.status_code != 200:
            raise AssertionError(f"Login failed: {r.status_code} {r.text}")

        r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code != 200:
            raise AssertionError(f"/me failed: {r.status_code} {r.text}")
    results.append(check("Register -> login -> /me round trip", check_auth_roundtrip))

    print()
    if all(results):
        print("Everything checks out. If the frontend still fails, the issue is")
        print("likely CORS_ORIGINS, VITE_API_URL, or a browser cache — see")
        print("docs/SETUP.md's troubleshooting section.")
        sys.exit(0)
    else:
        print("One or more checks failed — see the FAILED lines above for the fix.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        import requests  # noqa: F401
    except ImportError:
        print("This script needs the 'requests' package: pip install requests")
        sys.exit(1)
    main()
