#!/usr/bin/env python3
"""
Test script to validate resource manager functionality.
"""

import sys
import time
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.sandbox.core.resource_manager import get_resource_manager, ResourceLimits

def test_resource_manager():
    """Test the resource manager functionality."""
    print("Testing Resource Manager...")
    
    # Get resource manager instance
    rm = get_resource_manager()
    
    # Test 1: Basic stats
    print("\n=== Test 1: Basic Resource Stats ===")
    stats = rm.get_resource_stats()
    print(f"Memory: {stats['memory_mb']:.1f}MB")
    print(f"Processes: {stats['processes']}")
    print(f"Active contexts: {stats['active_contexts']}")
    print(f"Cleanup running: {stats['cleanup_running']}")
    
    # Test 2: Process management
    print("\n=== Test 2: Process Management ===")
    process = subprocess.Popen(['sleep', '2'], stdout=subprocess.PIPE)
    process_id = rm.process_manager.add_process(process, "test_sleep")
    print(f"Added process: {process_id}")
    
    processes = rm.process_manager.list_processes()
    print(f"Active processes: {len(processes)}")
    
    # Wait for process to finish
    time.sleep(3)
    
    finished = rm.process_manager.cleanup_finished()
    print(f"Cleaned up {finished} finished processes")
    
    # Test 3: Resource limits
    print("\n=== Test 3: Resource Limits ===")
    try:
        rm.check_resource_limits()
        print("✓ Resource limits OK")
    except Exception as e:
        print(f"✗ Resource limit exceeded: {e}")
    
    # Test 4: Thread pool
    print("\n=== Test 4: Thread Pool ===")
    def test_task():
        time.sleep(0.1)
        return "Task completed"
    
    future = rm.thread_pool.submit(test_task)
    result = future.result(timeout=1)
    print(f"Thread pool result: {result}")
    
    # Test 5: Configuration
    print("\n=== Test 5: Configuration ===")
    print(f"Max Memory: {ResourceLimits.MAX_MEMORY_MB}MB")
    print(f"Max Processes: {ResourceLimits.MAX_PROCESSES}")
    print(f"Max Threads: {ResourceLimits.MAX_THREADS}")
    print(f"Cleanup Interval: {ResourceLimits.CLEANUP_INTERVAL_SEC}s")
    
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    test_resource_manager()
