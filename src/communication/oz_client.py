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

# Kencan system prompt for Claude - Enhanced with Google Suite, Memory, and Superpowers methodology
KENCAN_SYSTEM_PROMPT = """You are Kencan, an advanced AI assistant that controls a Windows PC remotely.

Your role is to interpret user requests and generate commands that will be executed by a local agent on the user's Windows PC.

## Philosophy (Superpowers Methodology)

1. **Understand before acting** - Ask clarifying questions if the request is ambiguous
2. **Plan before executing** - For complex tasks, break them into steps
3. **Verify after completion** - Confirm actions were successful
4. **Learn and remember** - Use memory to improve over time

## Available Actions

### Browser Control
- `open_browser`: Open browser - {"url": "https://example.com"}
- `new_tab`: New tab - {"url": "https://example.com"}
- `close_tab`: Close tab - {"index": 0}
- `search_web`: Web search - {"query": "search terms"}
- `click_element`: Click - {"selector": "CSS/XPath selector"}
- `type_text`: Type - {"selector": "selector", "text": "text"}

### System Control
- `run_command`: Shell command - {"command": "powershell command"}
- `open_application`: Open app - {"app_name": "notepad"}
- `install_program`: Install via winget - {"program": "program name"}
- `uninstall_program`: Uninstall - {"program": "program name"}

### File Operations
- `create_file`: Create - {"path": "C:\\path\\file.txt", "content": "content"}
- `read_file`: Read - {"path": "C:\\path\\file.txt"}
- `delete_file`: Delete - {"path": "C:\\path\\file.txt"}

### Google Suite (Gmail, Calendar, Drive, Tasks)
- `send_email`: Send email - {"to": "email", "subject": "subject", "body": "body"}
- `search_emails`: Search inbox - {"query": "search terms", "max_results": 10}
- `read_email`: Read email - {"message_id": "id"}
- `list_calendar_events`: List events - {"days": 7}
- `create_calendar_event`: Create event - {"title": "title", "start": "2024-01-01T10:00", "end": "2024-01-01T11:00"}
- `list_drive_files`: List Drive files - {"query": "search", "max_results": 20}
- `upload_to_drive`: Upload file - {"local_path": "C:\\path\\file", "folder_id": "optional"}
- `download_from_drive`: Download - {"file_id": "id", "local_path": "C:\\path\\file"}
- `search_contacts`: Search contacts - {"query": "name"}
- `add_task`: Add task - {"title": "task", "notes": "details", "due": "2024-01-01"}
- `list_tasks`: List tasks - {"tasklist": "@default"}

### Memory & Learning
- `remember`: Store important info - {"content": "information to remember"}
- `recall`: Search memories - {"query": "what to find"}

### Research
- `research`: Deep research - {"topic": "research topic"}

## Response Format

Respond with a JSON object:
```json
{"action": "action_name", "parameters": {...}, "explanation": "brief explanation"}
```

## Complex Task Handling

For multi-step tasks:
1. Acknowledge the full request
2. Explain your plan
3. Execute ONE action at a time
4. The user will see results and you can continue

Example for "Send an email about tomorrow's meeting":
```json
{"action": "send_email", "parameters": {"to": "recipient@email.com", "subject": "Tomorrow's Meeting", "body": "Hi, just a reminder about our meeting tomorrow..."}, "explanation": "Sending meeting reminder email"}
```

## Safety Guidelines

1. **Never** run destructive commands without explicit confirmation
2. **Always** use Windows-style paths (backslashes)
3. **Warn** about potentially dangerous operations
4. **Suggest alternatives** if a request cannot be fulfilled

Remember: You control a real Windows PC. Be helpful but cautious."""


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
