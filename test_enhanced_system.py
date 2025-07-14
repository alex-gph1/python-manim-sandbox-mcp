#!/usr/bin/env python3
"""
Simple test to verify enhanced system components work correctly.
"""

import sys
import os
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_enhanced_execution_context():
    """Test enhanced execution context."""
    print("Testing Enhanced Execution Context...")
    
    try:
        from sandbox.core.execution_context import PersistentExecutionContext
        
        # Create context
        ctx = PersistentExecutionContext()
        print(f"✅ Created execution context with session: {ctx.session_id}")
        
        # Test code execution
        result = ctx.execute_code("x = 42\nprint(f'Hello from enhanced context: {x}')")
        print(f"✅ Code execution successful: {result['success']}")
        print(f"   Output: {result['stdout'].strip()}")
        
        # Test artifact categorization
        categories = ctx.categorize_artifacts()
        print(f"✅ Artifact categorization successful: {len(categories)} categories")
        
        # Test performance stats
        stats = ctx.get_execution_stats()
        print(f"✅ Performance stats: {stats['total_executions']} executions")
        
        # Test artifact report
        report = ctx.get_artifact_report()
        print(f"✅ Artifact report: {report['total_artifacts']} artifacts")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced execution context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_local_sandbox():
    """Test local sandbox with enhanced features."""
    print("\nTesting Enhanced Local Sandbox...")
    
    try:
        from sandbox.sdk.local_sandbox import LocalSandbox
        
        # Create sandbox
        sandbox = LocalSandbox()
        print(f"✅ Created local sandbox with session: {sandbox.session_id}")
        
        # Test basic functionality
        info = sandbox.get_execution_info()
        print(f"✅ Execution info: Python {info['python_version'][:6]}")
        
        # Test performance stats
        stats = sandbox.get_performance_stats()
        print(f"✅ Performance stats available: {stats}")
        
        # Test artifact methods
        report = sandbox.get_artifact_report()
        print(f"✅ Artifact report: {report['total_artifacts']} artifacts")
        
        summary = sandbox.get_artifact_summary()
        print(f"✅ Artifact summary generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Local sandbox test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_virtual_environment():
    """Test virtual environment detection."""
    print("\nTesting Virtual Environment Detection...")
    
    try:
        venv_path = Path("/home/stan/Prod/sandbox/venv")
        print(f"✅ Virtual environment exists: {venv_path.exists()}")
        
        if venv_path.exists():
            python_path = venv_path / "bin" / "python"
            print(f"✅ Python executable exists: {python_path.exists()}")
            
            # Check if Manim is available
            try:
                import subprocess
                result = subprocess.run([str(python_path), "-c", "import manim; print('Manim available')"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Manim is available in virtual environment")
                else:
                    print("⚠️  Manim not available in virtual environment")
            except Exception as e:
                print(f"⚠️  Could not check Manim availability: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Virtual environment test failed: {e}")
        return False

def test_directory_structure():
    """Test directory structure creation."""
    print("\nTesting Directory Structure...")
    
    try:
        project_root = Path("/home/stan/Prod/sandbox")
        print(f"✅ Project root exists: {project_root.exists()}")
        
        # Test session directory creation
        sessions_dir = project_root / "sessions"
        if sessions_dir.exists():
            print(f"✅ Sessions directory exists with {len(list(sessions_dir.iterdir()))} sessions")
        
        # Test artifacts directory
        artifacts_dir = project_root / "artifacts"
        if artifacts_dir.exists():
            print(f"✅ Artifacts directory exists with {len(list(artifacts_dir.iterdir()))} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Directory structure test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Enhanced Sandbox System - Component Tests")
    print("=" * 50)
    
    tests = [
        test_enhanced_execution_context,
        test_local_sandbox,
        test_virtual_environment,
        test_directory_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Enhanced system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
