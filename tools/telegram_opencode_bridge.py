#!/usr/bin/env python3
"""
DEPRECATED SHIM - This file will be removed in a future refactor.

Canonical path: tools/telegram/bridge.py

This shim exists for backward compatibility only.
Please update your scripts to use: tools/telegram/bridge.py
"""
import os
import sys

# Add tools directory to path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import and run from the new location
from tools.telegram.bridge import main

if __name__ == "__main__":
    main()
