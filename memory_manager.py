import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib

class MemoryManager:
    def __init__(self, memory_dir: str = "./memory"):
        self.memory_dir = memory_dir
        self.ensure_memory_dir()
        
    def ensure_memory_dir(self):
        """Create memory directory if it doesn't exist"""
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
    
    def get_app_signature(self, app_path: str = ".") -> str:
        """Create a unique signature for the application based on its structure"""
        signature_data = []
        
        # Get key files that define the app (core identity)
        key_files = [
            "package.json", "composer.json", "requirements.txt", 
            "Dockerfile", "docker-compose.yml", ".env.example",
            "main.py", "app.py", "index.js", "app.js"
        ]
        
        for file in key_files:
            file_path = os.path.join(app_path, file)
            if os.path.exists(file_path):
                signature_data.append(file)
        
        # Add core directory structure (only essential directories)
        core_dirs = []
        