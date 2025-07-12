#!/usr/bin/env python3
"""
Simple test of shell execution functionality using subprocess directly.
"""

import subprocess
import os
import sys
import json
from pathlib import Path

def test_shell_functionality():
    """Test shell execution capabilities."""
    print("🐚 Testing Shell Execution Capabilities...")
    
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"
    
    # Set up environment like the MCP server does
    env = os.environ.copy()
    if venv_path.exists():
        env['VIRTUAL_ENV'] = str(venv_path)
        venv_bin = str(venv_path / "bin")
        if venv_bin not in env.get('PATH', ''):
            env['PATH'] = f"{venv_bin}:{env.get('PATH', '')}"
    
    print(f"✅ Project root: {project_root}")
    print(f"✅ Virtual env: {venv_path} ({'exists' if venv_path.exists() else 'missing'})")
    
    tests = [
        ("Basic command", "echo 'Hello Shell!'"),
        ("Environment check", "which python"),
        ("Working directory", "pwd"),
        ("List files", "ls -la | head -5"),
        ("Virtual env check", "echo $VIRTUAL_ENV"),
    ]
    
    passed = 0
    for test_name, command in tests:
        try:
            print(f"\n🔧 {test_name}:")
            print(f"   Command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(project_root),
                timeout=10,
                capture_output=True,
                text=True,
                env=env
            )
            
            print(f"   Return code: {result.returncode}")
            print(f"   Stdout: {result.stdout.strip()[:100]}")
            if result.stderr:
                print(f"   Stderr: {result.stderr.strip()[:100]}")
            
            if result.returncode == 0:
                print("   ✅ Success")
                passed += 1
            else:
                print("   ⚠️  Non-zero return code")
                
        except subprocess.TimeoutExpired:
            print("   ❌ Command timed out")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

def test_package_installation():
    """Test package installation via shell."""
    print("\n📦 Testing Package Installation...")
    
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"
    
    # Set up environment
    env = os.environ.copy()
    if venv_path.exists():
        env['VIRTUAL_ENV'] = str(venv_path)
        venv_bin = str(venv_path / "bin")
        if venv_bin not in env.get('PATH', ''):
            env['PATH'] = f"{venv_bin}:{env.get('PATH', '')}"
    
    try:
        # Install matplotlib if not already installed
        print("🔧 Installing matplotlib via uv...")
        result = subprocess.run(
            "uv pip install matplotlib",
            shell=True,
            cwd=str(project_root),
            timeout=60,
            capture_output=True,
            text=True,
            env=env
        )
        
        print(f"   Return code: {result.returncode}")
        if result.returncode == 0:
            print("   ✅ Installation successful")
            
            # Verify installation
            verify_result = subprocess.run(
                "uv pip list | grep matplotlib",
                shell=True,
                cwd=str(project_root),
                timeout=10,
                capture_output=True,
                text=True,
                env=env
            )
            
            if verify_result.returncode == 0:
                print(f"   ✅ Verified: {verify_result.stdout.strip()}")
                return True
            else:
                print("   ⚠️  Installation not verified")
                return False
        else:
            print(f"   ❌ Installation failed: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Installation timed out")
        return False
    except Exception as e:
        print(f"   ❌ Installation error: {e}")
        return False

def main():
    """Run all shell tests."""
    print("🧪 Testing Enhanced Sandbox Shell Capabilities\n")
    
    basic_passed = test_shell_functionality()
    install_passed = test_package_installation()
    
    if basic_passed and install_passed:
        print("\n🎉 All shell execution tests passed!")
        print("📦 Enhanced Sandbox MCP is ready with both Python and shell execution!")
        return True
    else:
        print("\n❌ Some shell tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
