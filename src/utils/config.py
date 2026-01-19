"""
Configuration utilities for Kencan
"""

import json
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to JSON file"""
    try:
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False
