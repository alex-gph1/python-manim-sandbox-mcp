#!/usr/bin/env python3
"""
Interactive Sandbox Playground

This provides a direct interactive environment for testing the sandbox,
similar to the microsandbox experience where you can type commands directly
and see immediate results.

Usage:
    python playground.py

Commands:
    2+5                    # Execute Python expression
    print("hello world")  # Execute Python code
    !ls                    # Execute shell command
    .help                  # Show help
    .exit                  # Exit playground
    .clear                 # Clear screen
    .status                # Show sandbox status
    .cache                 # Show cache statistics
    .cache clear           # Clear cache
    .artifacts             # List artifacts
    .artifacts clear       # Clear artifacts
"""

import os
import sys
import code
import json
import traceback
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from sandbox.sdk.local_sandbox import LocalSandbox
    from sandbox.sdk.config import SandboxOptions
    from sandbox.core.execution_context import PersistentExecutionContext
except ImportError as e:
    print(f"Error importing sandbox modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class SandboxPlayground:
    """Interactive playground for sandbox testing."""
    
    def __init__(self):
        self.setup_sandbox()
        self.setup_commands()
        
    def setup_sandbox(self):
        """Initialize the sandbox environment."""
        print("🚀 Initializing Sandbox Playground...")
        
        # Create sandbox options
        options = SandboxOptions(
            timeout=30,
            memory_limit=None,
            enable_networking=True,
            working_directory=str(project_root),
            environment_variables={},
            allowed_imports=None,
            persistent_session=True
        )
        
        # Initialize sandbox
        self.sandbox = LocalSandbox(options)
        self.context = PersistentExecutionContext()
        
        print("✅ Sandbox initialized successfully!")
        print(f"📁 Working directory: {project_root}")
        print(f"🐍 Python executable: {sys.executable}")
        print(f"📦 Virtual environment: {os.environ.get('VIRTUAL_ENV', 'System Python')}")
        print()
        
    def setup_commands(self):
        """Setup command handlers."""
        self.commands = {
            '.help': self.show_help,
            '.exit': self.exit_playground,
            '.quit': self.exit_playground,
            '.clear': self.clear_screen,
            '.status': self.show_status,
            '.cache': self.show_cache,
            '.artifacts': self.show_artifacts,
            '.vars': self.show_variables,
            '.history': self.show_history,
            '.reset': self.reset_sandbox
        }
        
    def show_help(self, args=None):
        """Show help information."""
        help_text = """
🎮 Sandbox Playground Commands:

Python Execution:
  2+5                    Execute Python expression
  print("hello world")  Execute Python code
  x = 10; y = 20        Define variables
  import math           Import modules

Shell Commands:
  !ls                   Execute shell command
  !pwd                  Show current directory
  !pip list             List installed packages

Playground Commands:
  .help                 Show this help
  .exit, .quit          Exit playground
  .clear                Clear screen
  .status               Show sandbox status
  .cache                Show cache statistics
  .cache clear          Clear compilation cache
  .artifacts            List current artifacts
  .artifacts clear      Clear all artifacts
  .vars                 Show current variables
  .history              Show execution history
  .reset                Reset sandbox state

Tips:
  - Variables persist between commands
  - Use tab completion for file paths
  - Ctrl+C to interrupt execution
  - Ctrl+D to exit
"""
        print(help_text)
        
    def exit_playground(self, args=None):
        """Exit the playground."""
        print("\n👋 Goodbye! Thanks for using Sandbox Playground!")
        sys.exit(0)
        
    def clear_screen(self, args=None):
        """Clear the screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def show_status(self, args=None):
        """Show sandbox status."""
        stats = self.context.get_execution_stats()
        print(f"""
📊 Sandbox Status:
  Session ID: {stats['session_id']}
  Total executions: {stats['total_executions']}
  Average execution time: {stats['average_execution_time']:.3f}s
  Cache hit ratio: {stats['cache_hit_ratio']:.2%}
  Cached compilations: {stats['cached_compilations']}
  Artifacts: {stats['artifacts_count']}
  
🔧 Environment:
  Project root: {self.context.project_root}
  Virtual env: {self.context.venv_path}
  Python: {sys.executable}
        """)
        
    def show_cache(self, args=None):
        """Show cache statistics and manage cache."""
        if args and args[0] == 'clear':
            self.context.clear_cache()
            print("🧹 Cache cleared successfully!")
            return
            
        stats = self.context.get_execution_stats()
        print(f"""
💾 Cache Statistics:
  Cache hits: {stats['cache_hits']}
  Cache misses: {stats['cache_misses']}
  Hit ratio: {stats['cache_hit_ratio']:.2%}
  Cached compilations: {stats['cached_compilations']}
  
Use '.cache clear' to clear the cache.
        """)
        
    def show_artifacts(self, args=None):
        """Show or manage artifacts."""
        if args and args[0] == 'clear':
            self.context.cleanup()
            print("🧹 Artifacts cleared successfully!")
            return
            
        artifacts = self.context._get_current_artifacts()
        if not artifacts:
            print("📁 No artifacts found.")
            return
            
        print(f"📁 Current artifacts ({len(artifacts)} files):")
        for artifact in sorted(artifacts):
            print(f"  - {artifact}")
            
    def show_variables(self, args=None):
        """Show current variables."""
        vars_dict = {k: v for k, v in self.context.globals_dict.items() 
                    if not k.startswith('_')}
        
        if not vars_dict:
            print("📝 No variables defined.")
            return
            
        print(f"📝 Current variables ({len(vars_dict)}):")
        for name, value in vars_dict.items():
            try:
                value_str = repr(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f"  {name} = {value_str}")
            except:
                print(f"  {name} = <unprintable>")
                
    def show_history(self, args=None):
        """Show execution history."""
        limit = 10
        if args and args[0].isdigit():
            limit = int(args[0])
            
        history = self.context.get_execution_history(limit)
        if not history:
            print("📜 No execution history found.")
            return
            
        print(f"📜 Execution history (last {len(history)} entries):")
        for i, entry in enumerate(history, 1):
            code_preview = entry['code'].replace('\n', '\\n')
            if len(code_preview) > 40:
                code_preview = code_preview[:37] + "..."
            status = "✅" if entry['result']['success'] else "❌"
            print(f"  {i}. {status} {code_preview} ({entry['execution_time']:.3f}s)")
            
    def reset_sandbox(self, args=None):
        """Reset sandbox state."""
        self.context.globals_dict.clear()
        self.context.clear_cache()
        print("🔄 Sandbox state reset successfully!")
        
    def execute_python(self, code):
        """Execute Python code."""
        try:
            # Try to compile to check if it's an expression or statement
            try:
                compile(code, '<input>', 'eval')
                is_expression = True
            except SyntaxError:
                is_expression = False
                
            # Execute the code
            result = self.context.execute_code(code)
            
            # Show results
            if result['success']:
                if result['stdout']:
                    print(result['stdout'], end='')
                    
                # For expressions, show the result
                if is_expression and not result['stdout']:
                    try:
                        expr_result = eval(code, self.context.globals_dict)
                        if expr_result is not None:
                            print(repr(expr_result))
                    except:
                        pass
                        
                # Show any new artifacts
                if result['artifacts']:
                    print(f"📁 Generated {len(result['artifacts'])} artifact(s)")
                    
            else:
                print(f"❌ Error: {result['error']}")
                if result['stderr']:
                    print(result['stderr'], end='')
                    
        except Exception as e:
            print(f"❌ Execution error: {e}")
            traceback.print_exc()
            
    def execute_shell(self, command):
        """Execute shell command."""
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='')
                
            if result.returncode != 0:
                print(f"❌ Command failed with return code {result.returncode}")
                
        except subprocess.TimeoutExpired:
            print("❌ Command timed out")
        except Exception as e:
            print(f"❌ Shell execution error: {e}")
            
    def process_input(self, user_input):
        """Process user input."""
        user_input = user_input.strip()
        
        if not user_input:
            return
            
        # Handle playground commands
        if user_input.startswith('.'):
            parts = user_input.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else None
            
            if command in self.commands:
                self.commands[command](args)
            else:
                print(f"❌ Unknown command: {command}")
                print("Type '.help' for available commands")
            return
            
        # Handle shell commands
        if user_input.startswith('!'):
            self.execute_shell(user_input[1:])
            return
            
        # Handle Python code
        self.execute_python(user_input)
        
    def run(self):
        """Run the interactive playground."""
        print("🎮 Welcome to Sandbox Playground!")
        print("Type '.help' for commands or just start typing Python code.")
        print("Examples: 2+5, print('hello'), !ls, .status")
        print("=" * 50)
        
        try:
            while True:
                try:
                    user_input = input("sandbox>>> ")
                    self.process_input(user_input)
                except KeyboardInterrupt:
                    print("\n(Use .exit to quit)")
                    continue
                except EOFError:
                    print("\n👋 Goodbye!")
                    break
                    
        except Exception as e:
            print(f"❌ Playground error: {e}")
            traceback.print_exc()
        finally:
            # Clean up
            self.context.cleanup()


def main():
    """Main entry point."""
    playground = SandboxPlayground()
    playground.run()


if __name__ == "__main__":
    main()
