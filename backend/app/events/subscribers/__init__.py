"""
Event Subscribers Package

This package contains all event subscriber modules.
Each module contains subscribers for specific event types.
"""

import importlib
import pkgutil
from pathlib import Path

# Auto-discover and import all .py files in this directory
for _finder, module_name, _ispkg in pkgutil.iter_modules([str(Path(__file__).parent)]):
    if module_name != "__init__":
        importlib.import_module(f".{module_name}", __package__)

# Import all subscriber modules to ensure they are registered
# from . import user, test_events

# __all__ = [
#     "user",
#     "test_events",
#     # Add any new modules here as they're created
# ]
