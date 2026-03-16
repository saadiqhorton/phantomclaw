#!/usr/bin/env python3
"""
DEPRECATED SHIM - This file will be removed in a future refactor.

Canonical path: tools/repo/sentinel.py

This shim exists for backward compatibility only.
Please update your scripts to use: tools/repo/sentinel.py
"""
import os
import sys

# Add tools directory to path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import from the new location
from tools.repo.sentinel import check_repo

if __name__ == "__main__":
    # Re-parse arguments since we're importing the function
    if len(sys.argv) < 2:
        print("Usage: python tools/repo/sentinel.py <path_to_repo>")
        print("(Deprecated: python tools/repo_sentinel.py <path_to_repo> also works)")
        sys.exit(1)

    check_repo(sys.argv[1])
