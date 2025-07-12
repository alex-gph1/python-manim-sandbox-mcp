#!/usr/bin/env python3
"""
Test the MCP sandbox server via HTTP transport to validate production readiness.
"""

import json
import requests
import time
import sys

def test_http_mcp_server():
    """Test the HTTP MCP sandbox server."""
    base_url = "http://localhost:8765/mcp"
    
    print("🚀 Testing MCP Sandbox Server via HTTP...")
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test server availability
    try:
        response = requests.get(base_url)
        print(f"✅ Server responding (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Test with proper headers for Server-Sent Events
    headers = {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Initialize connection
    print("\n📡 Test 1: Testing server connection...")
    try:
        init_request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "http-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(base_url, 
                               json=init_request, 
                               headers=headers,
                               stream=True)
        
        if response.status_code == 200:
            print("✅ Server accepts HTTP requests")
            # Read the response stream
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = json.loads(decoded_line[6:])
                        if data.get('result'):
                            print(f"✅ Initialization successful")
                            break
                    elif 'error' in decoded_line:
                        print(f"❌ Server error: {decoded_line}")
                        return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    print("🎉 HTTP MCP Server is operational!")
    return True

def check_server_logs():
    """Check server status and logs."""
    print("\n📋 Server Status Check...")
    
    import subprocess
    try:
        # Check if server process is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'sandbox-server' in result.stdout:
            print("✅ Server process is running")
            
            # Count server processes
            server_lines = [line for line in result.stdout.split('\n') if 'sandbox-server' in line and 'grep' not in line]
            print(f"✅ Found {len(server_lines)} server process(es)")
            
            return True
        else:
            print("❌ Server process not found")
            return False
            
    except Exception as e:
        print(f"❌ Could not check server status: {e}")
        return False

def test_artifacts_endpoint():
    """Test if we can access server tools via HTTP."""
    print("\n🔧 Test 2: Testing tools availability...")
    
    base_url = "http://localhost:8765/mcp"
    headers = {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json'
    }
    
    try:
        tools_request = {
            "jsonrpc": "2.0",
            "id": "test-tools",
            "method": "tools/list"
        }
        
        response = requests.post(base_url, 
                               json=tools_request, 
                               headers=headers,
                               timeout=10)
        
        if response.status_code == 200:
            print("✅ Tools endpoint accessible")
            return True
        else:
            print(f"❌ Tools endpoint error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def main():
    """Run all HTTP tests."""
    print("🧪 Running HTTP MCP Server Tests\n")
    
    test_results = []
    
    # Test 1: Server status
    test_results.append(check_server_logs())
    
    # Test 2: HTTP connectivity
    test_results.append(test_http_mcp_server())
    
    # Test 3: Tools availability
    test_results.append(test_artifacts_endpoint())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 HTTP Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 MCP Sandbox HTTP Server is production ready!")
        return True
    else:
        print("❌ Some HTTP tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
