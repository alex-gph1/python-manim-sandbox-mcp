#!/usr/bin/env python3
"""
Demo script showing relative imports working within the sandbox package.
This file should be run as: python -m sandbox.demo_relative_imports
"""

def demo_relative_imports():
    """Demonstrate relative imports within the package."""
    print("Demo: Testing relative imports within sandbox package")
    
    # Relative import from server subpackage
    from .server.main import run_server, get_status
    print(f"✓ Relative import from server: {run_server()}")
    print(f"✓ Relative import from server: {get_status()}")
    
    # Relative import from utils subpackage
    from .utils.helpers import helper_function, process_data
    print(f"✓ Relative import from utils: {helper_function()}")
    print(f"✓ Relative import from utils: {process_data('relative import data')}")
    
    # Import sibling modules
    from . import server
    from . import utils
    print(f"✓ Successfully imported server subpackage: {server}")
    print(f"✓ Successfully imported utils subpackage: {utils}")

if __name__ == "__main__":
    demo_relative_imports()
