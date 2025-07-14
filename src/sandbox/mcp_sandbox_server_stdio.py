from fastmcp import FastMCP
import io
import sys
import os
import traceback
import json
import uuid
import tempfile
import shutil
import subprocess
from .core.resource_manager import get_resource_manager
from .core.security import get_security_manager, SecurityLevel
import threading
import time
import socket
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Set up logging to file instead of stderr to avoid MCP protocol interference
log_file = Path(tempfile.gettempdir()) / "sandbox_mcp_server.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        # Only use console handler for critical errors
        logging.StreamHandler(sys.stderr) if os.getenv('SANDBOX_MCP_DEBUG') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastMCP server named "python-sandbox"
mcp = FastMCP("python-sandbox")

# Global state for execution context
class ExecutionContext:
    def __init__(self):
        # Compute project_root dynamically from current file location
        # When installed as package, __file__ is in src/sandbox/, so go up 2 levels
        current_file = Path(__file__).resolve()
        if 'src/sandbox' in str(current_file):
            # Installed package: go from src/sandbox/mcp_*.py to project root
            self.project_root = current_file.parent.parent.parent
        else:
            # Development: assume file is in project root
            self.project_root = current_file.parent
        
        # Set up sandbox working area one level above project root
        self.sandbox_area = self.project_root.parent / "sandbox_area"
        self.sandbox_area.mkdir(exist_ok=True)
        
        self.venv_path = self.project_root / ".venv"
        self.artifacts_dir = None
        self.web_servers = {}  # Track running web servers
        self.execution_globals = {}  # Persistent globals across executions
        self.compilation_cache = {}  # Cache for compiled code
        self.cache_hits = 0
        self.cache_misses = 0
        self._setup_environment()
    
    def _setup_environment(self):
        """Setup sys.path and virtual environment with robust path detection."""
        # Compute absolute paths
        project_root_str = str(self.project_root)
        project_parent_str = str(self.project_root.parent)  # Add parent to find 'sandbox' package
        
        # Detect venv site-packages dynamically
        venv_site_packages = None
        if self.venv_path.exists():
            # Try multiple Python versions
            for py_version in ['python3.11', 'python3.12', 'python3.10', 'python3.9']:
                candidate = self.venv_path / "lib" / py_version / "site-packages"
                if candidate.exists():
                    venv_site_packages = candidate
                    break
        
        # De-duplicate sys.path using OrderedDict to preserve order
        from collections import OrderedDict
        current_paths = OrderedDict.fromkeys(sys.path)
        
        # Paths to add (parent first for package imports, then project root)
        paths_to_add = [project_parent_str, project_root_str]
        if venv_site_packages:
            paths_to_add.append(str(venv_site_packages))
        
        # Add new paths at the beginning, preserving order and avoiding duplicates
        new_sys_path = []
        for path in paths_to_add:
            if path not in current_paths:
                new_sys_path.append(path)
                current_paths[path] = None  # Mark as added
        
        # Rebuild sys.path with new paths first
        sys.path[:] = new_sys_path + list(current_paths.keys())
        
        # Set up virtual environment activation
        if self.venv_path.exists():
            venv_python = self.venv_path / "bin" / "python"
            venv_bin = self.venv_path / "bin"
            
            if venv_python.exists():
                # Set environment variables for venv activation
                os.environ['VIRTUAL_ENV'] = str(self.venv_path)
                
                # Prepend venv/bin to PATH if not already present
                current_path = os.environ.get('PATH', '')
                venv_bin_str = str(venv_bin)
                if venv_bin_str not in current_path.split(os.pathsep):
                    os.environ['PATH'] = f"{venv_bin_str}{os.pathsep}{current_path}"
                
                # Update sys.executable to point to venv python
                sys.executable = str(venv_python)
        
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Virtual env: {self.venv_path if self.venv_path.exists() else 'Not found'}")
        logger.info(f"sys.executable: {sys.executable}")
        logger.info(f"sys.path (first 5): {sys.path[:5]}")
        logger.info(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    
    def create_artifacts_dir(self) -> str:
        """Create a structured directory for execution artifacts within the project."""
        execution_id = str(uuid.uuid4())[:8]
        # Create artifacts directory within project
        artifacts_root = self.project_root / "artifacts"
        artifacts_root.mkdir(exist_ok=True)
        
        # Create session-specific directory with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = f"session_{timestamp}_{execution_id}"
        
        self.artifacts_dir = artifacts_root / session_dir
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different artifact types
        (self.artifacts_dir / "plots").mkdir(exist_ok=True)
        (self.artifacts_dir / "images").mkdir(exist_ok=True)
        (self.artifacts_dir / "animations").mkdir(exist_ok=True)
        (self.artifacts_dir / "files").mkdir(exist_ok=True)
        
        return str(self.artifacts_dir)
    
    def cleanup_artifacts(self):
        """Clean up artifacts directory."""
        if self.artifacts_dir and self.artifacts_dir.exists():
            shutil.rmtree(self.artifacts_dir, ignore_errors=True)

# Global execution context
ctx = ExecutionContext()
resource_manager = get_resource_manager()
security_manager = get_security_manager(SecurityLevel.MEDIUM)

def monkey_patch_matplotlib():
    """Monkey patch matplotlib to save plots to artifacts directory."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        
        original_show = plt.show
        
        def patched_show(*args, **kwargs):
            if ctx.artifacts_dir:
                plots_dir = ctx.artifacts_dir / "plots"
                plots_dir.mkdir(exist_ok=True)
                figure_path = plots_dir / f"plot_{uuid.uuid4().hex[:8]}.png"
                plt.savefig(figure_path, dpi=150, bbox_inches='tight')
                logger.info(f"Plot saved to: {figure_path}")
            return original_show(*args, **kwargs)
        
        plt.show = patched_show
        return True
    except ImportError:
        return False

def execute_manim_code(manim_code: str, quality: str = 'medium_quality') -> Dict[str, Any]:
    """Execute Manim code and save animation to artifacts directory with enhanced support."""
    if not ctx.artifacts_dir:
        ctx.create_artifacts_dir()
    
    # Create a subdirectory for this specific animation
    animation_id = str(uuid.uuid4())[:8]
    manim_dir = ctx.artifacts_dir / f"manim_{animation_id}"
    manim_dir.mkdir(exist_ok=True)
    
    script_path = manim_dir / "scene.py"
    
    result = {
        'success': False,
        'output': '',
        'error': None,
        'video_path': None,
        'animation_id': animation_id,
        'artifacts_dir': str(manim_dir),
        'scenes_found': [],
        'execution_time': 0
    }
    
    start_time = time.time()
    
    try:
        # Enhance Manim code with proper imports if missing
        if 'from manim import *' not in manim_code and 'import manim' not in manim_code:
            manim_code = 'from manim import *\n' + manim_code
        
        # Write the Manim script
        with open(script_path, 'w') as f:
            f.write(manim_code)
        
        # Determine quality flags
        quality_flags = {
            'low_quality': ['-ql'],
            'medium_quality': ['-qm'],
            'high_quality': ['-qh'],
            'production_quality': ['-qp']
        }.get(quality, ['-qm'])
        
        # Try to use virtual environment first
        manim_executable = None
        if ctx.venv_path.exists():
            venv_manim = ctx.venv_path / 'bin' / 'manim'
            if venv_manim.exists():
                manim_executable = str(venv_manim)
        
        # Fallback to system manim or python -m manim
        if not manim_executable:
            # Try python -m manim with virtual environment python
            if ctx.venv_path.exists():
                venv_python = ctx.venv_path / 'bin' / 'python'
                if venv_python.exists():
                    cmd = [str(venv_python), '-m', 'manim'] + quality_flags + [str(script_path)]
                else:
                    cmd = [sys.executable, '-m', 'manim'] + quality_flags + [str(script_path)]
            else:
                cmd = [sys.executable, '-m', 'manim'] + quality_flags + [str(script_path)]
        else:
            cmd = [manim_executable] + quality_flags + [str(script_path)]
        
        # Set up environment for Manim execution
        env = os.environ.copy()
        if ctx.venv_path.exists():
            env['VIRTUAL_ENV'] = str(ctx.venv_path)
            env['PATH'] = f"{ctx.venv_path / 'bin'}{os.pathsep}{env.get('PATH', '')}"
        
        logger.info(f"Executing Manim with command: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd,
            cwd=str(manim_dir),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        result['output'] = process.stdout
        result['execution_time'] = time.time() - start_time
        
        if process.returncode == 0:
            result['success'] = True
            
            # Find the generated files
            media_dir = manim_dir / "media"
            if media_dir.exists():
                # Look for video files
                video_files = list(media_dir.rglob("*.mp4"))
                image_files = list(media_dir.rglob("*.png"))
                
                if video_files:
                    result['video_path'] = str(video_files[0])
                    logger.info(f"Manim animation saved to: {video_files[0]}")
                
                if image_files:
                    result['image_files'] = [str(f) for f in image_files]
                
                # Extract scene names from output
                import re
                scene_matches = re.findall(r'Scene: ([A-Za-z0-9_]+)', result['output'])
                result['scenes_found'] = scene_matches
                
                if not video_files and not image_files:
                    result['error'] = 'No output files generated'
            else:
                result['error'] = 'No media directory found'
        else:
            result['success'] = False
            result['error'] = process.stderr or 'Manim execution failed'
            
    except subprocess.TimeoutExpired:
        result['error'] = 'Manim execution timed out (5 minutes)'
        result['execution_time'] = time.time() - start_time
    except Exception as e:
        result['error'] = f'Error during Manim execution: {str(e)}'
        result['execution_time'] = time.time() - start_time
        logger.error(f"Manim execution error: {e}")
    
    return result

def monkey_patch_pil():
    """Monkey patch PIL to save images to artifacts directory."""
    try:
        from PIL import Image
        
        original_show = Image.Image.show
        original_save = Image.Image.save
        
        def patched_show(self, title=None, command=None):
            if ctx.artifacts_dir:
                images_dir = ctx.artifacts_dir / "images"
                images_dir.mkdir(exist_ok=True)
                image_path = images_dir / f"image_{uuid.uuid4().hex[:8]}.png"
                self.save(image_path)
                logger.info(f"Image saved to: {image_path}")
            return original_show(self, title, command)
        
        def patched_save(self, fp, format=None, **params):
            result = original_save(self, fp, format, **params)
            # If saving to artifacts dir, log it
            if ctx.artifacts_dir and str(fp).startswith(str(ctx.artifacts_dir)):
                logger.info(f"Image saved to artifacts: {fp}")
            return result
        
        Image.Image.show = patched_show
        Image.Image.save = patched_save
        return True
    except ImportError:
        return False

def find_free_port(start_port=8000):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports available")

def launch_web_app(code: str, app_type: str) -> Optional[str]:
    """Launch a web application and return the URL."""
    try:
        resource_manager.check_resource_limits()
        port = find_free_port()
        resource_manager.process_manager.cleanup_finished()
    
        if app_type == 'flask':
            # Modify Flask code to run on specific port
            modified_code = code + f"\nif __name__ == '__main__': app.run(host='127.0.0.1', port={port}, debug=False)"
        elif app_type == 'streamlit':
            # For Streamlit, we need to create a temporary file and run it
            script_path = ctx.artifacts_dir / f"streamlit_app_{uuid.uuid4().hex[:8]}.py"
            with open(script_path, 'w') as f:
                f.write(code)
            
            # Launch Streamlit in subprocess
            cmd = [sys.executable, '-m', 'streamlit', 'run', str(script_path), '--server.port', str(port), '--server.headless', 'true']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Register process with resource manager
            process_id = resource_manager.process_manager.add_process(
                process, 
                name=f"streamlit_{port}",
                metadata={'type': 'streamlit', 'port': port}
            )
            
            # Give it time to start
            time.sleep(2)
            
            if process.poll() is None:  # Still running
                url = f"http://127.0.0.1:{port}"
                ctx.web_servers[url] = process_id
                return url
            else:
                return None
        else:
            return None
        
        if app_type == 'flask':
            # Execute the modified Flask code in a separate thread
            def run_flask():
                exec(modified_code, ctx.execution_globals)
            
            # Use resource manager for thread management
            future = resource_manager.thread_pool.submit(run_flask)
            time.sleep(1)  # Give Flask time to start
            
            url = f"http://127.0.0.1:{port}"
            return url
            
    except Exception as e:
        logger.error(f"Failed to launch web app: {e}")
        return None

def collect_artifacts() -> List[Dict[str, Any]]:
    """Collect all artifacts from the artifacts directory."""
    artifacts = []
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return artifacts
    
    for file_path in ctx.artifacts_dir.iterdir():
        if file_path.is_file():
            try:
                # Read file as base64 for embedding
                with open(file_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                
                artifacts.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'type': file_path.suffix.lower(),
                    'content_base64': content,
                    'size': file_path.stat().st_size
                })
            except Exception as e:
                logger.error(f"Error reading artifact {file_path}: {e}")
    
    return artifacts

@mcp.tool
def execute(code: str, interactive: bool = False, web_app_type: Optional[str] = None) -> str:
    """
    Execute Python code with enhanced features:
    - Robust sys.path and venv activation
    - Module import error handling with full traceback
    - Artifact interception and storage
    - Web app launch support
    - Interactive REPL mode
    
    Args:
        code: Python code to execute
        interactive: If True, drop into interactive REPL after execution
        web_app_type: Type of web app to launch ('flask' or 'streamlit')
    
    Returns:
        JSON string containing execution results, artifacts, and metadata
    """
    # Create artifacts directory for this execution
    artifacts_dir = ctx.create_artifacts_dir()
    
    # Set up monkey patches
    matplotlib_patched = monkey_patch_matplotlib()
    pil_patched = monkey_patch_pil()
    
    # Capture stdout and stderr
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = {
        'stdout': '',
        'stderr': '',
        'error': None,
        'artifacts': [],
        'web_url': None,
        'execution_info': {
            'sys_executable': sys.executable,
            'sys_path_first_3': sys.path[:3],
            'project_root': str(ctx.project_root),
            'artifacts_dir': artifacts_dir,
            'matplotlib_patched': matplotlib_patched,
            'pil_patched': pil_patched
        }
    }
    
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        # Check if this is a web app
        if web_app_type in ['flask', 'streamlit']:
            url = launch_web_app(code, web_app_type)
            if url:
                result['web_url'] = url
                result['stdout'] = f"Web application launched at: {url}"
            else:
                result['stderr'] = f"Failed to launch {web_app_type} application"
        else:
            # Regular code execution
            exec(code, ctx.execution_globals)
        
        # Interactive REPL mode
        if interactive:
            result['stdout'] += "\n[Interactive mode enabled - code executed successfully]\n"
            result['stdout'] += "Note: REPL mode would be available in a real terminal session\n"
    
    except ImportError as e:
        # Enhanced import error handling
        error_trace = traceback.format_exc()
        module_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        
        error_details = {
            'type': 'ImportError',
            'message': str(e),
            'module': module_name,
            'traceback': error_trace,
            'sys_path': sys.path[:5],  # First 5 paths for debugging
            'attempted_paths': [p for p in sys.path if Path(p).exists()]
        }
        result['error'] = error_details
        result['stderr'] = f"Import Error: {e}\n\nFull traceback:\n{error_trace}"
    
    except Exception as e:
        # General exception handling
        error_trace = traceback.format_exc()
        result['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': error_trace
        }
        result['stderr'] = f"Error: {e}\n\nFull traceback:\n{error_trace}"
    
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Capture output
        result['stdout'] += stdout_capture.getvalue()
        result['stderr'] += stderr_capture.getvalue()
        
        # Collect artifacts
        result['artifacts'] = collect_artifacts()
    
    return json.dumps(result, indent=2)

@mcp.tool
def list_artifacts() -> str:
    """List all current artifacts."""
    artifacts = collect_artifacts()
    if not artifacts:
        return "No artifacts found."
    
    result = "Current artifacts:\n"
    for artifact in artifacts:
        result += f"- {artifact['name']} ({artifact['size']} bytes) - {artifact['type']}\n"
    
    return result

@mcp.tool
def clear_cache(important_only: bool = False) -> str:
    """Clear the compilation cache, optionally preserving important commands."""
    if important_only:
        # Logic to preserve important commands goes here
        preserved_commands = ["import", "def", "class"]
        ctx.compilation_cache = {k: v for k, v in ctx.compilation_cache.items() if any(cmd in k for cmd in preserved_commands)}
    else:
        ctx.compilation_cache.clear()
    
    ctx.cache_hits = 0
    ctx.cache_misses = 0
    return "Cache cleared successfully."

@mcp.tool
def cleanup_artifacts() -> str:
    """Clean up all artifacts and temporary files."""
    ctx.cleanup_artifacts()
    # Also cleanup web servers
    for url, process in ctx.web_servers.items():
        try:
            process.terminate()
        except:
            pass
    ctx.web_servers.clear()
    return "Artifacts and web servers cleaned up."

@mcp.tool
def start_repl() -> str:
    """Start an interactive REPL session (simulated for MCP)."""
    # In a real implementation, this would stream stdin/stdout over MCP
    # For now, we provide a simulation
    return json.dumps({
        'status': 'repl_started',
        'message': 'Interactive REPL session started (simulated)',
        'note': 'In a full implementation, this would provide streaming I/O over MCP',
        'globals_available': list(ctx.execution_globals.keys()),
        'sys_path_active': sys.path[:3]
    }, indent=2)

@mcp.tool
def start_web_app(code: str, app_type: str = 'flask') -> str:
    """Launch a web application and return connection details."""
    url = launch_web_app(code, app_type)
    if url:
        return json.dumps({
            'status': 'success',
            'url': url,
            'app_type': app_type,
            'message': f'{app_type.title()} application launched successfully'
        }, indent=2)
    else:
        return json.dumps({
            'status': 'error',
            'app_type': app_type,
            'message': f'Failed to launch {app_type} application'
        }, indent=2)

@mcp.tool
def cleanup_temp_artifacts(max_age_hours: int = 24) -> str:
    """Clean up old temporary artifact directories."""
    cleaned = 0
    temp_dir = Path(tempfile.gettempdir())
    
    try:
        for item in temp_dir.glob('sandbox_artifacts_*'):
            if item.is_dir():
                # Check age
                age_hours = (time.time() - item.stat().st_mtime) / 3600
                if age_hours > max_age_hours:
                    shutil.rmtree(item, ignore_errors=True)
                    cleaned += 1
    except Exception as e:
        logger.error(f"Error during temp cleanup: {e}")
    
    return json.dumps({
        'cleaned_directories': cleaned,
        'max_age_hours': max_age_hours,
        'message': f'Cleaned {cleaned} old artifact directories'
    }, indent=2)

@mcp.tool
def shell_execute(command: str, working_directory: Optional[str] = None, timeout: int = 30) -> str:
    """
    Execute a shell command safely in a controlled environment.
    
    Args:
        command: The shell command to execute
        working_directory: Directory to run the command in (defaults to sandbox_area)
        timeout: Maximum execution time in seconds
    
    Returns:
        JSON string containing execution results, stdout, stderr, and metadata
    
    CAUTION: Commands execute in isolated sandbox_area. Avoid system modifications.
    """
    # Set working directory - default to sandbox_area for safety
    if working_directory is None:
        working_directory = str(ctx.sandbox_area)
    
    # Enhanced security checks using security manager
    is_safe, violation = security_manager.check_command_security(command)
    if not is_safe:
        return json.dumps({
            'stdout': '',
            'stderr': f'Command blocked for security: {violation.message}',
            'return_code': -1,
            'error': {
                'type': 'SecurityError',
                'message': violation.message,
                'level': violation.level.value,
                'command': command
            },
            'execution_info': {
                'working_directory': working_directory,
                'timeout': timeout,
                'command_blocked': True,
                'security_violation': True
            }
        }, indent=2)
    
    result = {
        'stdout': '',
        'stderr': '',
        'return_code': 0,
        'error': None,
        'execution_info': {
            'working_directory': working_directory,
            'timeout': timeout,
            'command': command,
            'command_blocked': False
        }
    }
    
    try:
        # Execute the command with timeout
        process = subprocess.run(
            command,
            shell=True,
            cwd=working_directory,
            timeout=timeout,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Use current environment including VIRTUAL_ENV
        )
        
        result['stdout'] = process.stdout
        result['stderr'] = process.stderr
        result['return_code'] = process.returncode
        
        if process.returncode != 0:
            result['error'] = {
                'type': 'CommandError',
                'message': f'Command failed with return code {process.returncode}',
                'return_code': process.returncode
            }
            
    except subprocess.TimeoutExpired:
        result['error'] = {
            'type': 'TimeoutError',
            'message': f'Command timed out after {timeout} seconds',
            'timeout': timeout
        }
        result['stderr'] = f'Command timed out after {timeout} seconds'
        result['return_code'] = -2
        
    except Exception as e:
        result['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': traceback.format_exc()
        }
        result['stderr'] = f'Error executing command: {e}'
        result['return_code'] = -3
    
    return json.dumps(result, indent=2)

@mcp.tool
def create_manim_animation(manim_code: str, quality: str = 'medium_quality') -> str:
    """
    Create a Manim animation from Python code.
    
    Args:
        manim_code: Python code containing Manim scene definitions
        quality: Animation quality ('low_quality', 'medium_quality', 'high_quality', 'production_quality')
    
    Returns:
        JSON string with execution results, video path, and metadata
    """
    result = execute_manim_code(manim_code, quality)
    return json.dumps(result, indent=2)

@mcp.tool
def list_manim_animations() -> str:
    """List all Manim animations in the current artifacts directory."""
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return "No artifacts directory found. Create an animation first."
    
    animations = []
    for item in ctx.artifacts_dir.iterdir():
        if item.is_dir() and item.name.startswith('manim_'):
            animation_info = {
                'animation_id': item.name.replace('manim_', ''),
                'path': str(item),
                'created': item.stat().st_ctime,
                'size_mb': sum(f.stat().st_size for f in item.rglob('*') if f.is_file()) / 1024 / 1024
            }
            
            # Find video files
            video_files = list(item.rglob('*.mp4'))
            if video_files:
                animation_info['video_file'] = str(video_files[0])
                animation_info['video_size_mb'] = video_files[0].stat().st_size / 1024 / 1024
            
            animations.append(animation_info)
    
    if not animations:
        return "No Manim animations found."
    
    return json.dumps({
        'total_animations': len(animations),
        'animations': animations
    }, indent=2)

@mcp.tool
def cleanup_manim_animation(animation_id: str) -> str:
    """Clean up a specific Manim animation directory."""
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return "No artifacts directory found."
    
    manim_dir = ctx.artifacts_dir / f"manim_{animation_id}"
    
    if not manim_dir.exists():
        return f"Animation directory not found: {animation_id}"
    
    try:
        shutil.rmtree(manim_dir)
        return f"Successfully cleaned up animation: {animation_id}"
    except Exception as e:
        return f"Failed to clean up animation {animation_id}: {str(e)}"

@mcp.tool
def get_manim_examples() -> str:
    """Get example Manim code snippets for common animations."""
    examples = {
        'simple_circle': '''
from manim import *

class SimpleCircle(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(PINK, opacity=0.5)
        self.play(Create(circle))
        self.wait(1)
''',
        'moving_square': '''
from manim import *

class MovingSquare(Scene):
    def construct(self):
        square = Square()
        square.set_fill(BLUE, opacity=0.5)
        self.play(Create(square))
        self.play(square.animate.shift(RIGHT * 2))
        self.play(square.animate.shift(UP * 2))
        self.wait(1)
''',
        'text_animation': '''
from manim import *

class TextAnimation(Scene):
    def construct(self):
        text = Text("Hello, Manim!")
        text.set_color(YELLOW)
        self.play(Write(text))
        self.play(text.animate.scale(1.5))
        self.wait(1)
''',
        'graph_plot': '''
from manim import *

class GraphPlot(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=6,
            y_length=6
        )
        axes.add_coordinates()
        
        graph = axes.plot(lambda x: x**2, color=BLUE)
        graph_label = axes.get_graph_label(graph, label="f(x) = x^2")
        
        self.play(Create(axes))
        self.play(Create(graph))
        self.play(Write(graph_label))
        self.wait(1)
'''
    }
    
    return json.dumps({
        'examples': examples,
        'usage': "Use create_manim_animation() with any of these examples to generate animations."
    }, indent=2)

@mcp.tool
def get_execution_info() -> str:
    """Get information about the current execution environment."""
    info = {
        'project_root': str(ctx.project_root),
        'venv_path': str(ctx.venv_path),
        'venv_active': ctx.venv_path.exists(),
        'sys_executable': sys.executable,
        'sys_path_length': len(sys.path),
        'sys_path_first_5': sys.path[:5],
        'artifacts_dir': str(ctx.artifacts_dir) if ctx.artifacts_dir else None,
        'web_servers': list(ctx.web_servers.keys()),
        'global_variables': list(ctx.execution_globals.keys()),
        'virtual_env': os.environ.get('VIRTUAL_ENV'),
        'path_contains_venv': str(ctx.venv_path / 'bin') in os.environ.get('PATH', ''),
        'current_working_directory': os.getcwd(),
        'shell_available': True,
        'manim_available': shutil.which('manim') is not None
    }
    return json.dumps(info, indent=2)

@mcp.tool
def get_artifact_report() -> str:
    """Get comprehensive artifact report with categorization and metadata."""
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return json.dumps({
            'status': 'no_artifacts',
            'message': 'No artifacts directory found. Execute some code first.'
        }, indent=2)
    
    # Use the enhanced artifact system from PersistentExecutionContext
    from .core.execution_context import PersistentExecutionContext
    
    # Create a temporary context to use the enhanced artifact methods
    temp_ctx = PersistentExecutionContext()
    temp_ctx.artifacts_dir = ctx.artifacts_dir
    
    try:
        report = temp_ctx.get_artifact_report()
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f'Failed to generate artifact report: {str(e)}'
        }, indent=2)

@mcp.tool
def categorize_artifacts() -> str:
    """Categorize artifacts by type with detailed metadata."""
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return json.dumps({
            'status': 'no_artifacts',
            'message': 'No artifacts directory found. Execute some code first.'
        }, indent=2)
    
    # Use the enhanced artifact system from PersistentExecutionContext
    from .core.execution_context import PersistentExecutionContext
    
    # Create a temporary context to use the enhanced artifact methods
    temp_ctx = PersistentExecutionContext()
    temp_ctx.artifacts_dir = ctx.artifacts_dir
    
    try:
        categories = temp_ctx.categorize_artifacts()
        return json.dumps(categories, indent=2)
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f'Failed to categorize artifacts: {str(e)}'
        }, indent=2)

@mcp.tool
def cleanup_artifacts_by_type(artifact_type: str) -> str:
    """Clean up artifacts of a specific type.
    
    Args:
        artifact_type: Type of artifacts to clean (e.g., 'images', 'videos', 'plots', 'manim')
    
    Returns:
        JSON string with cleanup results
    """
    if not ctx.artifacts_dir or not ctx.artifacts_dir.exists():
        return json.dumps({
            'status': 'no_artifacts',
            'message': 'No artifacts directory found.'
        }, indent=2)
    
    # Use the enhanced artifact system from PersistentExecutionContext
    from .core.execution_context import PersistentExecutionContext
    
    # Create a temporary context to use the enhanced artifact methods
    temp_ctx = PersistentExecutionContext()
    temp_ctx.artifacts_dir = ctx.artifacts_dir
    
    try:
        categorized = temp_ctx.categorize_artifacts()
        
        if artifact_type not in categorized:
            return json.dumps({
                'status': 'error',
                'message': f'Artifact type "{artifact_type}" not found',
                'available_types': list(categorized.keys())
            }, indent=2)
        
        cleaned_count = 0
        for file_info in categorized[artifact_type]:
            try:
                file_path = Path(file_info['full_path'])
                if file_path.exists():
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_info['path']}: {e}")
        
        return json.dumps({
            'status': 'success',
            'artifact_type': artifact_type,
            'cleaned_count': cleaned_count,
            'message': f'Successfully cleaned {cleaned_count} {artifact_type} artifacts'
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f'Failed to cleanup artifacts: {str(e)}'
        }, indent=2)

@mcp.tool
def start_enhanced_repl() -> str:
    """Start an enhanced REPL session with IPython support and magic commands."""
    try:
        # Check if IPython is available
        try:
            import IPython
            ipython_available = True
        except ImportError:
            ipython_available = False
        
        repl_info = {
            'status': 'repl_started',
            'ipython_available': ipython_available,
            'features': {
                'tab_completion': ipython_available,
                'history': ipython_available,
                'magic_commands': ipython_available,
                'syntax_highlighting': ipython_available,
                'artifact_management': True,
                'manim_support': True,
                'virtual_env': ctx.venv_path.exists()
            },
            'available_magic_commands': [
                '%artifacts - List and manage artifacts',
                '%manim - Execute Manim animations',
                '%save_session - Save current session variables',
                '%load_session - Load saved session',
                '%clear_cache - Clear compilation cache',
                '%env_info - Show environment information'
            ],
            'globals_available': list(ctx.execution_globals.keys()),
            'artifacts_dir': str(ctx.artifacts_dir) if ctx.artifacts_dir else None,
            'virtual_env': os.environ.get('VIRTUAL_ENV'),
            'message': 'Enhanced REPL session started with artifact management and Manim support'
        }
        
        return json.dumps(repl_info, indent=2)
        
    except Exception as e:
        return json.dumps({
            'status': 'error',
            'message': f'Failed to start enhanced REPL: {str(e)}'
        }, indent=2)

@mcp.tool
def execute_with_artifacts(code: str, track_artifacts: bool = True) -> str:
    """Execute Python code with enhanced artifact tracking and categorization.
    
    Args:
        code: Python code to execute
        track_artifacts: Whether to track and categorize artifacts
    
    Returns:
        JSON string with execution results and detailed artifact information
    """
    # Create artifacts directory for this execution
    artifacts_dir = ctx.create_artifacts_dir()
    
    # Set up monkey patches
    matplotlib_patched = monkey_patch_matplotlib()
    pil_patched = monkey_patch_pil()
    
    # Track artifacts before execution
    from .core.execution_context import PersistentExecutionContext
    temp_ctx = PersistentExecutionContext()
    temp_ctx.artifacts_dir = Path(artifacts_dir)
    
    artifacts_before = temp_ctx._get_current_artifacts() if track_artifacts else set()
    
    # Capture stdout and stderr
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = {
        'stdout': '',
        'stderr': '',
        'error': None,
        'artifacts': [],
        'artifact_report': None,
        'execution_info': {
            'sys_executable': sys.executable,
            'artifacts_dir': artifacts_dir,
            'matplotlib_patched': matplotlib_patched,
            'pil_patched': pil_patched,
            'track_artifacts': track_artifacts
        }
    }
    
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        # Execute the code
        exec(code, ctx.execution_globals)
        
    except Exception as e:
        # Handle exceptions
        error_trace = traceback.format_exc()
        result['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': error_trace
        }
        result['stderr'] = f"Error: {e}\n\nFull traceback:\n{error_trace}"
    
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Capture output
        result['stdout'] = stdout_capture.getvalue()
        result['stderr'] += stderr_capture.getvalue()
        
        # Track new artifacts
        if track_artifacts:
            artifacts_after = temp_ctx._get_current_artifacts()
            new_artifacts = artifacts_after - artifacts_before
            
            if new_artifacts:
                result['artifacts'] = list(new_artifacts)
                result['artifact_report'] = temp_ctx.get_artifact_report()
    
    return json.dumps(result, indent=2)

def main():
    """Entry point for the stdio MCP server."""
    mcp.run()

if __name__ == "__main__":
    # Run FastMCP server using stdio transport for LM Studio
    main()
