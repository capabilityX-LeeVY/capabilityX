"""
Account configuration handler for test cases
"""
import json
import os
from pathlib import Path
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


class AccountConfigHandler:
    """Handle account configuration for test cases"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent / "account.json"
        
        self.config_path = config_path
        self.accounts = self._load_accounts()
    
    def _load_accounts(self):
        """Load account configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                LOGGER_ERROR(f"Account config file not found: {self.config_path}", "RED")
                return {}
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                LOGGER_INFO(f"Loaded {len(accounts)} account configurations", "GREEN")
                return accounts
        except Exception as e:
            LOGGER_ERROR(f"Failed to load account config: {str(e)}", "RED")
            return {}
    
    def get_account_info(self, account_name=None):
        """
        Get account information by account name
        
        Args:
            account_name (str): Account name, defaults to 'default' if None
            
        Returns:
            dict: Account info with 'email' and 'password' keys, or None if not found
        """
        if account_name is None:
            account_name = "default"
        
        if account_name in self.accounts:
            account_info = self.accounts[account_name]
            LOGGER_INFO(f"Using account '{account_name}': {account_info['email']}", "CYAN")
            return account_info
        else:
            LOGGER_WARNING(f"Account '{account_name}' not found, falling back to 'default'", "YELLOW")
            if "default" in self.accounts:
                account_info = self.accounts["default"]
                LOGGER_INFO(f"Using default account: {account_info['email']}", "CYAN")
                return account_info
            else:
                LOGGER_ERROR("No default account configured", "RED")
                return None
    
    def get_email(self, account_name=None):
        """Get email for the specified account"""
        account_info = self.get_account_info(account_name)
        return account_info['email'] if account_info else None
    
    def get_password(self, account_name=None):
        """Get password for the specified account"""
        account_info = self.get_account_info(account_name)
        return account_info['password'] if account_info else None

    def get_phone_username(self, account_name=None):
        """Get phone username for the specified account"""
        account_info = self.get_account_info(account_name)
        return account_info['phone_username'] if account_info else None

    def get_phone_password(self, account_name=None):
        """Get phone password for the specified account"""
        account_info = self.get_account_info(account_name)
        return account_info['phone_password'] if account_info else None

    def list_accounts(self):
        """List all available accounts"""
        return list(self.accounts.keys())


# Global instance
account_config = AccountConfigHandler()
