#!/usr/bin/env python3
"""
Simple test script to verify MCP server functionality.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path for testing
sys.path.insert(0, str(Path(__file__).parent))

# Import the server module - need to get the actual function, not the tool wrapper
import mcp_sandbox_server_stdio as server_module

# Get the actual functions from the FunctionTool objects
execute = server_module.execute.fn
get_execution_info = server_module.get_execution_info.fn
list_artifacts = server_module.list_artifacts.fn
cleanup_artifacts = server_module.cleanup_artifacts.fn

def test_basic_execution():
    """Test basic code execution."""
    print("Testing basic execution...")
    code = "print('Hello from sandbox!')"
    result = execute(code)
    result_data = json.loads(result)
    
    print(f"Error: {result_data['error']}")
    print(f"Stdout: {result_data['stdout']}")
    print(f"Success: {'Hello from sandbox!' in result_data['stdout']}")
    print()

def test_package_imports():
    """Test package imports."""
    print("Testing package imports...")
    code = """
from sandbox.server.main import run_server
from sandbox.utils.helpers import helper_function

print("Server:", run_server())
print("Helper:", helper_function())
"""
    result = execute(code)
    result_data = json.loads(result)
    
    print(f"Error: {result_data['error']}")
    print(f"Stdout: {result_data['stdout']}")
    print(f"Success: {result_data['error'] is None}")
    print()

def test_import_error_handling():
    """Test import error handling."""
    print("Testing import error handling...")
    code = "import nonexistent_module"
    result = execute(code)
    result_data = json.loads(result)
    
    print(f"Error type: {result_data['error']['type'] if result_data['error'] else None}")
    print(f"Error module: {result_data['error']['module'] if result_data['error'] else None}")
    print(f"Success: {result_data['error'] is not None}")
    print()

def test_execution_info():
    """Test execution info."""
    print("Testing execution info...")
    info = get_execution_info()
    info_data = json.loads(info)
    
    print(f"Project root: {info_data['project_root']}")
    print(f"Sys path length: {info_data['sys_path_length']}")
    print(f"Success: {'/home/stan/Prod/sandbox' in info_data['sys_path_first_5']}")
    print()

def test_artifacts():
    """Test artifact functionality."""
    print("Testing artifacts...")
    artifacts_list = list_artifacts()
    print(f"Artifacts: {artifacts_list}")
    
    cleanup_result = cleanup_artifacts()
    print(f"Cleanup: {cleanup_result}")
    print()

def test_interactive_mode():
    """Test interactive mode."""
    print("Testing interactive mode...")
    code = "print('Interactive test')"
    result = execute(code, interactive=True)
    result_data = json.loads(result)
    
    print(f"Error: {result_data['error']}")
    print(f"Contains interactive: {'Interactive mode enabled' in result_data['stdout']}")
    print()

if __name__ == '__main__':
    print("Running simple MCP server tests...\n")
    
    test_basic_execution()
    test_package_imports()
    test_import_error_handling()
    test_execution_info()
    test_artifacts()
    test_interactive_mode()
    
    print("Tests completed!")
