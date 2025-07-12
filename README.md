# Sandbox MCP

> Production-ready MCP server for secure Python code execution with artifact capture, virtual environment support, and LM Studio integration

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.5-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/scooter-lacroix/sandbox-mcp.git
cd sandbox-mcp

# Install with uv (recommended)
uv venv && uv pip install -e .

# Run the MCP server
uv run sandbox-server-stdio
```

## ✨ Features

### 🔧 **Robust Python Execution**
- **Virtual Environment Detection**: Auto-detects and activates `.venv`
- **Dynamic sys.path Management**: Intelligent path resolution
- **Persistent Context**: Variables persist across executions
- **Enhanced Error Handling**: Detailed ImportError diagnostics

### 🎨 **Automatic Artifact Capture**
- **Matplotlib Integration**: Auto-saves plots via `plt.show()` monkey-patching
- **PIL/Pillow Support**: Captures images from `Image.show()`
- **Base64 Encoding**: Embeds artifacts directly in responses
- **Smart Cleanup**: Configurable temp directory management

### 🌐 **Web Application Support**
- **Flask & Streamlit**: Launch web apps with auto port detection
- **Process Management**: Track and manage running servers
- **URL Generation**: Returns accessible endpoints

### 🐊 **Safe Shell Execution**
- **Command Security**: Filters dangerous operations (rm -rf, sudo, etc.)
- **Virtual Environment**: Inherits activated environment settings
- **Timeout Control**: Configurable execution timeouts
- **Working Directory**: Custom execution contexts

### 🔌 **MCP Integration**
- **Dual Transport**: HTTP and stdio support
- **LM Studio Ready**: Drop-in integration for AI models
- **FastMCP Powered**: Modern MCP implementation

## 📦 Installation

### Prerequisites
- Python 3.9+
- uv (recommended) or pip

### Using uv (Recommended)

```bash
git clone https://github.com/scooter-lacroix/sandbox-mcp.git
cd sandbox-mcp
uv venv
uv pip install -e .
```

### Using pip

```bash
git clone https://github.com/scooter-lacroix/sandbox-mcp.git
cd sandbox-mcp
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
pip install -e .
```

## 🖥️ Usage

### Command Line Interface

```bash
# Start HTTP server (web integration)
sandbox-server

