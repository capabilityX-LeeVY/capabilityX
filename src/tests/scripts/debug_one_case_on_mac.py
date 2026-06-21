import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent  # Go up to src/
sys.path.insert(0, str(src_path))

from core.mac.GTManager import GTManager

def DebugOneCase():
    language = "en_US"
    file = "/Users/faye/workspace/webex-regress-shield/src/test_space/test_suites/web/web_video_vbg.yaml"
    GTManager.run_by_file(file, language)

def Test():
    from core.mac.GTFunction import GTFunction
    f = GTFunction()
    correlation_id = f.call_by_name("get_correlation_id_from_log")
    print(f"Correlation ID: {correlation_id}")  

if __name__ == "__main__":  
    DebugOneCase()
    #Test()