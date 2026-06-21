import requests

from config.paths import API_KEY_PATH
from config.config import AI_URL, AGENT_PARAMS
from common.handler.settingsHandler import DynamicConfig


def update_token(agent_type='openai'):
        """
        Update access token for different agent types.
        
        Args:
            url_openAI (str): API endpoint URL
            agent_type (str): Agent type to request token for. Options: 'openai', 'controlhub'
        """
        url = AI_URL
        
        # Get params based on agent_type
        if agent_type in AGENT_PARAMS:
            params = AGENT_PARAMS[agent_type].copy()
        else:
            raise ValueError(f"Unknown agent_type: {agent_type}. Available types: {list(AGENT_PARAMS.keys())}")

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token")

            if access_token:
                api_key = DynamicConfig(API_KEY_PATH)
                
                # Store token with agent_type specific key
                if agent_type == 'controlhub':
                    # Store Control Hub token separately
                    api_key.set('controlhub_access_token', access_token)
                    print(f"✅ Successfully updated Control Hub access token")
                else:
                    # Store OpenAI token (default)
                    api_key.set('access_token', access_token)
                    print(f"✅ Successfully updated OpenAI access token")
            return access_token      
        except requests.RequestException as e:
            print(f"❌ Failed to fetch token for agent_type '{agent_type}': {e}")
        except ValueError as e:
            print(f"❌ Failed to parse JSON: {e}")