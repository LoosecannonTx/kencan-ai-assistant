"""
File operations module for Kencan
Handles file and directory operations
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List

class FileOperations:
    """Controller for file operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize file operations"""
        self.config = config
    
    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            
            return {
                'success': True,
                'message': f'Created file: {path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file"""
        try:
            file_path = Path(path)
            content = file_path.read_text(encoding='utf-8')
            
            return {
                'success': True,
                'content': content,
                'size': file_path.stat().st_size
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            file_path = Path(path)
            if file_path.is_file():
                file_path.unlink()
                return {
                    'success': True,
                    'message': f'Deleted file: {path}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Not a file or does not exist'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return {
                'success': True,
                'message': f'Created directory: {path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents"""
        try:
            dir_path = Path(path)
            if not dir_path.is_dir():
                return {
                    'success': False,
                    'error': 'Not a directory'
                }
            
            items = []
            for item in dir_path.iterdir():
                items.append({
                    'name': item.name,
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })
            
            return {
                'success': True,
                'items': items
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file"""
        try:
            shutil.copy2(source, destination)
            return {
                'success': True,
                'message': f'Copied {source} to {destination}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file"""
        try:
            shutil.move(source, destination)
            return {
                'success': True,
                'message': f'Moved {source} to {destination}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
