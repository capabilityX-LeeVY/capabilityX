from config.paths import SETTINGS_PATH, APP_VERSION_PATH, NAVIGATION_REPORT_PATH, PERFORMANCE_REPORT_PATH, STRESS_REPORT_PATH, SCREEN_READER_REPORT_PATH
import os
from common.handler.settingsHandler import DynamicConfig
from common.utils import deviceInfo
from common.utils.logger import LOGGER_ERROR, LOGGER_INFO, LOGGER_WARNING
from common.handler import fileHandler
from common.utils import generatelogs


def write_navigate_report_header(settings, test_suite, language):
    appVersion = settings.get('appVersion')
    
    safe_test_suite = test_suite.replace('/', '').replace('\\', '')
    report_file_path = os.path.expandvars(
    os.path.join(NAVIGATION_REPORT_PATH, f'navigation-report-{safe_test_suite}-{language}.md')
    )
    navigation_report_file_path = fileHandler.getFilePath(report_file_path)

    with open(navigation_report_file_path, 'w') as file:
        file.write(f"# Webex Meetings - GT Test Report: [{appVersion}]\n\n")

    return navigation_report_file_path

def write_navigate_report_title(report_file_path, test_case):

    with open(report_file_path, 'a') as file:
        file.write(f"## Test Case: [{test_case}]\n\n")
        file.write("| Test Case  | Step Num | Step Name | Current Control Name | Reference   | Window Image   | Control Image | KB Navigate | Focus Ring | Screen Reader | AI Check | Value Verify | Response Time | Main CPU | Main Memory | Main GPU |\n")
        file.write("|-----------------|-------|---------------------|----------------------|-------------|----------------|---------------|-------------|------------|---------------|----------|--------------|---------------|----------|-------------|----------|\n")

    return report_file_path

def write_navigate_report_body(report_path, test_case, ui_path_order, locate_control_name, current_control_name="", reference="", image="", control_image="", kb_navigate="", focus_ring="", screen_reader="", ai_check="", value_verify="N/A", response_time="N/A", main_cpu="N/A", main_mem="N/A", main_gpu="N/A"):
    """
    Appends a row to the navigation report.
    
    Args:
        locate_control_name: Target control name to locate (from test case YAML)
        current_control_name: Actual focused control name (from ControlName)
        response_time: UI response time - time from control action to next focusable state becoming available
    """
    # Apply default values if empty
    if not response_time or response_time.strip() == "":
        response_time = "N/A"
    
    if not ai_check or ai_check.strip() == "":
        ai_check = "N/A"
    
    if not value_verify or value_verify.strip() == "":
        value_verify = "N/A"
    
    if not current_control_name or current_control_name.strip() == "":
        current_control_name = "N/A"
    
    # Clean control names: replace newlines and tabs with spaces for markdown table compatibility
    def clean_text_for_markdown(text):
        if isinstance(text, str):
            # Replace newlines, carriage returns, and tabs with single space
            text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            # Replace multiple spaces with single space
            text = ' '.join(text.split())
        return text
    
    locate_control_name = clean_text_for_markdown(locate_control_name)
    current_control_name = clean_text_for_markdown(current_control_name)
    ai_check = clean_text_for_markdown(ai_check)
    value_verify = clean_text_for_markdown(value_verify)
    screen_reader = clean_text_for_markdown(screen_reader)
    
    with open(report_path, 'a', encoding='utf-8') as file:
        file.write(
            f"| {test_case} | {ui_path_order} | {locate_control_name} | {current_control_name} | {reference} | {image} | {control_image} | {kb_navigate} | {focus_ring} | {screen_reader} | {ai_check} | {value_verify} | {response_time} | {main_cpu} | {main_mem} | {main_gpu} |\n"
        )

def write_performance_report_header(settings, test_suite):
    osInfo = settings.get('osInfo')
    appVersion = settings.get('appVersion')
    qtVersion = settings.get('installOptions', 'qtversion')
    
    report_file_path = os.path.expandvars(
        # os.path.join('%LOCALAPPDATA%', 'WebexRegressSheild', 'report', 'navigation', f'acc-navigation-report-QT{qtVersion}-{appVersion}.md')
        os.path.join(PERFORMANCE_REPORT_PATH, f'performance-report-{test_suite}.md')
    )
    performance_report_file_path = fileHandler.getFilePath(report_file_path)

    with open(performance_report_file_path, 'w') as file:
        file.write(f"# WebEx APP Meetings Performance Testing Report [{appVersion}] [High Device]\n\n")
        file.write("| Test Case | Control Description | main cpu | main mem | media cpu | media mem |\n")
        file.write("|-----------|---------------------|----------|----------|-----------|-----------|\n")    

    return performance_report_file_path

def write_performance_report_body(report_path, test_case, ctrl_desc, main_cpu='N/A', main_mem='N/A', media_cpu='N/A', media_mem='N/A'):
    """
    Appends a row to the navigation report.
    """
    with open(report_path, 'a', encoding='utf-8') as file:
        file.write(
            f"| {test_case} | {ctrl_desc} | {main_cpu if main_cpu is not None else 'N/A'} | {main_mem if main_mem is not None else 'N/A'} | {media_cpu if media_cpu is not None else 'N/A'} | {media_mem if media_mem is not None else 'N/A'} |\n"
        )

