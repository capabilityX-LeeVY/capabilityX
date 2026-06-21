import os
import sys


from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
from config.paths import FEATURE_TOGGLE_CONFIG_PATH
from common.utils.featureToggle import FeatureToggle
from common.utils.logger import LOGGER_INFO



def test_feature_toggle():
    FeatureToggle.loadFromFile(FEATURE_TOGGLE_CONFIG_PATH)
    installer = FeatureToggle.isEnabled('installer')
    devMode = FeatureToggle.isEnabled('devMode')
    LOGGER_INFO(f"Feature 'installer' is enabled: {installer}")
    LOGGER_INFO(f"Feature 'devMode' is enabled: {devMode}")

test_feature_toggle()