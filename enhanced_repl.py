#!/usr/bin/env python3
"""
Enhanced Interactive REPL with Jupyter-style capabilities
Provides rich interactive Python experience with tab completion, history, and more
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil

try:
    import IPython
    from IPython.terminal.interactiveshell import TerminalInteractiveShell
    from IPython.terminal.ipapp import TerminalIPythonApp
    from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
    from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
    from traitlets.config import Config
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

import readline
import rlcompleter
import code
import ast
import traceback

class EnhancedREPL:
    """Enhanced REPL with advanced features"""
    
    def __init__(self, base_dir: str = "/home/stan/Prod/sandbox"):
        self.base_dir = Path(base_dir)
        self.history_file = self.base_dir / ".repl_history"
        self.config_file = self.base_dir / ".repl_config.json"
        self.artifacts_dir = self.base_dir / "artifacts"
        self.session_vars = {}
        self.magic_commands = {}
        self.load_config()
        self.setup_history()
        
    def load_config(self):
        """Load REPL configuration"""
        default_config = {
            "auto_indent": True,
            "syntax_highlighting": True,
            "tab_completion": True,
            "history_size": 1000,
            "save_session": True,
            "display_execution_time": True,
            "auto_import": [
                "numpy as np",
                "matplotlib.pyplot as plt",
                "pandas as pd",
                "os",
                "sys",
                "json",
                "datetime",
                "pathlib.Path"
            ]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save REPL configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_history(self):
        """Setup readline history"""
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        readline.set_history_length(self.config["history_size"])
        
        # Enable tab completion
        if self.config["tab_completion"]:
            readline.set_completer(rlcompleter.Completer().complete)
            readline.parse_and_bind("tab: complete")
    
    def save_history(self):
        """Save readline history"""
        readline.write_history_file(self.history_file)
    
    def start_ipython_repl(self):
        """Start enhanced IPython REPL"""
        if not IPYTHON_AVAILABLE:
            print("IPython not available, falling back to basic REPL")
            return self.start_basic_repl()
        
        # Create IPython configuration
        config = Config()
        config.TerminalInteractiveShell.confirm_exit = False
        config.TerminalInteractiveShell.history_length = self.config["history_size"]
        config.TerminalInteractiveShell.colors = 'Linux'
        config.TerminalInteractiveShell.autoindent = self.config["auto_indent"]
        
        # Create custom magic commands
        @magics_class
        class SandboxMagics(Magics):
            @line_magic
            def artifacts(self, line):
                """List artifacts in the sandbox"""
                from enhanced_artifact_manager import EnhancedArtifactManager
                manager = EnhancedArtifactManager()
                result = manager.list_artifacts()
                print(f"Found {result['total_artifacts']} artifacts")
                for category, files in result['categories'].items():
                    print(f"  {category}: {len(files)} files")
                return result
            
            @line_magic
            def save_session(self, line):
                """Save current session variables"""
                session_file = self.base_dir / f"session_{int(time.time())}.json"
                session_data = {
                    "variables": {k: str(v) for k, v in self.shell.user_ns.items() 
                                if not k.startswith('_') and not callable(v)},
                    "history": [str(h) for h in self.shell.history_manager.get_range()]
                }
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                print(f"Session saved to {session_file}")
            
            @cell_magic
            def manim(self, line, cell):
                """Execute Manim animation code"""
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(cell)
                    temp_file = f.name
                
                try:
                    result = subprocess.run([
                        'python', temp_file, '-pql'
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("Manim animation created successfully")
                        # Find and display the output file
                        media_dir = Path.cwd() / "media"
                        if media_dir.exists():
                            for video_file in media_dir.rglob("*.mp4"):
                                print(f"Output: {video_file}")
                    else:
                        print(f"Error: {result.stderr}")
                        
                finally:
                    os.unlink(temp_file)
        
        # Start IPython with custom configuration
        app = TerminalIPythonApp.instance()
        app.initialize([])
        app.shell.register_magic_function(SandboxMagics(app.shell).artifacts, 'line', 'artifacts')
        app.shell.register_magic_function(SandboxMagics(app.shell).save_session, 'line', 'save_session')
        app.shell.register_magic_function(SandboxMagics(app.shell).manim, 'cell', 'manim')
        
        # Auto-import common modules
        for import_stmt in self.config["auto_import"]:
            try:
                app.shell.run_line_magic('load_ext', 'autoreload')
                app.shell.run_line_magic('autoreload', '2')
                app.shell.ex(f"import {import_stmt}")
            except Exception as e:
                print(f"Warning: Could not import {import_stmt}: {e}")
        
        print("Enhanced IPython REPL started!")
        print("Available magic commands:")
        print("  %artifacts - List sandbox artifacts")
        print("  %save_session - Save current session")
        print("  %%manim - Execute Manim animation code")
        print("  Type 'exit' or Ctrl+D to quit")
        
        try:
            app.start()
        except KeyboardInterrupt:
            print("\nREPL interrupted by user")
        finally:
            self.save_history()
    
    def start_basic_repl(self):
        """Start basic enhanced REPL"""
        print("Enhanced Python REPL")
        print("Type 'help()' for help, 'exit()' to quit")
        print("Available commands: artifacts(), save_session(), config()")
        
        # Create custom namespace
        namespace = {
            '__name__': '__console__',
            '__doc__': None,
            'artifacts': self.cmd_artifacts,
            'save_session': self.cmd_save_session,
            'config': self.cmd_config,
            'help': self.cmd_help,
        }
        
        # Auto-import modules
        for import_stmt in self.config["auto_import"]:
            try:
                exec(f"import {import_stmt}", namespace)
            except Exception as e:
                print(f"Warning: Could not import {import_stmt}: {e}")
        
        # Start interactive console
        console = code.InteractiveConsole(namespace)
        try:
            console.interact()
        except KeyboardInterrupt:
            print("\nREPL interrupted by user")
        finally:
            self.save_history()
    
    def cmd_artifacts(self):
        """Command to list artifacts"""
        try:
            from enhanced_artifact_manager import EnhancedArtifactManager
            manager = EnhancedArtifactManager()
            result = manager.list_artifacts()
            print(f"Found {result['total_artifacts']} artifacts")
            for category, files in result['categories'].items():
                print(f"  {category}: {len(files)} files")
            return result
        except Exception as e:
            print(f"Error listing artifacts: {e}")
            return None
    
    def cmd_save_session(self):
        """Command to save current session"""
        try:
            import inspect
            frame = inspect.currentframe().f_back
            session_vars = {k: str(v) for k, v in frame.f_globals.items() 
                          if not k.startswith('_') and not callable(v)}
            
            session_file = self.base_dir / f"session_{int(time.time())}.json"
            with open(session_file, 'w') as f:
                json.dump(session_vars, f, indent=2)
            print(f"Session saved to {session_file}")
            return session_file
        except Exception as e:
            print(f"Error saving session: {e}")
            return None
    
    def cmd_config(self, key=None, value=None):
        """Command to view/modify configuration"""
        if key is None:
            print("Current configuration:")
            for k, v in self.config.items():
                print(f"  {k}: {v}")
            return self.config
        elif value is None:
            return self.config.get(key, "Key not found")
        else:
            self.config[key] = value
            self.save_config()
            print(f"Configuration updated: {key} = {value}")
            return value
    
    def cmd_help(self):
        """Command to show help"""
        help_text = """
Enhanced REPL Commands:
  artifacts() - List all artifacts in the sandbox
  save_session() - Save current session variables
  config() - View current configuration
  config(key) - Get specific configuration value
  config(key, value) - Set configuration value
  
Magic Commands (IPython mode):
  %artifacts - List artifacts
  %save_session - Save session
  %%manim - Execute Manim code in cell
  
Auto-imported modules:
  numpy as np, matplotlib.pyplot as plt, pandas as pd
  os, sys, json, datetime, pathlib.Path
        """
        print(help_text)

def main():
    """Main function to start the enhanced REPL"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Interactive Python REPL")
    parser.add_argument("--basic", action="store_true", help="Use basic REPL instead of IPython")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    repl = EnhancedREPL()
    
    if args.basic or not IPYTHON_AVAILABLE:
        repl.start_basic_repl()
    else:
        repl.start_ipython_repl()

if __name__ == "__main__":
    main()