def setBasicInfo():
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

def initialize_navigate_report(test_suite, language):
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

    report_file_path = write_navigate_report_header(settings, test_suite, language)
    generatelogs.setup_logging(report_file_path)
    return report_file_path

def initialize_performance_report(test_suite):
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

    report_file_path = write_performance_report_header(settings, test_suite)
    generatelogs.setup_logging(report_file_path)
    return report_file_path

def write_stress_report_header(settings, test_suite):
    osInfo = settings.get('osInfo')
    appVersion = settings.get('appVersion')
    qtVersion = settings.get('installOptions', 'qtversion')
    
    report_file_path = os.path.expandvars(
        os.path.join(STRESS_REPORT_PATH, f'stress-report-{test_suite}.md')
    )
    stress_report_file_path = fileHandler.getFilePath(report_file_path)

    with open(stress_report_file_path, 'w') as file:
        file.write(f"# WebEx APP Meetings Stress Testing Report [{appVersion}] [High Device]\n\n")
        file.write("**Stress Thresholds:** CPU <= 40.0%, Memory <= 3000.0MB\n\n")
        file.write("| Test Case | Control Description | Image | Main CPU (%) | Main Memory (MB) | Media CPU (%) | Media Memory (MB) | CPU Check | Memory Check | Process Count | Process Types | Window Response | Process Status | AI Check | Participants Number | Issues | Log Archive |\n")
        file.write("|-----------|---------------------|-------|--------------|------------------|---------------|-------------------|-----------|--------------|---------------|---------------|-----------------|----------------|----------|---------------------|--------|-------------|\n")    

    return stress_report_file_path

def write_stress_report_body(report_path, test_case, ctrl_desc, image='', main_cpu='N/A', main_mem='N/A', media_cpu='N/A', media_mem='N/A', cpu_check='N/A', memory_check='N/A', process_count='N/A', process_types='N/A', window_response='N/A', process_status='N/A', ai_check='', participants_number='', issues='', log_archive=''):
    """
    Appends a row to the stress report with enhanced format matching single-case-features-backup branch.
    """
    # Format the image column if provided
    image_col = ''
    if image:
        image_col = f'<img src="{image}" alt="{ctrl_desc}" style="max-width: 200px; height: auto;">'
    
    # Format CPU and Memory checks with emoji instead of HTML colors
    cpu_check_formatted = cpu_check
    if cpu_check == 'PASS':
        cpu_check_formatted = '✅ PASS'
    elif cpu_check == 'FAIL':
        cpu_check_formatted = '❌ FAIL'
    elif cpu_check == 'WARNING':
        cpu_check_formatted = '⚠️ WARNING'
    
    memory_check_formatted = memory_check
    if memory_check == 'PASS':
        memory_check_formatted = '✅ PASS'
    elif memory_check == 'FAIL':
        memory_check_formatted = '❌ FAIL'
    elif memory_check == 'WARNING':
        memory_check_formatted = '⚠️ WARNING'
    
    # Format process status with emoji instead of HTML colors  
    process_status_formatted = process_status
    if process_status == 'HEALTHY':
        process_status_formatted = '✅ HEALTHY'
    elif process_status == 'CRITICAL':
        process_status_formatted = '🚨 CRITICAL'
    elif process_status == 'UNHEALTHY':
        process_status_formatted = '⚠️ UNHEALTHY'
    elif process_status == 'DEGRADED':
        process_status_formatted = '⚠️ DEGRADED'
    elif process_status == 'WARNING':
        process_status_formatted = '⚠️ WARNING'
    elif process_status == 'SLUGGISH':
        process_status_formatted = '🐌 SLUGGISH'
    elif process_status == 'UNKNOWN':
        process_status_formatted = '❓ UNKNOWN'
    
    # Format window response with checkmark if good
    window_response_formatted = window_response
    if window_response.endswith('ms') and window_response != 'N/A':
        try:
            response_time = float(window_response.replace('ms', ''))
            if response_time < 100:  # Good response time
                window_response_formatted = f'✅ {window_response}'
        except:
            pass
    
    # Format AI check with emoji instead of HTML colors
    ai_check_formatted = ai_check
    if ai_check == 'PASS':
        ai_check_formatted = '✅ PASS'
    elif ai_check == 'FAIL':
        ai_check_formatted = '❌ FAIL'
    
    # Format participants number with icon if provided
    participants_formatted = participants_number
    if participants_number and participants_number != '':
        participants_formatted = f'👥 {participants_number}'
    
    # Format log archive as simple text link instead of HTML if provided
    log_archive_formatted = log_archive
    if log_archive and log_archive != '':
        if log_archive.startswith('http') or log_archive.endswith('.zip'):
            log_archive_name = log_archive.split('/')[-1] if '/' in log_archive else log_archive
            # Use markdown link format instead of HTML
            log_archive_formatted = f'📦 [{log_archive_name}]({log_archive})'
    
    with open(report_path, 'a', encoding='utf-8') as file:
        file.write(
            f"| {test_case} | {ctrl_desc} | {image_col} | {main_cpu} | {main_mem} | {media_cpu} | {media_mem} | {cpu_check_formatted} | {memory_check_formatted} | {process_count} | {process_types} | {window_response_formatted} | {process_status_formatted} | {ai_check_formatted} | {participants_formatted} | {issues} | {log_archive_formatted} |\n"
        )

