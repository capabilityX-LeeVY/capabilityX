import os
import json

def get_openai_api_key():
        try:
            openai_aip_key_json = os.environ.get('openai_aip_key_json', os.path.join('src', 'config', 'api_key.json'))
            # logging.info(f"loading openai_aip_key_json file: {openai_aip_key_json}")

            with open(openai_aip_key_json, 'r') as f:
                openai_aip_key = json.load(f)
        except FileNotFoundError:
            # logging.error(f"{openai_aip_key_json} is not found. Please check the file path.")
            print(f"{openai_aip_key_json} is not found. Please check the file path.")
        except Exception as e:
            # logging.error(f"Failed to load openai_aip_key_json file: {e}")
            print(f"Failed to load openai_aip_key_json file: {e}")
        return openai_aip_key['access_token']