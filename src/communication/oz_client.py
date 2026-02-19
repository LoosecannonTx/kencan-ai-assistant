"""
Oz Cloud Agent Client for Kencan
Uses Warp's Oz API to run Claude-powered cloud agents instead of Colab/phi-2
"""

import requests
import time
import logging
import json
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Kencan system prompt for Claude
KENCAN_SYSTEM_PROMPT = """You are Kencan, an AI assistant that controls a Windows PC remotely.

Your role is to interpret user requests and generate commands that will be executed by a local agent on the user's Windows PC.

## Available Actions

You can control the PC using these actions:

### Browser Control
- `open_browser`: Open browser with optional URL
  - parameters: {"url": "https://example.com"} (optional)
- `new_tab`: Open new browser tab
  - parameters: {"url": "https://example.com"} (optional)
- `close_tab`: Close a browser tab
  - parameters: {"index": 0} (optional, closes current if not specified)
- `search_web`: Search the web
  - parameters: {"query": "search terms"}
- `click_element`: Click an element on page
  - parameters: {"selector": "CSS selector or XPath"}
- `type_text`: Type text into an element
  - parameters: {"selector": "CSS selector", "text": "text to type"}

### System Control
- `run_command`: Run a shell command
  - parameters: {"command": "powershell command"}
- `open_application`: Open an application
  - parameters: {"app_name": "notepad" or path}
- `install_program`: Install via winget
  - parameters: {"program": "program name"}
- `uninstall_program`: Uninstall via winget
  - parameters: {"program": "program name"}

### File Operations
- `create_file`: Create a new file
  - parameters: {"path": "C:\\path\\to\\file.txt", "content": "file content"}
- `read_file`: Read a file
  - parameters: {"path": "C:\\path\\to\\file.txt"}
- `delete_file`: Delete a file
  - parameters: {"path": "C:\\path\\to\\file.txt"}

### Research
- `research`: Perform web research on a topic
  - parameters: {"topic": "research topic"}

## Response Format

Always respond with a JSON object containing:
- `action`: The action to perform (from the list above)
- `parameters`: Object with the required parameters for the action
- `explanation`: Brief explanation of what you're doing (optional)

Example responses:
```json
{"action": "search_web", "parameters": {"query": "weather in Austin TX"}, "explanation": "Searching for current weather"}
```

```json
{"action": "create_file", "parameters": {"path": "C:\\Users\\Kenda\\Desktop\\notes.txt", "content": "Meeting notes..."}, "explanation": "Creating notes file on desktop"}
```

## Guidelines

1. Be helpful and execute user requests efficiently
2. For ambiguous requests, choose the most reasonable interpretation
3. Use Windows-style paths (backslashes)
4. For dangerous operations, include a warning in your explanation
5. If you cannot fulfill a request, explain why and suggest alternatives
6. When multiple steps are needed, execute one action at a time

Remember: You are controlling a real Windows PC. Be careful with destructive operations."""


class OzCloudClient:
    """Client for running Kencan via Warp's Oz cloud agents"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Oz client"""
        self.config = config
        self.oz_config = config.get('oz', {})
        self.api_key = self.oz_config.get('api_key', '')
        self.environment_id = self.oz_config.get('environment_id', '')
        self.base_url = "https://app.warp.dev/api/v1"
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        
        # Conversation context
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10
        
        # Connection state
        self._last_error: Optional[str] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Oz is properly configured"""
        return bool(self.api_key and self.environment_id)
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    def _build_prompt(self, user_input: str) -> str:
        """Build the full prompt with system instructions and conversation history"""
        # Build conversation context
        history_text = ""
        if self.conversation_history:
            history_text = "\n\n## Recent Conversation\n"
            for entry in self.conversation_history[-self.max_history:]:
                history_text += f"User: {entry['user']}\n"
                history_text += f"Assistant: {entry['assistant']}\n\n"
        
        # Build full prompt
        prompt = f"""{KENCAN_SYSTEM_PROMPT}
{history_text}
## Current Request

User: {user_input}

Respond with a JSON command object:"""
        
        return prompt
    
    def send_user_input(self, user_input: str) -> Dict[str, Any]:
        """Send user input to Oz cloud agent and get response"""
        if not self.is_configured:
            return {
                'success': False,
                'error': 'Oz not configured. Set oz.api_key and oz.environment_id in settings.json'
            }
        
        try:
            prompt = self._build_prompt(user_input)
            
            # Run cloud agent
            response = self.session.post(
                f"{self.base_url}/agent/run",
                json={
                    "prompt": prompt,
                    "config": {
                        "environment_id": self.environment_id
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            run_id = result.get('run_id')
            if not run_id:
                return {'success': False, 'error': 'No run_id returned'}
            
            # Poll for completion
            agent_response = self._wait_for_completion(run_id)
            
            if agent_response.get('success'):
                # Parse the response for command JSON
                response_text = agent_response.get('response', '')
                command = self._parse_command(response_text)
                
                # Save to conversation history
                self.conversation_history.append({
                    'user': user_input,
                    'assistant': response_text
                })
                if len(self.conversation_history) > self.max_history * 2:
                    self.conversation_history.pop(0)
                
                return {
                    'success': True,
                    'response': response_text,
                    'command': command,
                    'run_id': run_id
                }
            
            return agent_response
            
        except requests.exceptions.RequestException as e:
            self._last_error = str(e)
            logger.error(f"Oz API request failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _wait_for_completion(self, run_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll for agent run completion"""
        start_time = time.time()
        poll_interval = 2
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.base_url}/agent/runs/{run_id}",
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                status = result.get('status')
                
                if status == 'completed':
                    return {
                        'success': True,
                        'response': result.get('output', ''),
                        'status': status
                    }
                elif status in ('failed', 'cancelled'):
                    return {
                        'success': False,
                        'error': f"Agent run {status}: {result.get('error', 'Unknown error')}",
                        'status': status
                    }
                
                # Still running, wait and poll again
                time.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, 10)  # Exponential backoff up to 10s
                
            except Exception as e:
                logger.warning(f"Error polling run status: {e}")
                time.sleep(poll_interval)
        
        return {
            'success': False,
            'error': f"Timeout waiting for agent completion after {timeout}s"
        }
    
    def _parse_command(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract command JSON from agent response"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Try to find JSON block
            json_block_match = re.search(r'```json?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_block_match:
                return json.loads(json_block_match.group(1))
            
            return None
        except json.JSONDecodeError:
            return None
    
    def get_commands(self) -> List[Dict[str, Any]]:
        """Get pending commands (for compatibility with polling model)"""
        # Oz uses a request/response model, not polling
        # This method is here for API compatibility
        return []
    
    def clear_conversation(self) -> bool:
        """Clear conversation history"""
        self.conversation_history = []
        return True
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def test_connection(self) -> bool:
        """Test connection to Oz API"""
        if not self.is_configured:
            self._last_error = "Oz not configured"
            return False
        
        try:
            # Test by listing environments (lightweight API call)
            response = self.session.get(
                f"{self.base_url}/environments",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False
