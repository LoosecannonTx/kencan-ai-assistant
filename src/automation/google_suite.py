"""
Google Suite automation for Kencan
Uses gogcli (https://github.com/steipete/gogcli) for Gmail, Calendar, Drive, Contacts
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleSuiteController:
    """Controller for Google Suite operations via gogcli"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Google Suite controller"""
        self.config = config
        self.google_config = config.get('google', {})
        self.account = self.google_config.get('account', '')
        
    def _run_gog(self, args: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Run a gog command and return result"""
        try:
            cmd = ['gog', '--json'] + args
            if self.account:
                cmd = ['gog', '--account', self.account, '--json'] + args[1:]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout) if result.stdout.strip() else {}
                    return {'success': True, 'data': data}
                except json.JSONDecodeError:
                    return {'success': True, 'data': result.stdout}
            else:
                return {
                    'success': False,
                    'error': result.stderr or f'Command failed with code {result.returncode}'
                }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except FileNotFoundError:
            return {'success': False, 'error': 'gogcli not installed. Run: winget install steipete.gogcli'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== GMAIL ====================
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[str] = None, bcc: Optional[str] = None) -> Dict[str, Any]:
        """Send an email via Gmail"""
        try:
            args = ['gmail', 'send', '--to', to, '--subject', subject, '--body', body]
            if cc:
                args.extend(['--cc', cc])
            if bcc:
                args.extend(['--bcc', bcc])
            
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Email sent to {to}'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_emails(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search emails in Gmail"""
        try:
            args = ['gmail', 'search', query, '--max', str(max_results)]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def read_email(self, message_id: str) -> Dict[str, Any]:
        """Read a specific email"""
        try:
            args = ['gmail', 'messages', 'get', message_id]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_labels(self) -> Dict[str, Any]:
        """List Gmail labels"""
        try:
            args = ['gmail', 'labels', 'list']
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== CALENDAR ====================
    
    def list_events(self, days: int = 7) -> Dict[str, Any]:
        """List upcoming calendar events"""
        try:
            args = ['cal', 'list', '--days', str(days)]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_event(self, title: str, start: str, end: str, 
                     description: Optional[str] = None,
                     location: Optional[str] = None) -> Dict[str, Any]:
        """Create a calendar event"""
        try:
            args = ['cal', 'create', '--title', title, '--start', start, '--end', end]
            if description:
                args.extend(['--description', description])
            if location:
                args.extend(['--location', location])
            
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Event "{title}" created'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        try:
            args = ['cal', 'delete', event_id]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== DRIVE ====================
    
    def list_files(self, query: Optional[str] = None, max_results: int = 20) -> Dict[str, Any]:
        """List files in Google Drive"""
        try:
            args = ['drive', 'list', '--max', str(max_results)]
            if query:
                args.extend(['--query', query])
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def upload_file(self, local_path: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload a file to Google Drive"""
        try:
            if not Path(local_path).exists():
                return {'success': False, 'error': f'File not found: {local_path}'}
            
            args = ['drive', 'upload', local_path]
            if folder_id:
                args.extend(['--parent', folder_id])
            
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Uploaded {local_path} to Drive'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_file(self, file_id: str, local_path: str) -> Dict[str, Any]:
        """Download a file from Google Drive"""
        try:
            args = ['drive', 'download', file_id, '--output', local_path]
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Downloaded to {local_path}'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_drive(self, query: str) -> Dict[str, Any]:
        """Search files in Google Drive"""
        try:
            args = ['drive', 'search', query]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== CONTACTS ====================
    
    def search_contacts(self, query: str) -> Dict[str, Any]:
        """Search Google Contacts"""
        try:
            args = ['contacts', 'search', query]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_contact(self, name: str, email: Optional[str] = None, 
                       phone: Optional[str] = None) -> Dict[str, Any]:
        """Create a new contact"""
        try:
            args = ['contacts', 'create', '--name', name]
            if email:
                args.extend(['--email', email])
            if phone:
                args.extend(['--phone', phone])
            
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Contact "{name}" created'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== TASKS ====================
    
    def list_tasks(self, tasklist: str = '@default') -> Dict[str, Any]:
        """List tasks"""
        try:
            args = ['tasks', 'list', '--tasklist', tasklist]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_task(self, title: str, notes: Optional[str] = None,
                 due: Optional[str] = None) -> Dict[str, Any]:
        """Add a new task"""
        try:
            args = ['tasks', 'add', title]
            if notes:
                args.extend(['--notes', notes])
            if due:
                args.extend(['--due', due])
            
            result = self._run_gog(args)
            if result['success']:
                return {'success': True, 'message': f'Task "{title}" added'}
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark a task as complete"""
        try:
            args = ['tasks', 'done', task_id]
            return self._run_gog(args)
        except Exception as e:
            return {'success': False, 'error': str(e)}
