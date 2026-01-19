"""
API Client for communicating with cloud AI
"""

import requests
import time
from typing import Dict, Any, List, Optional
import json

class CloudAPIClient:
    """Client for communicating with the cloud-hosted AI"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize API client"""
        self.config = config
        self.cloud_config = config.get('cloud', {})
        self.endpoint = self.cloud_config.get('endpoint', '')
        self.api_key = self.cloud_config.get('api_key', '')
        self.session = requests.Session()
        
        # Set headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def test_connection(self) -> bool:
        """Test connection to cloud AI"""
        try:
            if not self.endpoint:
                return False
            
            response = self.session.get(
                f"{self.endpoint}/health",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the cloud AI"""
        try:
            response = self.session.post(
                f"{self.endpoint}/command",
                json=command,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """Poll for commands from cloud AI"""
        try:
            response = self.session.get(
                f"{self.endpoint}/commands/pending",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('commands', [])
            return []
        except Exception:
            return []
    
    def send_result(self, command_id: str, result: Dict[str, Any]) -> bool:
        """Send command execution result back to cloud"""
        try:
            response = self.session.post(
                f"{self.endpoint}/commands/{command_id}/result",
                json=result,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def send_user_input(self, user_input: str) -> Dict[str, Any]:
        """Send user input to cloud AI and get response"""
        try:
            response = self.session.post(
                f"{self.endpoint}/command",
                json={'input': user_input},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
