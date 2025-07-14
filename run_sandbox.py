#!/usr/bin/env python3
"""
Sandbox Runner

A simple script to run the sandbox in various modes.

Usage:
    python run_sandbox.py playground    # Interactive playground
    python run_sandbox.py mcp-http      # MCP HTTP server
    python run_sandbox.py mcp-stdio     # MCP STDIO server
    python run_sandbox.py test          # Run tests
"""

import sys
import subprocess
from pathlib import Path

def run_playground():
    """Run the interactive playground."""
    print("🎮 Starting Sandbox Playground...")
    subprocess.run([sys.executable, "playground.py"])

def run_mcp_http():
    """Run the MCP HTTP server."""
    print("🌐 Starting MCP HTTP Server on port 8765...")
    subprocess.run([sys.executable, "-m", "sandbox.mcp_sandbox_server"])

def run_mcp_stdio():
    """Run the MCP STDIO server."""
    print("📡 Starting MCP STDIO Server...")
    subprocess.run([sys.executable, "-m", "sandbox.mcp_sandbox_server_stdio"])

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_sandbox.py [playground|mcp-http|mcp-stdio|test]")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "playground":
        run_playground()
    elif mode == "mcp-http":
        run_mcp_http()
    elif mode == "mcp-stdio":
        run_mcp_stdio()
    elif mode == "test":
        run_tests()
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: playground, mcp-http, mcp-stdio, test")
        sys.exit(1)

if __name__ == "__main__":
    main()
