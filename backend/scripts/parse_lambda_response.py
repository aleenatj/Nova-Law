#!/usr/bin/env python3
"""Parse Lambda response and check for success status."""

import json
import sys
from pathlib import Path


def parse_lambda_response(response_file: str) -> bool:
    """Parse Lambda response and return success status.

    Args:
        response_file: Path to the JSON response file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(response_file) as f:
            data = json.load(f)

        # Parse the nested body JSON string
        body = json.loads(data.get("body", "{}"))
        result = body.get("result", {})

        success = result.get("success", False)
        message = result.get("message", "Unknown error")

        if success:
            print("✅ Operation completed successfully")
            return True
        else:
            print(f"❌ Operation failed: {message}")
            return False

    except Exception as e:
        print(f"❌ Error parsing Lambda response: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_lambda_response.py <response_file>")
        sys.exit(1)

    response_file = sys.argv[1]
    if not Path(response_file).exists():
        print(f"❌ Response file not found: {response_file}")
        sys.exit(1)

    success = parse_lambda_response(response_file)
    sys.exit(0 if success else 1)
