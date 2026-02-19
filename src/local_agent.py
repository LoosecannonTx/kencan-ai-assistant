"""
Kencan Local PC Agent
Executes commands on the local Windows PC as directed by the cloud AI
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

# Import automation modules
from automation.browser_control import BrowserController
from automation.system_control import SystemController
from automation.file_operations import FileOperations
from automation.google_suite import GoogleSuiteController
from communication.api_client import CloudAPIClient
from communication.oz_client import OzCloudClient
from utils.logger import setup_logger
from utils.config import load_config
from utils.memory import PersistentMemory
from utils.voice import VoiceAssistant, speak, respond

class LocalAgent:
    """Main local agent that controls PC operations"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """Initialize the local agent"""
        self.config = load_config(config_path)
        self.logger = setup_logger(self.config)
        
        # Initialize controllers
        self.browser = BrowserController(self.config)
        self.system = SystemController(self.config)
        self.files = FileOperations(self.config)
        self.google = GoogleSuiteController(self.config)
        
        # Initialize persistent memory
        self.memory = PersistentMemory()
        self.session_id = None
        
        # Initialize cloud client based on backend setting
        self.backend = self.config.get('agent', {}).get('backend', 'cloud')
        if self.backend == 'oz':
            self.cloud_client = OzCloudClient(self.config)
            self.logger.info("Using Oz cloud agent backend")
        else:
            self.cloud_client = CloudAPIClient(self.config)
            self.logger.info("Using legacy cloud API backend")
        
        self.running = False
        self.voice = None  # Initialized if --voice flag used
        self.voice_enabled = False
        self.logger.info("Local agent initialized")
    
    def enable_voice(self):
        """Enable voice assistant"""
        try:
            self.voice = VoiceAssistant(wake_word="kencan")
            self.voice_enabled = True
            self.logger.info("Voice assistant enabled")
            self.voice.say("Kencan voice assistant activated")
        except Exception as e:
            self.logger.error(f"Failed to enable voice: {e}")
            self.voice_enabled = False
    
    def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command from the cloud AI"""
        action = command.get('action')
        params = command.get('parameters', {})
        
        self.logger.info(f"Executing action: {action}")
        
        try:
            if action == 'open_browser':
                result = self.browser.open_browser(params.get('url'))
            
            elif action == 'new_tab':
                result = self.browser.new_tab(params.get('url'))
            
            elif action == 'close_tab':
                result = self.browser.close_tab(params.get('index'))
            
            elif action == 'search_web':
                result = self.browser.search(params.get('query'))
            
            elif action == 'click_element':
                result = self.browser.click(params.get('selector'))
            
            elif action == 'type_text':
                result = self.browser.type_text(
                    params.get('selector'),
                    params.get('text')
                )
            
            elif action == 'install_program':
                result = self.system.install_program(params.get('program'))
            
            elif action == 'uninstall_program':
                result = self.system.uninstall_program(params.get('program'))
            
            elif action == 'run_command':
                result = self.system.run_command(params.get('command'))
            
            elif action == 'open_application':
                result = self.system.open_application(params.get('app_name'))
            
            elif action == 'create_file':
                result = self.files.create_file(
                    params.get('path'),
                    params.get('content', '')
                )
            
            elif action == 'read_file':
                result = self.files.read_file(params.get('path'))
            
            elif action == 'delete_file':
                result = self.files.delete_file(params.get('path'))
            
            elif action == 'research':
                # Multi-step research task
                result = self._perform_research(params.get('topic'))
            
            # Google Suite actions
            elif action == 'send_email':
                result = self.google.send_email(
                    params.get('to'),
                    params.get('subject'),
                    params.get('body'),
                    params.get('cc'),
                    params.get('bcc')
                )
            
            elif action == 'search_emails':
                result = self.google.search_emails(
                    params.get('query'),
                    params.get('max_results', 10)
                )
            
            elif action == 'read_email':
                result = self.google.read_email(params.get('message_id'))
            
            elif action == 'list_calendar_events':
                result = self.google.list_events(params.get('days', 7))
            
            elif action == 'create_calendar_event':
                result = self.google.create_event(
                    params.get('title'),
                    params.get('start'),
                    params.get('end'),
                    params.get('description'),
                    params.get('location')
                )
            
            elif action == 'list_drive_files':
                result = self.google.list_files(
                    params.get('query'),
                    params.get('max_results', 20)
                )
            
            elif action == 'upload_to_drive':
                result = self.google.upload_file(
                    params.get('local_path'),
                    params.get('folder_id')
                )
            
            elif action == 'download_from_drive':
                result = self.google.download_file(
                    params.get('file_id'),
                    params.get('local_path')
                )
            
            elif action == 'search_contacts':
                result = self.google.search_contacts(params.get('query'))
            
            elif action == 'add_task':
                result = self.google.add_task(
                    params.get('title'),
                    params.get('notes'),
                    params.get('due')
                )
            
            elif action == 'list_tasks':
                result = self.google.list_tasks(params.get('tasklist', '@default'))
            
            # Memory actions
            elif action == 'remember':
                if self.session_id:
                    self.memory.record_learning(self.session_id, params.get('content'), 8)
                result = {'success': True, 'message': 'Remembered'}
            
            elif action == 'recall':
                memories = self.memory.search_memory(params.get('query'), 5)
                result = {'success': True, 'memories': memories}
            
            else:
                result = {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
            
            self.logger.info(f"Action completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _perform_research(self, topic: str) -> Dict[str, Any]:
        """Perform web research on a topic"""
        try:
            # Open browser and search
            self.browser.open_browser()
            results = self.browser.search(topic)
            
            # Get content from top results
            research_data = {
                'topic': topic,
                'results': results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'data': research_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start(self):
        """Start the agent and listen for commands"""
        self.running = True
        self.logger.info("🤖 Kencan Local Agent started")
        
        # Test connection to cloud
        if not self.cloud_client.test_connection():
            self.logger.warning("Cannot connect to cloud AI. Check your configuration.")
            if not self.config.get('local_agent', {}).get('offline_mode', False):
                return
        
        self.logger.info("✅ Connected to cloud AI")
        
        if self.backend == 'oz':
            self._run_interactive_mode()
        else:
            self._run_polling_mode()
    
    def _run_interactive_mode(self):
        """Run in interactive mode with Oz backend (request/response)"""
        self.logger.info("Running in interactive mode (Oz backend)")
        print("\n🤖 Kencan is ready! Type your requests below.")
        print("Type 'quit' to exit, 'clear' to reset conversation.")
        if self.voice_enabled:
            print("Voice enabled - say 'Kencan' to use voice commands.")
            self.voice.say("Ready! Type or speak your requests.")
        print()
        
        while self.running:
            try:
                # Get input (text or voice)
                if self.voice_enabled:
                    user_input = self._get_input_with_voice()
                else:
                    user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                if user_input.lower() == 'quit':
                    self.logger.info("User requested quit")
                    if self.voice_enabled:
                        self.voice.say("Goodbye!")
                    self.running = False
                    break
                if user_input.lower() == 'clear':
                    self.cloud_client.clear_conversation()
                    msg = "Conversation cleared."
                    print(msg + "\n")
                    if self.voice_enabled:
                        self.voice.say(msg)
                    continue
                if user_input.lower() == 'voice':
                    # Toggle voice listening
                    if self.voice_enabled:
                        spoken = self.voice.listen_once()
                        if spoken:
                            user_input = spoken
                            print(f"You (voice): {user_input}")
                        else:
                            print("Didn't catch that. Try again.")
                            continue
                    else:
                        print("Voice not enabled. Start with --voice flag.")
                        continue
                
                # Send to Oz and get response
                print("Thinking...")
                if self.voice_enabled:
                    self.voice.say("Let me think...")
                    
                response = self.cloud_client.send_user_input(user_input)
                
                if response.get('success'):
                    response_text = response.get('response', '')
                    print(f"\nKencan: {response_text}\n")
                    
                    # Speak response (truncated for TTS)
                    if self.voice_enabled and response_text:
                        # Speak just the explanation or first sentence
                        speak_text = response_text.split('.')[0] + '.'
                        if len(speak_text) > 200:
                            speak_text = speak_text[:200] + '...'
                        self.voice.say(speak_text)
                    
                    # Execute the command if one was parsed
                    command = response.get('command')
                    if command and command.get('action'):
                        action_name = command.get('action')
                        print(f"Executing: {action_name}...")
                        if self.voice_enabled:
                            self.voice.say(f"Executing {action_name}")
                        result = self.execute_command(command)
                        if result.get('success'):
                            msg = result.get('message', 'Done')
                            print(f"✅ {msg}\n")
                            if self.voice_enabled:
                                self.voice.say(msg)
                        else:
                            err = result.get('error', 'Unknown error')
                            print(f"❌ Error: {err}\n")
                            if self.voice_enabled:
                                self.voice.say(f"Error: {err}")
                else:
                    err = response.get('error', 'Unknown error')
                    print(f"\n❌ Error: {err}\n")
                    if self.voice_enabled:
                        self.voice.say(f"Sorry, there was an error")
                    
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                self.running = False
                break
            except EOFError:
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Error in interactive loop: {str(e)}")
                print(f"\n❌ Error: {str(e)}\n")
    
    def _run_polling_mode(self):
        """Run in polling mode with legacy cloud backend"""
        self.logger.info("Listening for commands...")
        
        while self.running:
            try:
                # Poll for commands from cloud
                commands = self.cloud_client.get_commands()
                
                for command in commands:
                    result = self.execute_command(command)
                    self.cloud_client.send_result(command['id'], result)
                
                time.sleep(1)  # Poll interval
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(5)
    
    def _get_input_with_voice(self) -> str:
        """Get input from keyboard, with voice as fallback"""
        import sys
        import select
        
        # Simple blocking input for Windows
        return input("You: ").strip()
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        self.browser.cleanup()
        if self.voice:
            self.voice.cleanup()
        self.logger.info("Agent stopped")

def setup():
    """Interactive setup for first-time configuration"""
    print("🚀 Kencan Local Agent Setup")
    print("=" * 50)
    
    config_path = Path("config/settings.json")
    if config_path.exists():
        response = input("Configuration already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\n1. Cloud Configuration")
    platform = input("Cloud platform (colab/huggingface): ").strip() or "colab"
    endpoint = input("Cloud endpoint URL: ").strip()
    api_key = input("API key (optional): ").strip()
    
    print("\n2. Agent Configuration")
    expose = input("Expose agent publicly via ngrok? (y/n): ").lower() == 'y'
    ngrok_token = ""
    if expose:
        ngrok_token = input("Ngrok auth token: ").strip()
    
    print("\n3. Security Settings")
    require_confirm = input("Require confirmation for commands? (y/n): ").lower() == 'y'
    
    # Update config
    config = load_config("config/settings.json")
    config['cloud']['platform'] = platform
    config['cloud']['endpoint'] = endpoint
    if api_key:
        config['cloud']['api_key'] = api_key
    config['local_agent']['expose_public'] = expose
    if ngrok_token:
        config['local_agent']['ngrok_auth_token'] = ngrok_token
    config['security']['require_confirmation'] = require_confirm
    
    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Setup complete!")
    print(f"Configuration saved to {config_path}")
    print("\nNext steps:")
    print("1. Deploy the cloud AI using notebooks/kencan_colab.ipynb")
    print("2. Update the endpoint URL in config/settings.json")
    print("3. Run: python src/local_agent.py")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Kencan Local PC Agent")
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    parser.add_argument('--config', type=str, default='config/settings.json',
                       help='Path to configuration file')
    parser.add_argument('--voice', action='store_true', help='Enable voice assistant')
    
    args = parser.parse_args()
    
    if args.setup:
        setup()
        return
    
    # Start agent
    agent = LocalAgent(args.config)
    
    if args.voice:
        agent.enable_voice()
    
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()

if __name__ == "__main__":
    main()
