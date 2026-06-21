import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.benchmark import model_gpt4, model_gpt4_o, model_gpt4_o1, model_gpt4_o3, model_gpt5
from tests.models.ai_token_loader import get_openai_api_key
from rs_sdk.utils.image_handler import image_base64_encode
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

access_token = get_openai_api_key()
image_url = image_base64_encode(rf"src/tests/models/sample/focus_ring_01.png")
# image_url = 'https://i.imgur.com/CzXTtJV.jpeg'
# image_url ='https://cisco-api.ingeniuxondemand.com/DITA/content/en/us/td/i/400001-500000/450001-460000/450001-451000/450705.jpg'

model_name = "gpt-5"

def test_models_benchmark(access_token, image_url_base64):
    LOGGER_INFO(f"Testing model {model_name}", "GREEN")
    if model_name == "gpt-4":
        model_gpt4.run_model_gpt4(access_token, image_url_base64)
    elif model_name == "gpt-4o":
        model_gpt4_o.run_model_gpt4_o(access_token, image_url_base64)
    elif model_name == "gpt-4o1":
        model_gpt4_o1.run_model_gpt4_o1(access_token, image_url_base64)
    elif model_name == "gpt-4o3":
        model_gpt4_o3.run_model_gpt4_o3(access_token, image_url_base64)
    elif model_name == "gpt-5":
        model_gpt5.run_model_gpt5(access_token, image_url_base64)
    else:
        model_gpt4.run_model_gpt4(access_token, image_url_base64)
        LOGGER_INFO(f"===========================================================================================================", "GREEN")
        model_gpt4_o.run_model_gpt4_o(access_token, image_url_base64)
        LOGGER_INFO(f"===========================================================================================================", "GREEN")
        model_gpt4_o1.run_model_gpt4_o1(access_token, image_url_base64)
        LOGGER_INFO(f"===========================================================================================================", "GREEN")
        model_gpt4_o3.run_model_gpt4_o3(access_token, image_url_base64)
        LOGGER_INFO(f"===========================================================================================================", "GREEN")
        model_gpt5.run_model_gpt5(access_token, image_url_base64)
        LOGGER_INFO(f"===========================================================================================================", "GREEN")

test_models_benchmark(access_token, image_url)