#!/usr/bin/env python3
"""
Direct test of the sandbox execution functionality to verify artifact generation.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_matplotlib_artifacts():
    """Test matplotlib artifact generation directly."""
    print("🎨 Testing Matplotlib Artifact Generation...")
    
    try:
        # Import the execute function from the MCP server
        from sandbox.mcp_sandbox_server_stdio import ctx, monkey_patch_matplotlib, monkey_patch_pil
        
        # Create artifacts directory
        artifacts_dir = ctx.create_artifacts_dir()
        print(f"✅ Created artifacts directory: {artifacts_dir}")
        
        # Apply monkey patches
        matplotlib_patched = monkey_patch_matplotlib()
        pil_patched = monkey_patch_pil()
        print(f"✅ Matplotlib patched: {matplotlib_patched}")
        print(f"✅ PIL patched: {pil_patched}")
        
        if not matplotlib_patched:
            print("❌ Matplotlib not available - skipping test")
            return False
        
        # Test code that generates a plot
        test_code = '''
import matplotlib
matplotlib.use('Agg')  # Ensure non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Generate test data
x = np.linspace(0, 4*np.pi, 200)
y1 = np.sin(x)
y2 = np.cos(x)

# Create subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Plot 1: Sine wave
ax1.plot(x, y1, 'b-', linewidth=2, label='sin(x)')
ax1.set_xlabel('x (radians)')
ax1.set_ylabel('y')
ax1.set_title('Sine Wave - MCP Sandbox Artifact Test')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Cosine wave
ax2.plot(x, y2, 'r-', linewidth=2, label='cos(x)')
ax2.set_xlabel('x (radians)')
ax2.set_ylabel('y')
ax2.set_title('Cosine Wave - MCP Sandbox Artifact Test')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()  # This should be intercepted by monkey patch

print("Matplotlib plots generated successfully!")
print(f"Figure count: {len(plt.get_fignums())}")
'''
        
        # Execute the test code
        print("🚀 Executing matplotlib test code...")
        exec(test_code, ctx.execution_globals)
        print("✅ Code executed without errors")
        
        # Check for artifacts
        artifacts_path = Path(artifacts_dir)
        if artifacts_path.exists():
            artifacts = list(artifacts_path.glob("*.png"))
            print(f"✅ Found {len(artifacts)} PNG artifacts:")
            
            for i, artifact in enumerate(artifacts):
                size = artifact.stat().st_size
                print(f"   {i+1}. {artifact.name} ({size:,} bytes)")
                
                # Verify the file is a valid PNG
                if size > 1000:  # PNG files should be reasonable size
                    print(f"      ✅ Artifact appears valid (size: {size:,} bytes)")
                else:
                    print(f"      ⚠️  Artifact may be too small (size: {size} bytes)")
            
            return len(artifacts) > 0
        else:
            print("❌ Artifacts directory not found")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling functionality."""
    print("\n⚠️  Testing Error Handling...")
    
    try:
        from sandbox.mcp_sandbox_server_stdio import ctx
        
        error_code = "import definitely_nonexistent_module_12345"
        
        try:
            exec(error_code, ctx.execution_globals)
            print("❌ Expected ImportError was not raised")
            return False
        except ImportError as e:
            print(f"✅ ImportError correctly raised: {e}")
            return True
        except Exception as e:
            print(f"❌ Unexpected error type: {type(e).__name__}: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_sys_path_configuration():
    """Test sys.path configuration."""
    print("\n🔧 Testing sys.path Configuration...")
    
    try:
        from sandbox.mcp_sandbox_server_stdio import ctx
        
        print(f"✅ Project root: {ctx.project_root}")
        print(f"✅ Virtual env: {ctx.venv_path}")
        print(f"✅ sys.path length: {len(sys.path)}")
        print(f"✅ First 3 sys.path entries:")
        for i, path in enumerate(sys.path[:3], 1):
            print(f"   {i}. {path}")
        
        # Test package import
        try:
            import sandbox
            print(f"✅ Sandbox package imported from: {sandbox.__file__}")
            return True
        except ImportError as e:
            print(f"❌ Failed to import sandbox package: {e}")
            return False
            
    except Exception as e:
        print(f"❌ sys.path test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running Direct Execution Tests for MCP Sandbox\n")
    
    test_results = []
    
    # Test 1: sys.path configuration
    test_results.append(test_sys_path_configuration())
    
    # Test 2: Matplotlib artifacts
    test_results.append(test_matplotlib_artifacts())
    
    # Test 3: Error handling
    test_results.append(test_error_handling())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MCP Sandbox is ready for production.")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
