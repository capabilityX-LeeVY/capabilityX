import psutil
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

def get_webex_main_pid():
    all_processes = psutil.process_iter()
    process_name = "CiscoCollabHost.exe"
    hosted_processes = []
    for process in all_processes:
        try:
            process_info = process.as_dict(attrs=['name', 'cmdline'])
            if process_info['name'] == process_name and any('Hosted=true' in cmd for cmd in process_info['cmdline']):
                hosted_processes.append(process)
        except psutil.NoSuchProcess:
            pass

    if hosted_processes:
        desired_process = hosted_processes[0]
        LOGGER_INFO(f"webex main process found: {desired_process.name()} (PID: {desired_process.pid})")
    else:
        LOGGER_ERROR("webex main process not found")
        return None

    return desired_process.pid

def get_webex_media_pid():
    all_processes = psutil.process_iter()
    process_name = "CiscoCollabHost.exe"
    hosted_processes = []
    for process in all_processes:
        try:
            process_info = process.as_dict(attrs=['name', 'cmdline'])
            if process_info['name'] == process_name and any('media' in cmd for cmd in process_info['cmdline']):
                hosted_processes.append(process)
        except psutil.NoSuchProcess:
            pass

    if hosted_processes:
        desired_process = hosted_processes[0]
        LOGGER_INFO(f"webex media process found: {desired_process.name()} (PID: {desired_process.pid})")
    else:
        LOGGER_ERROR("webex media process not found")
        return None

    return desired_process.pid

if __name__ == "__main__":
    get_webex_main_pid()
    get_webex_media_pid()