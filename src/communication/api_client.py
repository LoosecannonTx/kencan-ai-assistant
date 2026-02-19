"""
API Client for communicating with cloud AI
Includes retry logic, graceful degradation, and improved error handling
"""

import requests
import time
import logging
from typing import Dict, Any, List, Optional, Callable
import json

logger = logging.getLogger(__name__)


class CloudAPIClient:
    """Client for communicating with the cloud-hosted AI"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize API client"""
        self.config = config
        self.cloud_config = config.get('cloud', {})
        self.security_config = config.get('security', {})
        self.endpoint = self.cloud_config.get('endpoint', '')
        self.api_key = self.cloud_config.get('api_key', '')
        self.session = requests.Session()
        
        # Retry configuration
        self.max_retries = self.security_config.get('max_retries', 3)
        self.retry_delay = self.cloud_config.get('reconnect_interval', 5)
        
        # Connection state
        self._is_connected = False
        self._last_error = None
        self._consecutive_failures = 0
        
        # Set headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def _retry_request(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a request with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                self._consecutive_failures = 0
                self._is_connected = True
                return result
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self._consecutive_failures += 1
                logger.warning(f"Connection failed (attempt {attempt + 1}/{self.max_retries}): {e}")
            except requests.exceptions.Timeout as e:
                last_exception = e
                self._consecutive_failures += 1
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries}): {e}")
            except requests.exceptions.RequestException as e:
                last_exception = e
                self._consecutive_failures += 1
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        self._is_connected = False
        self._last_error = str(last_exception)
        raise last_exception
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to cloud"""
        return self._is_connected
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    def test_connection(self) -> bool:
        """Test connection to cloud AI"""
        try:
            if not self.endpoint:
                self._last_error = "No endpoint configured"
                return False
            
            response = self.session.get(
                f"{self.endpoint}/health",
                timeout=10
            )
            self._is_connected = response.status_code == 200
            if not self._is_connected:
                self._last_error = f"Health check failed with status {response.status_code}"
            return self._is_connected
        except Exception as e:
            self._is_connected = False
            self._last_error = str(e)
            return False
    
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the cloud AI with retry logic"""
        try:
            def _send():
                response = self.session.post(
                    f"{self.endpoint}/command",
                    json=command,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            
            return self._retry_request(_send)
        except Exception as e:
            logger.error(f"Failed to send command after {self.max_retries} retries: {e}")
            return {
                'success': False,
                'error': str(e),
                'retries_exhausted': True
            }
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """Poll for commands from cloud AI with graceful degradation"""
        try:
            def _get():
                response = self.session.get(
                    f"{self.endpoint}/commands/pending",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('commands', [])
                elif response.status_code == 404:
                    # Endpoint doesn't exist - graceful degradation
                    logger.debug("commands/pending endpoint not available")
                    return []
                else:
                    response.raise_for_status()
                return []
            
            return self._retry_request(_get)
        except Exception as e:
            # Graceful degradation - return empty list instead of crashing
            if self._consecutive_failures >= self.max_retries:
                logger.warning(f"Cloud connection lost after {self._consecutive_failures} failures")
            return []
    
    def send_result(self, command_id: str, result: Dict[str, Any]) -> bool:
        """Send command execution result back to cloud with retry"""
        try:
            def _send():
                response = self.session.post(
                    f"{self.endpoint}/commands/{command_id}/result",
                    json=result,
                    timeout=10
                )
                return response.status_code == 200
            
            return self._retry_request(_send)
        except Exception as e:
            logger.error(f"Failed to send result for command {command_id}: {e}")
            return False
    
    def send_user_input(self, user_input: str) -> Dict[str, Any]:
        """Send user input to cloud AI and get response with retry"""
        try:
            def _send():
                response = self.session.post(
                    f"{self.endpoint}/command",
                    json={'input': user_input},
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
            
            return self._retry_request(_send)
        except Exception as e:
            logger.error(f"Failed to send user input: {e}")
            return {
                'success': False,
                'error': str(e),
                'retries_exhausted': True
            }
    
    def clear_conversation(self) -> bool:
        """Clear conversation history on cloud"""
        try:
            response = self.session.post(
                f"{self.endpoint}/conversation/clear",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to clear conversation: {e}")
            return False
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history from cloud"""
        try:
            response = self.session.get(
                f"{self.endpoint}/conversation/history",
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('history', [])
            return []
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
