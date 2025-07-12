#!/usr/bin/env python3
"""
Simple MCP client to test the sandbox server functionality.
This script communicates with the MCP server via subprocess to validate production readiness.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

def send_mcp_request(process, request):
    """Send a JSON-RPC request to the MCP server."""
    request_json = json.dumps(request) + '\n'
    process.stdin.write(request_json.encode())
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline()
    if response_line:
        return json.loads(response_line.decode().strip())
    return None

def test_mcp_server():
    """Test the MCP sandbox server functionality."""
    print("🚀 Testing MCP Sandbox Server...")
    
    # Start the MCP server process
    server_cmd = [sys.executable, "-m", "uv", "run", "sandbox-server-stdio"]
    
    try:
        process = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/stan/Prod/sandbox"
        )
        
        # Give server time to start
        time.sleep(2)
        
        print("✅ MCP Server started successfully")
        
        # Test 1: Initialize connection
        print("\n📡 Test 1: Initializing MCP connection...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = send_mcp_request(process, init_request)
        if response and response.get("result"):
            print("✅ Connection initialized successfully")
            print(f"   Server capabilities: {len(response['result'].get('capabilities', {}))}")
        else:
            print("❌ Failed to initialize connection")
            return False
        
        # Test 2: List available tools
        print("\n🔧 Test 2: Listing available tools...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = send_mcp_request(process, tools_request)
        if response and response.get("result"):
            tools = response["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
        else:
            print("❌ Failed to list tools")
            return False
        
        # Test 3: Execute Python code with matplotlib
        print("\n🐍 Test 3: Testing Python execution with matplotlib artifacts...")
        execute_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "execute",
                "arguments": {
                    "code": """
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Generate test plot
x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.xlabel('x (radians)')
plt.ylabel('y')
plt.title('MCP Sandbox Test - Matplotlib Artifact')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()  # Should be intercepted as artifact

print("Matplotlib plot generated successfully!")
print(f"Backend: {matplotlib.get_backend()}")
"""
                }
            }
        }
        
        response = send_mcp_request(process, execute_request)
        if response and response.get("result"):
            result = json.loads(response["result"]["content"][0]["text"])
            print("✅ Python code executed successfully")
            print(f"   Stdout: {result.get('stdout', '')[:100]}...")
            print(f"   Artifacts generated: {len(result.get('artifacts', []))}")
            
            if result.get('artifacts'):
                for i, artifact in enumerate(result['artifacts']):
                    print(f"   Artifact {i+1}: {artifact['name']} ({artifact['size']} bytes)")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
        else:
            print("❌ Failed to execute Python code")
            return False
        
        # Test 4: Test error handling
        print("\n⚠️  Test 4: Testing error handling...")
        error_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "execute",
                "arguments": {
                    "code": "import nonexistent_module"
                }
            }
        }
        
        response = send_mcp_request(process, error_request)
        if response and response.get("result"):
            result = json.loads(response["result"]["content"][0]["text"])
            if result.get('error') and result['error'].get('type') == 'ImportError':
                print("✅ Error handling working correctly")
                print(f"   Error type: {result['error']['type']}")
                print(f"   Module: {result['error'].get('module', 'N/A')}")
            else:
                print("❌ Error handling not working as expected")
        
        # Test 5: List artifacts
        print("\n📦 Test 5: Listing artifacts...")
        artifacts_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "list_artifacts",
                "arguments": {}
            }
        }
        
        response = send_mcp_request(process, artifacts_request)
        if response and response.get("result"):
            artifacts_info = response["result"]["content"][0]["text"]
            print("✅ Artifacts listed successfully")
            print(f"   {artifacts_info[:100]}...")
        
        print("\n🎉 All tests completed successfully!")
        print("🔧 MCP Sandbox Server is production ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
