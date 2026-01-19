# Kencan AI Assistant - Setup Guide

Complete guide to setting up Kencan on your PC with free cloud GPU.

## Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Internet connection
- Google account (for Colab) OR Hugging Face account

## Part 1: Local Agent Setup

### Step 1: Install Python Dependencies

```powershell
cd kencan-ai-assistant
pip install -r requirements.txt
```

This will install all necessary packages including:
- Selenium for browser automation
- PyAutoGUI for UI control
- Flask for API server
- Transformers for AI models
- And more...

### Step 2: Configure the Agent

Run the interactive setup:

```powershell
python src/local_agent.py --setup
```

You'll be prompted to configure:
- Cloud platform (Colab or Hugging Face)
- Connection settings
- Security preferences

Alternatively, manually edit `config/settings.json`:

```json
{
  "cloud": {
    "platform": "colab",
    "endpoint": "https://your-ngrok-url.ngrok.io",
    "api_key": "optional_api_key"
  },
  "security": {
    "require_confirmation": false
  }
}
```

### Step 3: Install Chrome WebDriver

The browser automation requires Chrome and ChromeDriver:

1. Make sure Google Chrome is installed
2. ChromeDriver will be automatically installed when you first run the agent

## Part 2: Cloud AI Deployment

### Option A: Google Colab (Recommended for Beginners)

1. **Get an ngrok account** (free):
   - Visit https://ngrok.com
   - Sign up for free account
   - Get your auth token from the dashboard

2. **Open the Colab notebook**:
   - Go to https://colab.research.google.com
   - Upload `notebooks/kencan_colab.ipynb`
   - Or open from GitHub if you've pushed the project

3. **Enable GPU**:
   - Runtime → Change runtime type
   - Hardware accelerator → GPU (T4 is free!)
   - Save

4. **Run the notebook**:
   - Update the `NGROK_AUTH_TOKEN` in the config cell
   - Run all cells in order
   - Copy the ngrok URL that's displayed

5. **Update local configuration**:
   - Paste the ngrok URL into `config/settings.json` as the `endpoint`

### Option B: Hugging Face Spaces

1. **Create a Space**:
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Gradio" as the SDK
   - Enable GPU in settings (free tier available)

2. **Generate deployment files**:
   ```powershell
   python scripts/deploy_hf.py
   ```

3. **Upload files**:
   - Upload contents of `hf_spaces/` directory to your Space
   - The Space will automatically start

4. **Get the endpoint**:
   - Your Space URL will be: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE`
   - Use this as your endpoint

## Part 3: First Run

### Start the Local Agent

```powershell
python src/local_agent.py
```

You should see:
```
🤖 Kencan Local Agent started
✅ Connected to cloud AI
Listening for commands...
```

### Test the Connection

Send a test command from the cloud interface or use the Python API:

```python
from communication.api_client import CloudAPIClient
import json

config = json.load(open('config/settings.json'))
client = CloudAPIClient(config)

# Test connection
if client.test_connection():
    print("✅ Connection successful!")
    
    # Send a command
    response = client.send_user_input("Open Chrome")
    print(response)
```

## Part 4: Security Configuration

### Command Blocking

Edit `config/settings.json` to block dangerous commands:

```json
{
  "security": {
    "blocked_commands": [
      "format",
      "del C:\\Windows",
      "rm -rf /",
      "shutdown"
    ]
  }
}
```

### Require Confirmation

Set `require_confirmation: true` to manually approve each command before execution.

## Troubleshooting

### Issue: "Cannot connect to cloud AI"

**Solution:**
1. Check that the cloud notebook/space is running
2. Verify the endpoint URL in `config/settings.json`
3. Test the URL in a browser - should show a health check page

### Issue: "ChromeDriver not found"

**Solution:**
1. Make sure Chrome is installed
2. Run the agent once - it will auto-download the driver
3. Or manually install: `pip install webdriver-manager`

### Issue: "Module not found"

**Solution:**
```powershell
pip install -r requirements.txt --upgrade
```

### Issue: Ngrok connection timeout

**Solution:**
- Free ngrok tunnels expire after 2 hours
- Restart the Colab notebook to get a new URL
- Update the endpoint in `config/settings.json`

## Next Steps

- **Customize AI**: See [FINETUNING.md](FINETUNING.md) for fine-tuning instructions
- **Advanced Usage**: Check [API.md](API.md) for API documentation
- **Security**: Read [SECURITY.md](SECURITY.md) for security best practices

## Getting Help

If you encounter issues:
1. Check the logs in `logs/kencan.log`
2. Review error messages in the console
3. Open an issue on GitHub with logs and error details