def initialize_stress_report(test_suite):
    settings = DynamicConfig(SETTINGS_PATH)
    report_topic = reportTopicManager(settings)
    report_topic.setInfo()

    report_file_path = write_stress_report_header(settings, test_suite)
    generatelogs.setup_logging(report_file_path)
    return report_file_path


def _sort_sr_report_table(markdown_content: str) -> str:
    """Sort SR report markdown table rows by the No. (step_order) column ascending."""
    import re
    lines = markdown_content.split('\n')
    header_lines = []
    data_rows = []
    other_lines = []
    in_table = False

    for line in lines:
        if line.startswith('|'):
            if not in_table:
                # First table line — header
                header_lines.append(line)
                in_table = True
            elif line.startswith('|---') or line.startswith('| ---'):
                header_lines.append(line)
            else:
                data_rows.append(line)
        else:
            if in_table and data_rows:
                # Table ended — sort and flush
                def sort_key(row):
                    cols = row.split('|')
                    if len(cols) >= 2:
                        try:
                            return int(cols[1].strip())
                        except ValueError:
                            return 999999
                    return 999999
                data_rows.sort(key=sort_key)
                other_lines.extend(header_lines)
                other_lines.extend(data_rows)
                header_lines = []
                data_rows = []
                in_table = False
            other_lines.append(line)

    # Flush remaining table rows
    if data_rows:
        def sort_key(row):
            cols = row.split('|')
            if len(cols) >= 2:
                try:
                    return int(cols[1].strip())
                except ValueError:
                    return 999999
            return 999999
        data_rows.sort(key=sort_key)
        other_lines.extend(header_lines)
        other_lines.extend(data_rows)

    return '\n'.join(other_lines)


def write_screen_reader_report(markdown_content, test_suite=None, report_id=None):
    """
    Write screen reader report markdown content to file.
    
    Args:
        markdown_content (str): The markdown content to write
        test_suite (str, optional): Test suite name for file naming
        report_id (str, optional): Report ID for file naming
    
    Returns:
        str: The file path where the report was saved
    """
    try:
        # Generate filename based on available parameters
        if test_suite and report_id:
            filename = f'sr-report-{test_suite}-{report_id}.md'
        elif test_suite:
            filename = f'sr-report-{test_suite}.md'
        elif report_id:
            filename = f'sr-report-{report_id}.md'
        else:
            filename = 'sr-report.md'
        
        # Create full file path
        report_file_path = os.path.join(SCREEN_READER_REPORT_PATH, filename)
        screen_reader_report_file_path = fileHandler.getFilePath(report_file_path)
        
        # Sort markdown table rows by step_order (No. column) before writing
        markdown_content = _sort_sr_report_table(markdown_content)
        
        # Write markdown content to file
        with open(screen_reader_report_file_path, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
        
        return screen_reader_report_file_path
        
    except Exception as e:
        LOGGER_ERROR(f"Failed to write screen reader report: {str(e)}")
        return None


def append_analysis_to_report(report_path, analysis_result):
    """
    Append AI analysis result to the performance report file
    
    Args:
        report_path (str): Path to the report file
        analysis_result (str): The analysis result to append
    
    Returns:
        dict: Result containing success status and file paths
    """
    try:
        LOGGER_INFO(f"Appending AI analysis to report: {report_path}", "CYAN")
        
        with open(report_path, 'a', encoding='utf-8') as f:
            f.write("\n\n---\n\n")
            f.write("# AI Performance Analysis\n\n")
            f.write(analysis_result)
        
        LOGGER_INFO(f"Performance analysis appended to: {report_path}", "GREEN")
        
        return {
            'success': True,
            'original_path': report_path,
            'updated_path': report_path,
            'analysis_result': analysis_result
        }
        
    except Exception as e:
        LOGGER_ERROR(f"Failed to append analysis to file: {str(e)}", "RED")
        return {
            'success': False,
            'error': str(e),
            'original_path': report_path
        }

class reportTopicManager:
    def __init__(self, settings):
        self.settings = settings

    def setInfo(self):
        os_info = deviceInfo.getOSInfo()
        app_version = self.getAppInfo()
        self.saveInfo(os_info, app_version)

    def getAppInfo(self):
        app_version = fileHandler.readFile(APP_VERSION_PATH)
        return app_version

    def saveInfo(self, os_info, app_version):
        self.settings.set('appVersion', app_version)
        self.settings.set('osInfo', os_info)