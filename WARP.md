# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Kencan is a cloud-hosted AI assistant with full PC automation capabilities. It consists of three main components:
1. **Cloud AI Brain** - Runs on free cloud GPU platforms (Google Colab, Hugging Face Spaces) with model inference and decision-making
2. **Local PC Agent** - Python-based agent that executes commands on Windows PC
3. **Communication Bridge** - API-based connection (WebSocket/HTTP) between cloud and local system

The system enables browser automation, system control, file operations, and web research capabilities through a command-action architecture.

## Common Development Commands

### Setup and Installation
```powershell
# Install dependencies
pip install -r requirements.txt

# Run interactive setup (first-time configuration)
python src/local_agent.py --setup

# Install dependencies with upgrade
pip install -r requirements.txt --upgrade
```

### Running the Application
```powershell
# Start the local agent with default config
python src/local_agent.py

# Start with custom config
python src/local_agent.py --config path/to/config.json
```

### Testing
No formal test suite is currently defined. Manual testing is done by:
1. Starting the local agent
2. Sending test commands from the cloud interface or API client
3. Checking logs in `logs/kencan.log`

### Fine-tuning and Deployment
```powershell
# Create sample training data
python scripts/finetune.py --create-sample

# Fine-tune model (if you have local GPU)
python scripts/finetune.py --model microsoft/phi-2 --data data/training.json --output models/kencan-finetuned --epochs 3

# Generate Hugging Face Space deployment files
python scripts/deploy_hf.py
```

### Logs
```powershell
# View logs (location configured in config/settings.json)
Get-Content logs/kencan.log -Tail 50 -Wait
```

## Architecture Details

### Command Execution Flow
1. Cloud AI receives user input and generates a command JSON
2. Command is sent to local agent via API endpoint
3. Local agent polls for commands using `CloudAPIClient.get_commands()`
4. `LocalAgent.execute_command()` routes to appropriate controller based on `action` field
5. Controller (Browser/System/File) executes the operation
6. Result is sent back to cloud via `CloudAPIClient.send_result()`

### Module Structure

**`src/local_agent.py`** - Main entry point and command orchestrator
- `LocalAgent` class manages all controllers and command routing
- Maps action strings to controller methods
- Handles main event loop and cloud polling

**`src/automation/`** - Automation controllers
- `browser_control.py`: Selenium-based browser automation (BrowserController)
- `system_control.py`: Windows system operations via subprocess, psutil, winshell (SystemController)
- `file_operations.py`: File/directory operations using pathlib (FileOperations)

**`src/communication/`** - Cloud communication
- `api_client.py`: HTTP client for cloud AI communication (CloudAPIClient)
- Handles connection testing, command polling, and result reporting

**`src/utils/`** - Utilities
- `config.py`: JSON configuration loading/saving
- `logger.py`: Logging setup (not shown but referenced)

### Command Action Schema
Commands from cloud AI follow this structure:
```json
{
  "id": "command_id",
  "action": "action_name",
  "parameters": {
    "param1": "value1"
  }
}
```

Available actions and their parameters are documented in `src/local_agent.py` (lines 40-111).

### Configuration System
All configuration is stored in `config/settings.json` with sections:
- `agent`: Basic agent metadata
- `cloud`: Cloud endpoint, API key, connection settings
- `local_agent`: Local server settings, ngrok config
- `capabilities`: Feature flags for different operation types
- `security`: Command blocking, confirmation requirements, timeouts
- `browser`: Browser automation settings (headless mode, user data dir)
- `logging`: Log level and output configuration

### Security Model
Security is enforced in `SystemController._is_command_allowed()`:
- Blocks commands matching patterns in `security.blocked_commands`
- Default blocked: `format`, `del C:\Windows`, `rm -rf /`
- Optional confirmation mode via `security.require_confirmation`
- Command timeouts enforced via `security.command_timeout`

## Important Implementation Notes

### Windows-Specific Dependencies
This project is **Windows-only**. Key dependencies:
- `pywin32` - Windows API access
- `winshell` - Windows shell operations
- System commands assume PowerShell/cmd.exe

When making changes, ensure compatibility with Windows paths (backslashes), Windows-specific commands (winget, explorer), and Windows process management.

### Browser Automation
- Uses Selenium WebDriver with Chrome as default browser
- ChromeDriver is auto-installed via `webdriver-manager`
- Browser instance persists across commands until cleanup
- Headless mode supported but disabled by default

### Cloud Connection Architecture
The local agent uses a **polling model**:
- Polls cloud endpoint every 1 second for new commands
- Requires cloud to maintain a command queue
- Connection test via `/health` endpoint
- Commands retrieved from `/commands/pending`
- Results posted to `/commands/{id}/result`

### Error Handling Pattern
All controller methods return a consistent result format:
```python
{
  'success': bool,
  'message'?: str,  # on success
  'error'?: str,    # on failure
  'data'?: any      # additional data
}
```

## Development Workflow

### Adding New Actions
1. Add action handler in `LocalAgent.execute_command()` (around line 40)
2. Implement the operation in appropriate controller (Browser/System/File)
3. Update `capabilities` in `config/settings.json` if adding new capability type
4. Document the action in training data format for fine-tuning (see docs/FINETUNING.md)

### Modifying Configuration
- Edit `config/settings.json` directly, or
- Use `python src/local_agent.py --setup` for interactive configuration
- Configuration is loaded once at agent startup

### Cloud Deployment
- **Google Colab**: Use `notebooks/kencan_colab.ipynb`
  - Requires ngrok auth token for public endpoint
  - Free T4 GPU, but sessions timeout after ~2 hours
  - Must update local config with new ngrok URL after restart
- **Hugging Face Spaces**: Use `scripts/deploy_hf.py` to generate deployment files
  - Persistent endpoint URL
  - Free GPU tier available

## File Paths and Conventions

- Configuration: `config/settings.json`
- Logs: `logs/kencan.log` (configurable)
- Training data: `data/` directory
- Fine-tuned models: `models/` directory
- Cloud notebooks: `notebooks/`
- Documentation: `docs/` (SETUP.md, FINETUNING.md)

## Key Constraints and Gotchas

1. **Ngrok Free Tier Limitation**: Free ngrok tunnels expire after 2 hours. When using Google Colab, you must restart the notebook and update `config/settings.json` with the new URL periodically.

2. **Command Blocking**: Be careful when adding system commands - verify they won't be blocked by `security.blocked_commands`. The check is case-insensitive substring matching.

3. **Browser State**: The BrowserController maintains a single WebDriver instance. Multiple tabs are supported but managed through window handles. Always check if `self.driver is None` before operations.

4. **Windows Path Escaping**: When creating training data or config entries with Windows paths, use double backslashes (`C:\\\\Users\\\\...`) in JSON.

5. **Offline Mode**: The agent supports offline mode if cloud connection fails and `local_agent.offline_mode` is enabled, but this functionality is limited.

6. **No Async**: Current implementation uses synchronous polling and blocking operations. Be mindful of command timeouts.
