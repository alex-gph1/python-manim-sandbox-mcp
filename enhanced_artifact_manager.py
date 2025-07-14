#!/usr/bin/env python3
"""
Enhanced Artifact Management System
Provides comprehensive artifact tracking, cleanup, and management capabilities
"""

import os
import json
import shutil
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess

@dataclass
class ArtifactInfo:
    """Structured information about an artifact"""
    path: str
    name: str
    size: int
    created: str
    modified: str
    type: str
    mime_type: str
    hash: str
    category: str
    parent_dir: str

class EnhancedArtifactManager:
    """Enhanced artifact management with comprehensive tracking"""
    
    def __init__(self, base_dir: str = "/home/stan/Prod/sandbox"):
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / "artifacts"
        self.cache_file = self.base_dir / ".artifact_cache.json"
        self.common_output_dirs = [
            "media/videos",  # Manim output
            "media/images",  # Manim images
            "output",        # General output
            "exports",       # Export directory
            "generated",     # Generated files
            "temp",          # Temporary files
            "cache",         # Cache files
        ]
        
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate SHA256 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except:
            return "unknown"
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on extension and location"""
        suffix = file_path.suffix.lower()
        path_str = str(file_path).lower()
        
        # Video files
        if suffix in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return "video"
        # Image files
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
            return "image"
        # Web files
        elif suffix in ['.html', '.css', '.js', '.json']:
            return "web"
        # Documents
        elif suffix in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            return "document"
        # Code files
        elif suffix in ['.py', '.js', '.cpp', '.java', '.c', '.h']:
            return "code"
        # Data files
        elif suffix in ['.csv', '.xlsx', '.json', '.xml']:
            return "data"
        # Manim specific
        elif "manim" in path_str or "media" in path_str:
            return "manim"
        # Temporary files
        elif "temp" in path_str or "cache" in path_str:
            return "temporary"
        else:
            return "other"
    
    def scan_artifacts(self, include_hidden: bool = False) -> List[ArtifactInfo]:
        """Comprehensive artifact scanning with detailed information"""
        artifacts = []
        
        # Scan common directories
        scan_dirs = [
            self.base_dir,
            self.artifacts_dir,
        ]
        
        # Add common output directories
        for output_dir in self.common_output_dirs:
            scan_dirs.append(self.base_dir / output_dir)
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
                
            for root, dirs, files in os.walk(scan_dir):
                # Skip hidden directories unless requested
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    # Skip hidden files unless requested
                    if not include_hidden and file.startswith('.'):
                        continue
                    
                    file_path = Path(root) / file
                    try:
                        stat = file_path.stat()
                        mime_type, _ = mimetypes.guess_type(str(file_path))
                        
                        artifact = ArtifactInfo(
                            path=str(file_path),
                            name=file,
                            size=stat.st_size,
                            created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            type=file_path.suffix.lower(),
                            mime_type=mime_type or "unknown",
                            hash=self._get_file_hash(file_path),
                            category=self._categorize_file(file_path),
                            parent_dir=str(file_path.parent)
                        )
                        artifacts.append(artifact)
                    except (OSError, PermissionError):
                        continue
        
        return artifacts
    
    def list_artifacts(self, category: Optional[str] = None, 
                      sort_by: str = "modified", 
                      reverse: bool = True) -> Dict:
        """List artifacts with filtering and sorting"""
        artifacts = self.scan_artifacts()
        
        if category:
            artifacts = [a for a in artifacts if a.category == category]
        
        # Sort artifacts
        if sort_by in ["created", "modified"]:
            artifacts.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)
        elif sort_by == "size":
            artifacts.sort(key=lambda x: x.size, reverse=reverse)
        elif sort_by == "name":
            artifacts.sort(key=lambda x: x.name.lower(), reverse=reverse)
        
        # Group by category
        categories = {}
        for artifact in artifacts:
            if artifact.category not in categories:
                categories[artifact.category] = []
            categories[artifact.category].append(asdict(artifact))
        
        return {
            "total_artifacts": len(artifacts),
            "categories": categories,
            "summary": {
                "total_size": sum(a.size for a in artifacts),
                "categories_count": len(categories),
                "last_scan": datetime.now().isoformat()
            }
        }
    
    def cleanup_artifacts(self, category: Optional[str] = None,
                         older_than_days: Optional[int] = None,
                         dry_run: bool = False) -> Dict:
        """Enhanced cleanup with detailed feedback"""
        artifacts = self.scan_artifacts()
        to_delete = []
        
        for artifact in artifacts:
            should_delete = True
            
            # Filter by category
            if category and artifact.category != category:
                should_delete = False
            
            # Filter by age
            if older_than_days:
                modified_time = datetime.fromisoformat(artifact.modified)
                age_days = (datetime.now() - modified_time).days
                if age_days < older_than_days:
                    should_delete = False
            
            if should_delete:
                to_delete.append(artifact)
        
        results = {
            "dry_run": dry_run,
            "total_found": len(artifacts),
            "to_delete": len(to_delete),
            "files_by_category": {},
            "total_size_to_free": 0,
            "errors": []
        }
        
        # Group by category for reporting
        for artifact in to_delete:
            if artifact.category not in results["files_by_category"]:
                results["files_by_category"][artifact.category] = []
            results["files_by_category"][artifact.category].append(artifact.name)
            results["total_size_to_free"] += artifact.size
        
        # Actually delete files if not dry run
        if not dry_run:
            deleted_count = 0
            for artifact in to_delete:
                try:
                    file_path = Path(artifact.path)
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    results["errors"].append(f"Failed to delete {artifact.path}: {str(e)}")
            
            results["successfully_deleted"] = deleted_count
        
        return results
    
    def create_artifact_report(self) -> str:
        """Generate comprehensive artifact report"""
        artifacts_info = self.list_artifacts()
        
        report = []
        report.append("=" * 60)
        report.append("ARTIFACT MANAGEMENT REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Artifacts: {artifacts_info['total_artifacts']}")
        report.append(f"Total Size: {artifacts_info['summary']['total_size'] / 1024 / 1024:.2f} MB")
        report.append("")
        
        report.append("CATEGORIES:")
        report.append("-" * 40)
        for category, files in artifacts_info["categories"].items():
            total_size = sum(f["size"] for f in files)
            report.append(f"{category.upper()}: {len(files)} files ({total_size / 1024 / 1024:.2f} MB)")
            
            # Show recent files
            recent_files = sorted(files, key=lambda x: x["modified"], reverse=True)[:3]
            for file in recent_files:
                report.append(f"  - {file['name']} ({file['size']} bytes)")
            if len(files) > 3:
                report.append(f"  ... and {len(files) - 3} more files")
            report.append("")
        
        return "\n".join(report)

# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Artifact Management")
    parser.add_argument("--list", action="store_true", help="List all artifacts")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup artifacts")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--older-than", type=int, help="Delete files older than N days")
    
    args = parser.parse_args()
    
    manager = EnhancedArtifactManager()
    
    if args.list:
        result = manager.list_artifacts(category=args.category)
        print(json.dumps(result, indent=2))
    elif args.cleanup:
        result = manager.cleanup_artifacts(
            category=args.category,
            older_than_days=args.older_than,
            dry_run=args.dry_run
        )
        print(json.dumps(result, indent=2))
    elif args.report:
        print(manager.create_artifact_report())
    else:
        print("Use --help for usage information")
