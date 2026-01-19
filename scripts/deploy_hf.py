"""
Hugging Face Spaces Deployment Script for Kencan AI Assistant
This script helps deploy Kencan to Hugging Face Spaces with free GPU
"""

import os
import sys

def create_hf_files():
    """Create necessary files for HF Spaces deployment"""
    
    # app.py for Gradio interface
    app_content = '''
import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
import json

# Load model
MODEL_NAME = "microsoft/phi-2"
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("Model loaded!")

def process_command(user_input, api_key):
    """Process user command and generate response"""
    if not user_input:
        return "Please provide a command"
    
    prompt = f"""You are Kencan, an AI assistant that controls a Windows PC.
User request: {user_input}
Provide specific instructions for the action to take.
Response:"""
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return response

# Create Gradio interface
with gr.Blocks(title="Kencan AI Assistant") as demo:
    gr.Markdown("# 🤖 Kencan AI Assistant")
    gr.Markdown("Cloud-hosted AI with free GPU for PC automation")
    
    with gr.Row():
        with gr.Column():
            user_input = gr.Textbox(
                label="Your Command",
                placeholder="e.g., Open Chrome and search for Python tutorials",
                lines=3
            )
            api_key = gr.Textbox(
                label="API Key (optional)",
                placeholder="Your authentication key",
                type="password"
            )
            submit_btn = gr.Button("Send Command", variant="primary")
        
        with gr.Column():
            output = gr.Textbox(label="AI Response", lines=10)
    
    submit_btn.click(
        fn=process_command,
        inputs=[user_input, api_key],
        outputs=output
    )
    
    gr.Markdown("""
    ### How to use:
    1. Enter your command above
    2. Click "Send Command"
    3. Copy the response to your local agent
    4. The local agent will execute the action
    
    ### API Endpoint:
    Use `/api/predict` endpoint to send commands programmatically
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
'''
    
    # requirements.txt for HF Spaces
    requirements = '''transformers>=4.35.0
torch>=2.1.0
accelerate>=0.25.0
gradio>=4.0.0
requests>=2.31.0
'''
    
    # README for HF Spaces
    readme = '''---
title: Kencan AI Assistant
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# Kencan AI Assistant

Cloud-hosted AI assistant with free GPU for PC automation and control.

## Features
- Free GPU inference
- Browser automation
- System control
- Web research
- Fully customizable

## Usage
1. Enter your command in the interface
2. Get AI-generated instructions
3. Execute on your local PC via the local agent

Visit the repository for full setup instructions.
'''
    
    print("Creating Hugging Face Spaces files...")
    
    hf_dir = "hf_spaces"
    os.makedirs(hf_dir, exist_ok=True)
    
    with open(os.path.join(hf_dir, "app.py"), "w") as f:
        f.write(app_content)
    
    with open(os.path.join(hf_dir, "requirements.txt"), "w") as f:
        f.write(requirements)
    
    with open(os.path.join(hf_dir, "README.md"), "w") as f:
        f.write(readme)
    
    print(f"✅ Files created in {hf_dir}/")
    print("\nNext steps:")
    print("1. Create a new Space on huggingface.co/spaces")
    print("2. Upload these files to your Space")
    print("3. Enable GPU in Space settings (free tier available)")
    print("4. Your API will be live at: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE")

if __name__ == "__main__":
    create_hf_files()
