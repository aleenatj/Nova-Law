#!/usr/bin/env python3
"""
Encrypt ID Tool - A reusable utility to encrypt ID numbers.

This tool provides functions to encrypt and decrypt ID numbers using the application's encryption system.
It can be used as a standalone script or imported as a module.

Usage as script:
    python encrypt_id_tool.py <id_number>
    python encrypt_id_tool.py --decrypt <encrypted_id>

Usage as module:
    from encrypt_id_tool import encrypt_id, decrypt_id
    encrypted = encrypt_id(123)
    decrypted = decrypt_id(encrypted)
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.utils.encryption import encrypt_id as app_encrypt_id, decrypt_id as app_decrypt_id


def encrypt_id(id_number: int | str) -> str:
    """
    Encrypt an ID number and return the encrypted string.
    
    Args:
        id_number: The ID number to encrypt (int or string)
        
    Returns:
        The encrypted ID as a string
        
    Raises:
        ValueError: If the ID number is invalid
        Exception: If encryption fails
    """
    try:
        # Convert to string if it's an integer
        id_str = str(id_number)
        
        # Validate that it's a positive integer
        if not id_str.isdigit() or int(id_str) <= 0:
            raise ValueError(f"Invalid ID number: {id_number}. Must be a positive integer.")
        
        # Encrypt the ID
        encrypted = app_encrypt_id(id_str)
        
        if encrypted is None:
            raise Exception("Encryption failed - returned None")
            
        return encrypted
        
    except Exception as e:
        raise Exception(f"Failed to encrypt ID {id_number}: {str(e)}")


def decrypt_id(encrypted_id: str) -> int:
    """
    Decrypt an encrypted ID and return the original ID number.
    
    Args:
        encrypted_id: The encrypted ID string
        
    Returns:
        The original ID number as an integer
        
    Raises:
        ValueError: If the encrypted ID is invalid
        Exception: If decryption fails
    """
    try:
        if not encrypted_id or not isinstance(encrypted_id, str):
            raise ValueError(f"Invalid encrypted ID: {encrypted_id}")
        
        # Decrypt the ID
        decrypted = app_decrypt_id(encrypted_id)
        
        if decrypted is None:
            raise Exception("Decryption failed - returned None")
        
        # Convert to integer
        try:
            return int(decrypted)
        except ValueError:
            raise ValueError(f"Decrypted value is not a valid integer: {decrypted}")
            
    except Exception as e:
        raise Exception(f"Failed to decrypt ID {encrypted_id}: {str(e)}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt ID numbers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python encrypt_id_tool.py 123
  python encrypt_id_tool.py --decrypt abc123def456
  python encrypt_id_tool.py 456 --verify
        """
    )
    
    parser.add_argument(
        "id_value",
        help="ID number to encrypt or encrypted ID to decrypt"
    )
    
    parser.add_argument(
        "--decrypt", "-d",
        action="store_true",
        help="Decrypt the provided encrypted ID"
    )
    
    parser.add_argument(
        "--verify", "-v",
        action="store_true",
        help="Verify encryption by decrypting the result (only works with --encrypt)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output the result, no additional messages"
    )
    
    args = parser.parse_args()
    
    try:
        if args.decrypt:
            # Decrypt mode
            if not args.quiet:
                print(f"🔓 Decrypting ID: {args.id_value}")
            
            decrypted_id = decrypt_id(args.id_value)
            
            if not args.quiet:
                print(f"✅ Decrypted ID: {decrypted_id}")
            else:
                print(decrypted_id)
                
        else:
            # Encrypt mode
            try:
                id_number = int(args.id_value)
            except ValueError:
                print(f"❌ Error: '{args.id_value}' is not a valid integer")
                sys.exit(1)
            
            if not args.quiet:
                print(f"🔒 Encrypting ID: {id_number}")
            
            encrypted_id = encrypt_id(id_number)
            
            if not args.quiet:
                print(f"✅ Encrypted ID: {encrypted_id}")
            else:
                print(encrypted_id)
            
            # Verify if requested
            if args.verify:
                if not args.quiet:
                    print(f"🔍 Verifying encryption...")
                
                try:
                    decrypted = decrypt_id(encrypted_id)
                    if decrypted == id_number:
                        if not args.quiet:
                            print(f"✅ Verification successful: {decrypted}")
                    else:
                        print(f"❌ Verification failed: expected {id_number}, got {decrypted}")
                        sys.exit(1)
                except Exception as e:
                    print(f"❌ Verification failed: {e}")
                    sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
