"""
Script to test secrets decryption.

Usage:
    python scripts/test_secrets.py
"""

import getpass
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

from utils.secrets_manager import SecretsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test secrets decryption."""
    print("=" * 60)
    print("🔍 DMarket Bot - Secrets Test Tool")
    print("=" * 60)
    print()

    # Get master password
    master_password = getpass.getpass("Enter master password: ")

    # Initialize manager
    try:
        manager = SecretsManager(master_password)
    except Exception as e:
        print(f"❌ Failed to initialize secrets manager: {e}")
        sys.exit(1)

    # List all secrets
    secrets = manager.list_secrets()
    print(f"\n📋 Found {len(secrets)} secrets:")
    for secret in secrets:
        print(f"  - {secret}")

    print()

    # Test decryption
    print("🔓 Testing decryption...")
    success_count = 0
    fail_count = 0

    for secret_name in secrets:
        value = manager.decrypt_secret(secret_name)
        if value:
            print(f"  ✅ {secret_name}: OK (length: {len(value)})")
            success_count += 1
        else:
            print(f"  ❌ {secret_name}: FAILED")
            fail_count += 1

    print()
    print("=" * 60)
    print(f"Results: {success_count} succeeded, {fail_count} failed")

    if fail_count == 0:
        print("✅ All secrets decrypted successfully!")
    else:
        print("❌ Some secrets failed to decrypt. Check master password.")
        sys.exit(1)


if __name__ == "__main__":
    main()
