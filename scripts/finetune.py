"""
Fine-tuning script for Kencan AI Assistant
Customize the AI for your specific needs and PC control tasks
"""

import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import argparse
from pathlib import Path

def load_training_data(data_path: str):
    """Load training data from JSON file"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def prepare_dataset(data, tokenizer):
    """Prepare dataset for training"""
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=512
        )
    
    # Convert to dataset format
    texts = []
    for item in data:
        # Format: instruction + response
        text = f"Instruction: {item['instruction']}\nResponse: {item['response']}"
        texts.append(text)
    
    dataset = Dataset.from_dict({'text': texts})
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    return tokenized_dataset

def finetune_model(
    model_name: str,
    training_data_path: str,
    output_dir: str,
    num_epochs: int = 3,
    learning_rate: float = 2e-5
):
    """Fine-tune the model on custom data"""
    
    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("Loading training data...")
    training_data = load_training_data(training_data_path)
    
    print("Preparing dataset...")
    dataset = prepare_dataset(training_data, tokenizer)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        fp16=torch.cuda.is_available(),
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none"
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator
    )
    
    print("Starting fine-tuning...")
    trainer.train()
    
    print(f"Saving model to {output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    print("✅ Fine-tuning complete!")

def create_sample_training_data(output_path: str):
    """Create sample training data file"""
    sample_data = [
        {
            "instruction": "Open Chrome browser",
            "response": '{"action": "open_browser", "parameters": {"browser": "chrome"}}'
        },
        {
            "instruction": "Search for Python tutorials",
            "response": '{"action": "search_web", "parameters": {"query": "Python tutorials"}}'
        },
        {
            "instruction": "Install Visual Studio Code",
            "response": '{"action": "install_program", "parameters": {"program": "Microsoft.VisualStudioCode"}}'
        },
        {
            "instruction": "Create a new file called test.txt",
            "response": '{"action": "create_file", "parameters": {"path": "test.txt", "content": ""}}'
        },
        {
            "instruction": "Open Notepad",
            "response": '{"action": "open_application", "parameters": {"app_name": "notepad"}}'
        }
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Sample training data created at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Kencan AI Assistant")
    parser.add_argument('--model', type=str, default='microsoft/phi-2',
                       help='Base model to fine-tune')
    parser.add_argument('--data', type=str, required=False,
                       help='Path to training data JSON file')
    parser.add_argument('--output', type=str, default='models/kencan-finetuned',
                       help='Output directory for fine-tuned model')
    parser.add_argument('--epochs', type=int, default=3,
                       help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=2e-5,
                       help='Learning rate')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample training data file')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_training_data('data/sample_training_data.json')
        return
    
    if not args.data:
        print("Error: --data argument required (or use --create-sample to generate sample data)")
        return
    
    finetune_model(
        model_name=args.model,
        training_data_path=args.data,
        output_dir=args.output,
        num_epochs=args.epochs,
        learning_rate=args.lr
    )

if __name__ == "__main__":
    main()
