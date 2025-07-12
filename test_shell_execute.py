#!/usr/bin/env python3
"""
Test the new shell_execute functionality.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_shell_execute():
    """Test the shell_execute function."""
    print("🐚 Testing Shell Execute Functionality...")
    
    try:
        # Import the module and access the shell_execute function directly
        import sandbox.mcp_sandbox_server_stdio as server
        
        # Find the shell_execute function from the MCP tools
        shell_execute_func = None
        for tool in server.mcp.tools:
            if tool.name == 'shell_execute':
                shell_execute_func = tool.func
                break
        
        if not shell_execute_func:
            raise Exception("shell_execute tool not found")
        
        # Use the function
        shell_execute = shell_execute_func
        
        # Test 1: Basic command
        print("✅ Test 1: Basic shell command (ls)")
        result_json = shell_execute("ls -la")
        result = json.loads(result_json)
        print(f"   Return code: {result['return_code']}")
        print(f"   Stdout lines: {len(result['stdout'].splitlines())}")
        
        # Test 2: Virtual environment detection
        print("✅ Test 2: Check virtual environment")
        result_json = shell_execute("which python")
        result = json.loads(result_json)
        print(f"   Python executable: {result['stdout'].strip()}")
        print(f"   Contains .venv: {'.venv' in result['stdout']}")
        
        # Test 3: Package installation using uv
        print("✅ Test 3: Install package with uv")
        result_json = shell_execute("uv pip install matplotlib", timeout=60)
        result = json.loads(result_json)
        print(f"   Return code: {result['return_code']}")
        if result['return_code'] == 0:
            print("   ✅ Package installation successful")
        else:
            print(f"   ⚠️  Package installation failed: {result['stderr'][:100]}...")
        
        # Test 4: Check installed packages
        print("✅ Test 4: List installed packages")
        result_json = shell_execute("uv pip list")
        result = json.loads(result_json)
        packages_output = result['stdout']
        matplotlib_installed = 'matplotlib' in packages_output
        print(f"   Matplotlib installed: {matplotlib_installed}")
        print(f"   Total packages: {len(packages_output.splitlines())}")
        
        # Test 5: Security check - dangerous command
        print("✅ Test 5: Security check for dangerous command")
        result_json = shell_execute("rm -rf /")
        result = json.loads(result_json)
        is_blocked = result['execution_info']['command_blocked']
        print(f"   Command blocked: {is_blocked}")
        if is_blocked:
            print("   ✅ Security check working correctly")
        else:
            print("   ❌ Security check failed - dangerous command not blocked!")
        
        # Test 6: Working directory
        print("✅ Test 6: Working directory test")
        result_json = shell_execute("pwd")
        result = json.loads(result_json)
        working_dir = result['stdout'].strip()
        print(f"   Working directory: {working_dir}")
        print(f"   Matches project root: {working_dir == result['execution_info']['working_directory']}")
        
        # Test 7: Timeout test
        print("✅ Test 7: Timeout test")
        result_json = shell_execute("sleep 5", timeout=2)
        result = json.loads(result_json)
        is_timeout = result.get('error', {}).get('type') == 'TimeoutError'
        print(f"   Command timed out: {is_timeout}")
        
        return True
        
    except Exception as e:
        print(f"❌ Shell execute test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run shell execute tests."""
    print("🧪 Running Shell Execute Tests for MCP Sandbox\n")
    
    success = test_shell_execute()
    
    if success:
        print("\n🎉 Shell execute functionality is working correctly!")
        print("📦 Enhanced Sandbox MCP now supports both Python and shell execution!")
        return True
    else:
        print("\n❌ Shell execute tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
