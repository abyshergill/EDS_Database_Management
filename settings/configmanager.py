import os
import logging
import json

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "database": {
                "type": "sqlite",  # or "postgresql"
                "sqlite_path": "eds.db",
                # "postgresql": {
                #     "host": "localhost",
                #     "port": 5432,
                #     "database": "eds_db",
                #     "user": "postgres",
                #     "password": "password"
                # }
            },
            "ui": {
                "theme": "modern",
                "window_size": "900x750"
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return self.default_config
    
    def save_config(self, config):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get(self, key_path, default=None):
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value