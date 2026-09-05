#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "firebase-admin>=6.2.0",
# ]
# ///
"""
Management script for Firebase Authentication Custom Claims.
Enforces Role-Based Access Control (RBAC) for the Google Store Assistant.

Usage via uv (standalone script execution):
    # Check active claims:
    uv run scripts/manage_admin_claims.py --project-id sre-demos --email user@example.com --list

    # Grant admin privileges:
    uv run scripts/manage_admin_claims.py --project-id sre-demos --email user@example.com --grant

    # Revoke admin privileges:
    uv run scripts/manage_admin_claims.py --project-id sre-demos --email user@example.com --revoke
"""

import argparse
import sys
import firebase_admin
from firebase_admin import auth

def init_firebase(project_id: str):
    if not firebase_admin._apps:
        try:
            firebase_admin.initialize_app(options={"projectId": project_id})
        except Exception as e:
            print(f"❌ Failed to initialize Firebase Admin SDK: {e}", file=sys.stderr)
            sys.exit(1)

def manage_claims(project_id: str, email: str, grant: bool = False, revoke: bool = False):
    init_firebase(project_id)
    
    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        print(f"\n❌ User not found with email: '{email}'")
        print("💡 The user must sign in with Google to the app at least once before claims can be attached.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fetching user: {e}\n", file=sys.stderr)
        sys.exit(1)

    claims = user.custom_claims or {}

    if grant:
        claims["sre_genai_admin"] = True
        auth.set_custom_user_claims(user.uid, claims)
        print(f"\n✅ Successfully GRANTED 'sre_genai_admin' claim to {email} (UID: {user.uid}).")
    elif revoke:
        if "sre_genai_admin" in claims:
            claims.pop("sre_genai_admin")
            auth.set_custom_user_claims(user.uid, claims)
            print(f"\n🚫 Successfully REVOKED 'sre_genai_admin' claim from {email} (UID: {user.uid}).")
        else:
            print(f"\nℹ️  User {email} does not have an active 'sre_genai_admin' claim.")

    # Fetch fresh record to verify
    updated_user = auth.get_user(user.uid)
    active_claims = updated_user.custom_claims or {}
    
    print("\n--- User Profile & Claims Status ---")
    print(f"Email:         {updated_user.email}")
    print(f"UID:           {updated_user.uid}")
    print(f"Display Name:  {updated_user.display_name}")
    print(f"Is Admin:      {active_claims.get('sre_genai_admin', False)}")
    print(f"Custom Claims: {active_claims}")
    print("------------------------------------\n")

def main():
    parser = argparse.ArgumentParser(
        description="Manage Firebase Authentication custom claims for SRE GenAI admins."
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="GCP / Firebase Project ID (e.g. 'sre-demos')."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the Google user account to manage."
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--grant",
        action="store_true",
        help="Grant administrator privileges ({'admin': True})."
    )
    group.add_argument(
        "--revoke",
        action="store_true",
        help="Revoke administrator privileges."
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="Display current custom claims without modifying them."
    )

    args = parser.parse_args()
    manage_claims(project_id=args.project_id.strip(), email=args.email.strip(), grant=args.grant, revoke=args.revoke)

if __name__ == "__main__":
    main()
