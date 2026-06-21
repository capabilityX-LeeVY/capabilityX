import json
from pathlib import Path
from typing import Any

class DictWrapper:
    def __init__(self, data):
        self._data = data if data is not None else {}
    
    def __getattr__(self, key: str) -> Any:
        if key == '_data':
            return object.__getattribute__(self, '_data')
        value = self._data.get(key)
        if isinstance(value, dict):
            return DictWrapper(value)
        return value
    
    def __getitem__(self, key):
        """Support dict-style access: obj['key']"""
        value = self._data[key]
        if isinstance(value, dict):
            return DictWrapper(value)
        return value
    
    def get(self, key, default=None):
        """Support dict.get() method"""
        value = self._data.get(key, default)
        if isinstance(value, dict):
            return DictWrapper(value)
        return value
    
    def __bool__(self):
        """Support truthiness check: if obj:"""
        return bool(self._data)
    
    def __len__(self):
        """Support len(obj)"""
        return len(self._data)
    
    def __iter__(self):
        """Support iteration: for key in obj:"""
        return iter(self._data)
    
    def __contains__(self, key):
        """Support 'key in obj' check"""
        return key in self._data
    
    def keys(self):
        """Support obj.keys()"""
        return self._data.keys()
    
    def values(self):
        """Support obj.values()"""
        return self._data.values()
    
    def items(self):
        """Support obj.items()"""
        return self._data.items()
    
    def __repr__(self):
        return f"DictWrapper({self._data})"
    
    def __str__(self):
        return str(self._data)

class DynamicConfig:
    def __init__(self, config_path):
        self.config_path = config_path
        # Ensure the config file exists before loading
        self._ensure_config_exists()
        self.loadConfig()

    def _ensure_config_exists(self):
        """Create a config file with default settings if it doesn't exist"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            # Create directory if it doesn't exist
            config_file.parent.mkdir(parents=True, exist_ok=True)
            # Create config file with default settings
            default_config = {
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)

    def loadConfig(self):
        with open(self.config_path, 'r', encoding='utf-8-sig') as f:
            self.config = json.load(f)

    def saveConfig(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def __getattr__(self, key: str) -> Any:
        if key in ('config', 'config_path'):
            return object.__getattribute__(self, key)
        value = self.get(key)
        if isinstance(value, dict):
            return DictWrapper(value)
        return value

    def set(self, key, value):          
        # 🔧 FIX: Reload config before setting to avoid overwriting external changes
        self.loadConfig()  # Ensure we have the latest config from file
        self.config[key] = value
        self.saveConfig()
