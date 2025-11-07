#!/usr/bin/env python3
"""
Generate a secure API key for Service-to-Service Authentication

This script generates a cryptographically secure random API key
suitable for the SERVICE_API_KEY environment variable.

Usage:
    python generate_api_key.py [--length LENGTH]

Examples:
    python generate_api_key.py
    python generate_api_key.py --length 64
"""

import secrets
import argparse
import sys


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.
    
    Args:
        length: Number of random bytes to generate (default: 32)
                The resulting string will be longer due to base64 encoding
    
    Returns:
        A URL-safe base64-encoded random string
    """
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a secure API key for service-to-service authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate a 32-byte key (default):
    python generate_api_key.py
  
  Generate a 64-byte key:
    python generate_api_key.py --length 64
  
  Save to .env file:
    python generate_api_key.py >> .env
        """
    )
    
    parser.add_argument(
        '--length',
        type=int,
        default=32,
        help='Length of random bytes to generate (default: 32)'
    )
    
    parser.add_argument(
        '--format',
        choices=['env', 'raw', 'both'],
        default='both',
        help='Output format: env (SERVICE_API_KEY=...), raw (just the key), or both (default)'
    )
    
    args = parser.parse_args()
    
    # Validate length
    if args.length < 16:
        print("⚠️  Warning: API key length is less than 16 bytes. This may not be secure.", file=sys.stderr)
        print("Recommended minimum: 32 bytes", file=sys.stderr)
    
    # Generate the key
    api_key = generate_api_key(args.length)
    
    # Output based on format
    if args.format == 'raw':
        print(api_key)
    elif args.format == 'env':
        print(f"SERVICE_API_KEY={api_key}")
    else:  # both
        print("=" * 80)
        print("🔑 Service-to-Service API Key Generated")
        print("=" * 80)
        print()
        print("Add this to your .env file:")
        print()
        print(f"SERVICE_API_KEY={api_key}")
        print()
        print("=" * 80)
        print("⚠️  Security Reminders:")
        print("  - Never commit this key to version control")
        print("  - Use the same key in Monitor_Atlas and Monitor_Hermes")
        print("  - Store it securely (use secret manager in production)")
        print("  - Rotate the key every 90 days")
        print("=" * 80)


if __name__ == "__main__":
    main()
