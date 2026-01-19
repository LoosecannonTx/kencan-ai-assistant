# Fine-Tuning Kencan AI Assistant

Learn how to customize Kencan's behavior for your specific needs using free cloud GPUs.

## Why Fine-Tune?

Fine-tuning allows you to:
- Teach Kencan your specific workflows
- Improve accuracy for your common tasks
- Add custom commands and behaviors
- Adapt to your PC's specific setup

## Quick Start

### 1. Create Training Data

Generate sample training data:

```powershell
python scripts/finetune.py --create-sample
```

This creates `data/sample_training_data.json` with example format:

```json
[
  {
    "instruction": "Open Chrome browser",
    "response": "{\"action\": \"open_browser\", \"parameters\": {\"browser\": \"chrome\"}}"
  },
  {
    "instruction": "Search for Python tutorials",
    "response": "{\"action\": \"search_web\", \"parameters\": {\"query\": \"Python tutorials\"}}"
  }
]
```

### 2. Add Your Custom Data

Edit the JSON file to include your specific tasks:

```json
[
  {
    "instruction": "Open my project folder",
    "response": "{\"action\": \"run_command\", \"parameters\": {\"command\": \"explorer C:\\\\Users\\\\YourName\\\\Projects\"}}"
  },
  {
    "instruction": "Start my dev environment",
    "response": "{\"action\": \"run_command\", \"parameters\": {\"command\": \"code C:\\\\Users\\\\YourName\\\\Projects && npm start\"}}"
  }
]
```

### 3. Fine-Tune on Google Colab

**Option A: Use the Colab Notebook** (Easiest)

1. Upload your training data to Google Drive
2. Open a new Colab notebook
3. Enable GPU (Runtime → Change runtime type → GPU)
4. Run the fine-tuning script:

```python
# Install dependencies
!pip install transformers datasets accelerate torch

# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Clone your project or upload training script
!git clone https://github.com/yourusername/kencan-ai-assistant.git
%cd kencan-ai-assistant

# Run fine-tuning
!python scripts/finetune.py \
    --model microsoft/phi-2 \
    --data /content/drive/MyDrive/training_data.json \
    --output /content/drive/MyDrive/kencan-finetuned \
    --epochs 3
```

**Option B: Local Fine-Tuning** (If you have a GPU)

```powershell
python scripts/finetune.py \
    --model microsoft/phi-2 \
    --data data/my_training_data.json \
    --output models/kencan-finetuned \
    --epochs 3
```

### 4. Deploy Your Fine-Tuned Model

Update the Colab notebook to use your model:

```python
# Instead of:
MODEL_NAME = "microsoft/phi-2"

# Use:
MODEL_NAME = "/content/drive/MyDrive/kencan-finetuned"
```

## Training Data Format

### Structure

Each training example should have:
- `instruction`: What the user wants to do
- `response`: The JSON command to execute

### Best Practices

1. **Be Specific**: Include variations of how you might phrase commands
   ```json
   [
     {"instruction": "open chrome", "response": "..."},
     {"instruction": "launch chrome browser", "response": "..."},
     {"instruction": "start google chrome", "response": "..."}
   ]
   ```

2. **Include Context**: Add examples with context
   ```json
   {
     "instruction": "I need to check my email",
     "response": "{\"action\": \"open_browser\", \"parameters\": {\"url\": \"https://gmail.com\"}}"
   }
   ```

3. **Cover Edge Cases**: Include error handling
   ```json
   {
     "instruction": "open notepad",
     "response": "{\"action\": \"open_application\", \"parameters\": {\"app_name\": \"notepad.exe\"}}"
   }
   ```

4. **Multi-Step Tasks**: Break down complex workflows
   ```json
   {
     "instruction": "set up my workspace",
     "response": "{\"action\": \"run_command\", \"parameters\": {\"command\": \"start chrome && start code && start spotify\"}}"
   }
   ```

## Available Actions

When creating training data, use these actions:

| Action | Description | Parameters |
|--------|-------------|------------|
| `open_browser` | Open web browser | `url` (optional) |
| `new_tab` | Open new browser tab | `url` (optional) |
| `search_web` | Search on Google | `query` |
| `install_program` | Install via winget | `program` |
| `uninstall_program` | Uninstall program | `program` |
| `open_application` | Launch application | `app_name` |
| `run_command` | Run shell command | `command` |
| `create_file` | Create a file | `path`, `content` |
| `research` | Perform web research | `topic` |

## Advanced Fine-Tuning

### Custom Model Selection

Try different base models:

```powershell
# Smaller, faster model
python scripts/finetune.py --model microsoft/phi-2

# Larger, more capable model (requires more VRAM)
python scripts/finetune.py --model mistralai/Mistral-7B-v0.1

# Code-focused model
python scripts/finetune.py --model Salesforce/codegen-350M-mono
```

### Hyperparameter Tuning

Adjust training parameters:

```powershell
python scripts/finetune.py \
    --data data/training.json \
    --epochs 5 \
    --lr 3e-5 \
    --output models/kencan-custom
```

### Using LoRA for Efficient Fine-Tuning

For large models with limited VRAM, use LoRA (Low-Rank Adaptation):

```python
# Add to finetune.py
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
```

## Collecting Training Data

### Automatic Data Collection

Log your interactions to build training data:

1. Enable logging in `config/settings.json`:
   ```json
   {
     "logging": {
       "save_interactions": true,
       "interaction_file": "data/interactions.json"
     }
   }
   ```

2. Use Kencan normally for a few days
3. Review and clean the logged data
4. Use it for fine-tuning

### Manual Curation

Create a spreadsheet with common tasks:

| What I Say | What Should Happen | Command |
|------------|-------------------|---------|
| "open vscode" | Launch VS Code | `open_application` |
| "check email" | Open Gmail | `open_browser` |
| "install python" | Install Python | `install_program` |

Convert to JSON format for training.

## Testing Your Fine-Tuned Model

After fine-tuning:

1. Deploy the model to Colab/HF Spaces
2. Update your local agent's endpoint
3. Test with various commands
4. Monitor accuracy and behavior

## Troubleshooting

### Out of Memory Error

- Reduce batch size in training arguments
- Use a smaller model
- Enable gradient accumulation
- Try LoRA fine-tuning

### Poor Performance

- Add more training examples (aim for 100+)
- Include more diverse phrasings
- Increase training epochs
- Check for typos in training data

### Model Not Following Instructions

- Make sure response format is valid JSON
- Include more examples of the desired behavior
- Increase learning rate slightly
- Fine-tune for more epochs

## Free Cloud Resources

- **Google Colab**: Free T4 GPU (limited hours)
- **Kaggle Notebooks**: Free P100 GPU (30 hours/week)
- **Paperspace Gradient**: Free GPU tier available
- **Lightning AI Studio**: Free GPU compute
