import platform

# from common.startup import token_initializer
from config.paths import SETTINGS_PATH
from common.utils.featureToggle import FeatureToggle
from tools.analysis_runner import FocusRingAnalysisRunner, ScreenReaderAnalysisRunner, i18nAnalysisRunner
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_ERROR, LOGGER_INFO
from tools.summary_runner import ControlTypeExporter
from common.finalizer import archive_processor, notifier

def build_output():
        settings = DynamicConfig(SETTINGS_PATH)
        AI_analysis_enabled = settings.get("openai")

        if FeatureToggle.isEnabled('croppedImage'):
            FocusRingAnalysisRunner().run_analysis() 
        
        if AI_analysis_enabled:
            # token_initializer.update_token()
            ScreenReaderAnalysisRunner().run_analysis()
            i18nAnalysisRunner().run_analysis()

        current_os = platform.system().lower()
        roomID = "c0af0ac0-772f-11ef-9431-6382b932281b"
        if current_os == 'windows':
            roomID = "c0af0ac0-772f-11ef-9431-6382b932281b"
            ControlTypeExporter().export_win_controltype_summary()
        elif current_os == 'darwin':
            roomID = "a83fa300-818d-11f0-9d5c-fb6fa60d4c49"
            ControlTypeExporter().export_mac_controltype_summary()
        roomID = settings.botRoomId or roomID
        output_url = archive_processor.RemoteArchiveProcessor().upload_archive()
        if output_url is None:
            LOGGER_ERROR("Failed to upload archive, skipping notification.")
            return
        LOGGER_INFO(f"Result upload completed!")
        # notifier.notify_messageBot(str(output_url))
        notifier.notify_messageBot_card(str(output_url), roomId=roomID)
        LOGGER_INFO(f"Report URL: {output_url}")
        return output_url
    