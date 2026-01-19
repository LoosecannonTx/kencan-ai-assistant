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
from communication.api_client import CloudAPIClient
from utils.logger import setup_logger
from utils.config import load_config

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
        self.cloud_client = CloudAPIClient(self.config)
        
        self.running = False
        self.logger.info("Local agent initialized")
    
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
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        self.browser.cleanup()
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
    
    args = parser.parse_args()
    
    if args.setup:
        setup()
        return
    
    # Start agent
    agent = LocalAgent(args.config)
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()

if __name__ == "__main__":
    main()
