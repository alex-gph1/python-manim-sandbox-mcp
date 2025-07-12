"""
Sandbox - Python Code Execution Environment

Enhanced Python code execution sandbox with FastMCP server integration,
designed for secure and feature-rich code execution with artifact management
and web application support.
"""

__version__ = "0.1.0"
__author__ = "Sandbox Development Team"
__description__ = "Python code execution sandbox with FastMCP server integration"

# Core modules
from . import server, utils
from . import mcp_sandbox_server, mcp_sandbox_server_stdio

__all__ = [
    'server',
    'utils', 
    'mcp_sandbox_server',
    'mcp_sandbox_server_stdio',
    '__version__',
    '__author__',
    '__description__'
]
