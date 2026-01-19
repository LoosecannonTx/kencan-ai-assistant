# Kencan AI Assistant

A cloud-hosted AI assistant with full PC automation capabilities, designed to run on free cloud GPU platforms and control your local computer.

## Overview

Kencan is an AI assistant system that leverages free cloud GPU resources (Google Colab, Hugging Face Spaces, etc.) to provide powerful AI capabilities while executing tasks on your local PC. The system consists of:

1. **Cloud AI Brain**: Runs on free cloud platforms with GPU acceleration
2. **Local PC Agent**: Executes commands and controls your computer
3. **Communication Bridge**: Secure connection between cloud and local system

## Features

- 🌩️ **Free Cloud GPU**: Runs on Google Colab, Hugging Face Spaces, or other free platforms
- 🖥️ **Full PC Control**: Opens browsers, manages tabs, installs/uninstalls programs
- 🔍 **Web Research**: Automated research and information gathering
- 🎯 **Fine-tunable**: Customizable AI behavior for your specific needs
- 🔒 **Secure**: Local agent only executes authorized commands
- 🚀 **Easy Setup**: Simple configuration and deployment

## Capabilities

Kencan can perform virtually any task on your PC:
- Open and control web browsers (Chrome, Firefox, Edge, etc.)
- Manage browser tabs and navigate websites
- Perform web searches and research
- Install and uninstall programs
- Manage files and folders
- Execute system commands
- Automate repetitive tasks
- And much more!

## Quick Start

1. **Set up the local agent**:
   ```powershell
   cd kencan-ai-assistant
   pip install -r requirements.txt
   python src/local_agent.py --setup
   ```

2. **Deploy to cloud** (choose one):
   - Google Colab: Open `notebooks/kencan_colab.ipynb`
   - Hugging Face Spaces: Follow `docs/huggingface_setup.md`

3. **Connect and run**:
   - Configure connection in `config/settings.json`
   - Start the local agent: `python src/local_agent.py`
   - Your AI assistant is ready!

## Architecture

```
┌─────────────────────────┐
│   Cloud AI (Free GPU)   │
│  - Model inference      │
│  - Decision making      │
│  - Task planning        │
└───────────┬─────────────┘
            │ Secure API
            │
┌───────────▼─────────────┐
│  Communication Bridge   │
│  - WebSocket/HTTP       │
│  - Authentication       │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Local PC Agent        │
│  - Browser control      │
│  - System automation    │
│  - Task execution       │
└─────────────────────────┘
```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Fine-tuning Instructions](docs/FINETUNING.md)
- [Cloud Deployment](docs/CLOUD_DEPLOYMENT.md)
- [Security Considerations](docs/SECURITY.md)
- [API Reference](docs/API.md)

## Requirements

- Python 3.8+
- Windows 10/11 (current implementation)
- Internet connection
- Free cloud platform account (Google, Hugging Face, etc.)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Disclaimer

This system provides powerful automation capabilities. Use responsibly and ensure you understand what commands are being executed on your system. Always review the security settings in `config/settings.json`.
