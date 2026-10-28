#!/usr/bin/env python3
"""Setup script for Nova Law Backend."""

import subprocess  # nosec B404


# Get version from pyproject.toml
def get_version():
    """Extract version from pyproject.toml."""
    try:
        result = subprocess.run(  # nosec B602, B607, B603
            ["poetry", "version", "-s"],
            capture_output=True,
            text=True,
            shell=True,
            check=False,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return "1.0.0"
