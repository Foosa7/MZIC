# app/utils/config_manager.py
import os
import json
from copy import deepcopy

class ConfigManager:
    def __init__(self, default_config_path, user_config_path=None):
        self.default_config_path = default_config_path
        self.user_config_path = user_config_path
        self.config = self._load_config()
    
    def _load_config(self):
        # Load default configuration
        with open(self.default_config_path, 'r') as f:
            config = json.load(f)
        
        # Override with user configuration if available
        if self.user_config_path and os.path.exists(self.user_config_path):
            with open(self.user_config_path, 'r') as f:
                user_config = json.load(f)
                self._deep_update(config, user_config)
        
        return config
    
    def _deep_update(self, base, update):
        """Recursively update a nested dictionary."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key, default=None):
        """Get a configuration value by key."""
        return self.config.get(key, default)
    
    def get_all(self):
        """Get the entire configuration."""
        return deepcopy(self.config)
    
    def save_user_config(self, config_updates):
        """Save updated user configuration."""
        if not self.user_config_path:
            raise ValueError("User configuration path not specified")
        
        # Load existing user config or create new
        if os.path.exists(self.user_config_path):
            with open(self.user_config_path, 'r') as f:
                user_config = json.load(f)
        else:
            user_config = {}
        
        # Update user config with new values
        self._deep_update(user_config, config_updates)
        
        # Save updated user config
        os.makedirs(os.path.dirname(self.user_config_path), exist_ok=True)
        with open(self.user_config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
        
        # Update current config
        self._deep_update(self.config, config_updates)
