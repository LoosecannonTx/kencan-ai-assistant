"""
System control module for Kencan
Handles system-level operations like running commands, installing programs, etc.
"""

import os
import subprocess
import psutil
import winshell
from typing import Dict, Any, List
from pathlib import Path

class SystemController:
    """Controller for system operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize system controller"""
        self.config = config
        self.security = config.get('security', {})
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed based on security settings"""
        blocked = self.security.get('blocked_commands', [])
        
        # Check if command contains blocked patterns
        for blocked_cmd in blocked:
            if blocked_cmd.lower() in command.lower():
                return False
        
        return True
    
    def run_command(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """Run a shell command"""
        try:
            if not self._is_command_allowed(command):
                return {
                    'success': False,
                    'error': 'Command blocked by security settings'
                }
            
            if timeout is None:
                timeout = self.security.get('command_timeout', 300)
            
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def install_program(self, program: str) -> Dict[str, Any]:
        """Install a program using winget"""
        try:
            # Use Windows Package Manager (winget)
            command = f"winget install {program} --silent --accept-package-agreements --accept-source-agreements"
            result = self.run_command(command, timeout=600)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Successfully installed {program}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to install {program}: {result.get("stderr", "")}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def uninstall_program(self, program: str) -> Dict[str, Any]:
        """Uninstall a program using winget"""
        try:
            command = f"winget uninstall {program} --silent"
            result = self.run_command(command, timeout=300)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'Successfully uninstalled {program}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to uninstall {program}: {result.get("stderr", "")}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application"""
        try:
            # Try to start the application
            subprocess.Popen(app_name, shell=True)
            
            return {
                'success': True,
                'message': f'Opened {app_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_running_processes(self) -> Dict[str, Any]:
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'success': True,
                'processes': processes[:50]  # Limit to top 50
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def kill_process(self, process_name: str) -> Dict[str, Any]:
        """Kill a process by name"""
        try:
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    killed.append(proc.info['pid'])
            
            if killed:
                return {
                    'success': True,
                    'message': f'Killed {len(killed)} process(es)',
                    'pids': killed
                }
            else:
                return {
                    'success': False,
                    'error': f'Process {process_name} not found'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'success': True,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
