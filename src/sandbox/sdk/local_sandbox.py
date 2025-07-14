"""
Local sandbox implementation for the enhanced Sandbox SDK.
"""

import io
import sys
import os
import traceback
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_sandbox import BaseSandbox
from .execution import Execution
from ..mcp_sandbox_server_stdio import ExecutionContext, monkey_patch_matplotlib, monkey_patch_pil
from ..core.execution_context import PersistentExecutionContext


class LocalSandbox(BaseSandbox):
    """
    Local sandbox implementation that uses the existing MCP server functionality.
    
    This provides secure local execution with artifact capture and virtual environment support.
    """

    def __init__(self, **kwargs):
        """
        Initialize a local sandbox instance.
        """
        # Force remote=False for local sandboxes
        kwargs["remote"] = False
        super().__init__(**kwargs)
        
        # Initialize local execution context with persistence
        self._execution_context = PersistentExecutionContext()
        self._execution_globals = self._execution_context.globals_dict
        
        # Apply monkey patches for artifact capture
        monkey_patch_matplotlib()
        monkey_patch_pil()

    async def get_default_image(self) -> str:
        """
        Get the default Docker image for local sandbox (not used in local execution).
        """
        return "local-python"

    async def start(
        self,
        image: Optional[str] = None,
        memory: int = 512,
        cpus: float = 1.0,
        timeout: float = 180.0,
    ) -> None:
        """
        Start the local sandbox.
        
        For local sandboxes, this primarily sets up the execution environment.
        """
        if self._is_started:
            return
            
        # Already set up in PersistentExecutionContext
        # No additional setup needed for persistent context
        
        self._is_started = True

    async def stop(self) -> None:
        """
        Stop the local sandbox and clean up resources.
        """
        if not self._is_started:
            return
            
        # Clean up artifacts if needed
        # Note: We might want to preserve artifacts for user access
        # self._execution_context.cleanup_artifacts()
        
        self._is_started = False

    async def run(self, code: str) -> Execution:
        """
        Execute Python code in the local sandbox.

        Args:
            code: Python code to execute

        Returns:
            An Execution object representing the executed code

        Raises:
            RuntimeError: If the sandbox is not started or execution fails
        """
        if not self._is_started:
            raise RuntimeError("Sandbox is not started. Call start() first.")

        # Use the enhanced persistent execution context
        import hashlib
        cache_key = hashlib.md5(code.encode()).hexdigest()
        
        result = self._execution_context.execute_code(code, cache_key=cache_key)
        
        # Create and return execution result
        return Execution(
            stdout=result['stdout'],
            stderr=result['stderr'],
            return_value=None,  # Will be enhanced in future versions
            exception=Exception(result['error']) if result['error'] else None,
            artifacts=result['artifacts'],
        )

    @property
    def artifacts_dir(self) -> Optional[str]:
        """
        Get the artifacts directory path.
        """
        return str(self._execution_context.artifacts_dir) if self._execution_context.artifacts_dir else None

    def list_artifacts(self) -> List[str]:
        """
        List all artifacts created during execution.
        """
        if not self._execution_context.artifacts_dir:
            return []
            
        artifacts_dir = Path(self._execution_context.artifacts_dir)
        if not artifacts_dir.exists():
            return []
            
        return [str(f) for f in artifacts_dir.rglob("*") if f.is_file()]

    def cleanup_artifacts(self) -> None:
        """
        Clean up all artifacts.
        """
        self._execution_context.cleanup_artifacts()

    def get_execution_info(self) -> Dict[str, Any]:
        """
        Get information about the execution environment.
        """
        return {
            "python_version": sys.version,
            "executable": sys.executable,
            "virtual_env": os.environ.get("VIRTUAL_ENV"),
            "project_root": str(self._execution_context.project_root),
            "artifacts_dir": self.artifacts_dir,
            "sys_path": sys.path[:10],  # First 10 entries
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics from the execution context.
        """
        return self._execution_context.get_execution_stats()
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get execution history.
        """
        return self._execution_context.get_execution_history(limit=limit)
    
    def clear_cache(self) -> None:
        """
        Clear compilation and execution cache.
        """
        self._execution_context.clear_cache()
    
    def save_session(self) -> None:
        """
        Manually save the current execution session state.
        """
        self._execution_context.save_persistent_state()
    
    @property
    def session_id(self) -> str:
        """
        Get the current session ID.
        """
        return self._execution_context.session_id
    
    def cleanup_session(self) -> None:
        """
        Cleanup the current session.
        """
        self._execution_context.cleanup()