# Start stdio server (LM Studio integration)
sandbox-server-stdio
```

### LM Studio Integration

Add to your LM Studio MCP configuration:

```json
{
  "mcpServers": {
    "sandbox": {
      "command": "sandbox-server-stdio",
      "args": []
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `execute` | Execute Python code with artifact capture |
| `shell_execute` | Execute shell commands safely with security filtering |
| `list_artifacts` | List generated artifacts |
| `cleanup_artifacts` | Clean up temporary files |
| `get_execution_info` | Get environment diagnostics |
| `start_repl` | Start interactive session |
| `start_web_app` | Launch Flask/Streamlit apps |
| `cleanup_temp_artifacts` | Maintenance operations |

## 💡 Examples

### Basic Python Execution

```python
# Execute simple code
result = execute(code="print('Hello, World!')")
```

### Matplotlib Artifact Generation

```python
code = """
import matplotlib.pyplot as plt
import numpy as np

# Generate plot
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.show()  # Automatically captured as artifact
"""

result = execute(code)
# Returns JSON with base64-encoded PNG
```

### Flask Web Application

```python
flask_code = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Sandbox Flask App</h1>'

@app.route('/api/status')
def status():
    return jsonify({"status": "running", "server": "sandbox"})
"""

result = start_web_app(flask_code, "flask")
# Returns URL where app is accessible
```

### Shell Command Execution

```python
# Install packages via shell
result = shell_execute("uv pip install matplotlib")

# Check environment
result = shell_execute("which python")

# List directory contents
result = shell_execute("ls -la")

# Custom working directory and timeout
result = shell_execute(
    "find . -name '*.py' | head -10", 
    working_directory="/path/to/search",
    timeout=60
)
```

### Error Handling

```python
# Import error with detailed diagnostics
result = execute(code="import nonexistent_module")
# Returns structured error with sys.path info

# Security-blocked shell command
result = shell_execute("rm -rf /")
# Returns security error with blocked pattern info
```

## 🏗️ Architecture

### Project Structure

```
sandbox-mcp/
├── src/
│   └── sandbox/                   # Main package
│       ├── __init__.py           # Package initialization
│       ├── mcp_sandbox_server.py # HTTP MCP server
│       ├── mcp_sandbox_server_stdio.py # stdio MCP server
│       ├── server/               # Server modules
│       │   ├── __init__.py
│       │   └── main.py
│       └── utils/                # Utility modules
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── test_integration.py       # Main test suite
│   └── test_simple_integration.py
├── pyproject.toml                # Package configuration
├── README.md                     # This file
├── .gitignore
└── uv.lock                       # Dependency lock file
```

### Core Components

#### ExecutionContext
Manages the execution environment:
- **Project Root Detection**: Dynamic path resolution
- **Virtual Environment**: Auto-detection and activation
- **sys.path Management**: Intelligent path handling
- **Artifact Management**: Temporary directory lifecycle
- **Global State**: Persistent execution context

#### Monkey Patching System
Non-intrusive artifact capture:
- **matplotlib.pyplot.show()**: Intercepts and saves plots
- **PIL.Image.show()**: Captures image displays
- **Conditional Patching**: Only applies if libraries available
- **Original Functionality**: Preserved through wrapper functions

#### MCP Integration
FastMCP-powered server with:
- **Dual Transport**: HTTP and stdio protocols
- **Tool Registry**: 7 available MCP tools
- **Streaming Support**: Ready for real-time interaction
- **Error Handling**: Structured error responses

## Testing

### Run All Tests
```bash
# Using uv
uv run pytest

# Using pytest directly
pytest tests/ -v

# Using unittest
python -m unittest tests.test_integration -v
```

### Test Categories

1. **Package Import Tests**: Verify absolute import functionality
2. **sys.path Tests**: Ensure correct path configuration
3. **Error Handling Tests**: Enhanced ImportError reporting
4. **Artifact Tests**: Matplotlib and PIL integration
5. **Web App Tests**: Flask and Streamlit launching
6. **Environment Tests**: Virtual environment detection

## Configuration

### pyproject.toml Features

- **Entry Points**: CLI command definitions
- **Package Discovery**: Automatic package detection
- **Build System**: Hatchling backend configuration
- **Test Configuration**: pytest integration
- **Dependencies**: FastMCP, matplotlib, Pillow

### Environment Variables

- `VIRTUAL_ENV`: Set automatically when `.venv` detected
- `PATH`: Modified to include `.venv/bin`
- Standard Python environment variables supported

## Error Handling

### Enhanced ImportError Reporting

When imports fail, detailed information is provided:
```json
{
  "type": "ImportError",
  "message": "No module named 'nonexistent'",
  "module": "nonexistent",
  "traceback": "Full traceback...",
  "sys_path": ["path1", "path2", "..."],
  "attempted_paths": ["existing_path1", "existing_path2"]
}
```

### General Exception Handling

All exceptions include:
- Exception type and message
- Full traceback
- Execution context information
- sys.path snapshot

## Integration with LM Studio

### MCP Configuration

Add to LM Studio MCP settings:
```json
{
  "mcpServers": {
    "sandbox": {
      "command": "sandbox-server-stdio",
      "args": []
    }
  }
}
```

### Available Tools in LM Studio

- `execute`: Run Python code with full feature set
- `list_artifacts`: View generated artifacts
- `cleanup_artifacts`: Clean up temporary files  
- `get_execution_info`: Environment diagnostics
- `start_repl`: Interactive session (simulated)
- `start_web_app`: Launch web applications
- `cleanup_temp_artifacts`: Maintenance operations

## Development

### Adding New Features

1. **Update ExecutionContext**: Add new environment setup
2. **Create MCP Tools**: Add new `@mcp.tool` decorated functions  
3. **Update Tests**: Add test cases in `test_integration.py`
4. **Update Documentation**: Document new functionality

### Code Style

- Follow existing patterns for error handling
- Use structured JSON returns for tool functions
- Maintain backward compatibility
- Add comprehensive logging

## Troubleshooting

### Import Issues
- Check `get_execution_info()` for sys.path configuration
- Verify virtual environment activation
- Ensure package is installed in development mode (`pip install -e .`)

### Virtual Environment Issues
- Confirm `.venv` directory exists
- Check Python version compatibility
- Verify `VIRTUAL_ENV` environment variable

### Artifact Issues
- Ensure temporary directory is writable
- Check matplotlib/PIL installation
- Verify artifact cleanup is working

### Web App Issues
- Confirm Flask/Streamlit installation
- Check port availability (8000-8099 range)
- Verify firewall settings

## Contributing

1. **Setup Development Environment**:
   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```

2. **Run Tests**: Ensure all tests pass before submitting changes

3. **Follow Patterns**: Use existing code patterns for consistency

4. **Update Documentation**: Keep README and docstrings current

## License

[Apache License](LICENSE)

## Changelog

### v0.1.0
- Initial enhanced package structure
- Dynamic project root detection
- Robust virtual environment integration
- Enhanced error handling with detailed tracebacks
- Artifact management with matplotlib/PIL support
- Web application launching (Flask/Streamlit)
- Comprehensive test suite
- MCP server integration (HTTP and stdio)
- CLI entry points
- LM Studio compatibility
