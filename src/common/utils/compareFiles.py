import difflib
import os
import re
from packaging.version import Version
from tools.MessageBot import BotMessage
from common.utils.markdownToHTML import CConvertMarkdownToHTML
from config.config import *
from config.paths import LOCAL_REPORT_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

def compareFiles():
    file1_path, file2_path = _findCompareVersions(LOCAL_REPORT_PATH)
    compare_results = _compareFiles(file1_path,file2_path)
    if compare_results != None:
        markdown_content = buildMessageToBot(compare_results)
        BotMessage.sendMessageToTeams(markdown_content)

def buildMessageToBot(compare_results):
    markdown_content =f"""
## ACC Comparison Report: {compare_results['largest_version']} VS {compare_results['largest_lower_version']}

### Overall WCAG Complaint Report:
- **Overall WCAG Summary**: [More detail](http://wbxregresssheild.qa.webex.com:8000/acc_report/)

### Version compared:
- **App version**: {compare_results['largest_version']}
- **Baseline**: {compare_results['largest_lower_version']}

### File details:
- **Output file name**: {compare_results['output_file_name']}
- **Total order count in {compare_results['largest_version']}**: {compare_results['file1_lines_count_minus_3']}
- **Total order count in {compare_results['largest_lower_version']}**: {compare_results['file2_lines_count_minus_3']}

### Diff deteals:
- **First diff line**:{compare_results['first_diff_line']}
    """
    return markdown_content

def formatDiffMarkdownLeftRight(diff):
    markdown_output = []
    table_header_added = False
    left_line = None
    right_line = None

    for line in diff:
        line = line.strip()

        if line.startswith('---') or line.startswith('+++'):
            markdown_output.append(f'{line}\n')
            if line.startswith('+++') and not table_header_added:
                markdown_output.append(f'\n')
                header = '| Tab Order | Project ID  | Process ID  | Description  | Control Localized Type | keyboard action | result | Tab Order | Project ID  | Process ID  | Description  | Control Localized Type | keyboard action | result |\n'
                separator = '|--------------|-------------|-------------|--------------|------------------------|-----------------|--------|-----------|-------------|-------------|--------------|------------------------|-----------------|--------|\n'
                markdown_output.append(header)
                markdown_output.append(separator)
                table_header_added = True    
        elif line.startswith('@@'):
            markdown_output.append(f'| <span style="color:#656d76;">{line}</span> |\n')

        elif line.startswith('-'):
            left_line = f'<span style="color:red;">{line}</span>'
            
        elif line.startswith('+'):
            right_line = f'<span style="color:green;">{line}</span>'

            if left_line is not None:
                left_columns = left_line.split('|')
                right_columns = right_line.split('|')

                if len(left_columns) > 3 and len(right_columns) > 3 and left_columns[3] != right_columns[3]:
                    left_columns[3] = f'<span style="background-color: #ffebe9; color: #1f2328">{left_columns[3]}</span>'
                    right_columns[3] = f'<span style="background-color: #e6ffec; color: #1f2328">{right_columns[3]}</span>'
                
                left_line = '| '.join(left_columns)
                right_line = '| '.join(right_columns)
                
                markdown_output.append(f'| {left_line}{right_line} |\n')
                left_line, right_line = None, None
            else:
                markdown_output.append(f'|  | | | | | | | {right_line} |\n')

        else:
            if left_line is not None:
                markdown_output.append(f'| {left_line} | | | | | | |  |\n')
                left_line = None
            # markdown_output.append(f'| {line}{line} |\n')

    if left_line is not None:
        markdown_output.append(f'| {left_line} | | | | | | |  |\n')
    if right_line is not None:
        markdown_output.append(f'|  | | | | | | | {right_line} |\n')

    return ''.join(markdown_output)

def formatDiffMarkdown(diff):
    markdown_output = []
    table_header_added = False
    
    for line in diff:
        line = line.strip()
        if line.startswith('---') or line.startswith('+++'):
            markdown_output.append(f'{line}\n')
            if line.startswith('+++') and not table_header_added:
                markdown_output.append('| Tab Order | Project ID  | Process ID  | Description  | Control Localized Type | IsEnabled | IsKeyboardFocusable | HasKeyboardFocus | default action | keyboard action | result |\n')
                markdown_output.append('|-----------|-------------|-------------|--------------|------------------------|-----------|---------------------|------------------|----------------|-----------------|--------|\n')
                table_header_added = True
        elif line.startswith('@@'):
            markdown_output.append(f'{line}\n')
        elif line.startswith('-') or line.startswith('+'):
            color = 'red' if line.startswith('-') else 'green'
            markdown_output.append(f'<span style="background-color:{color};">{line}</span>\n')
        else:
            markdown_output.append(f'{line}\n')

    return ''.join(markdown_output)

def compareFixedFiles(file1_path, file2_path, output_path):
    file1_name = os.path.basename(file1_path)
    file2_name = os.path.basename(file2_path)

    file1_lines = readFileWithErrorHandling(file1_path)
    file2_lines = readFileWithErrorHandling(file2_path)

    if file1_lines is None or file2_lines is None:
        LOGGER_INFO(f"Failed to process one or both files: {file1_path}, {file2_path}")
        return

    diff = list(difflib.unified_diff(
        file1_lines,
        file2_lines,
        fromfile=file1_name,
        tofile=file2_name,
        lineterm=''
    ))
    markdown_diff = formatDiffMarkdown(diff)
    try:
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(f'# Diff Report\n\n{markdown_diff}')
    except Exception as e:
        LOGGER_ERROR(f"Error reading files: {e}")

def _findCompareVersions(directory_path):
    version_file_map = {}
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            base_name, ext = os.path.splitext(file)
            if base_name.startswith('acc-navigation-report-'):
                try:
                    version_str = base_name.split('-')[-1]
                    file_version = Version(version_str)

                    file_path = os.path.join(root, file)
                    version_file_map[file_version] = file_path
                except Exception as e:
                    continue

    if version_file_map:
        largest_version = max(version_file_map.keys())
        largest_file_path = version_file_map[largest_version]

        lower_major_minor_versions = [
            version for version in version_file_map.keys() 
            if version.major == largest_version.major and version.minor == largest_version.minor - 1
        ]

        if lower_major_minor_versions:
            largest_lower_version = max(lower_major_minor_versions)
            largest_lower_file_path = version_file_map[largest_lower_version]
            return largest_lower_file_path, largest_file_path
        else:
            return None, largest_file_path
    else:
        return None, None
    
def readFileWithErrorHandling(file_path):
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                try:
                    lines.append(line)
                except UnicodeDecodeError as e:
                    LOGGER_ERROR(f"Error decoding line in file {file_path}: {e}")
                    continue
    except Exception as e:
        LOGGER_ERROR(f"Error opening or reading file {file_path}: {e}")
        return None
    return lines[1:]

def preprocess_lines(lines):
    processed_lines = []
    for line in lines:
        parts = line.split('|')
        new_parts = [part for idx, part in enumerate(parts) if idx not in (5, 6, 7, 8)]
        processed_lines.append('|'.join(new_parts).strip())
    return processed_lines

def _compareFiles(file1_path, file2_path):
    if not file1_path or not file2_path:
        LOGGER_ERROR("Error: One or both file paths are missing.")
        return None

    if not os.path.exists(file1_path):
        LOGGER_ERROR(f"Error: File not found: {file1_path}")
        return None

    if not os.path.exists(file2_path):
        LOGGER_ERROR(f"Error: File not found: {file2_path}")
        return None
    
    file1_name = os.path.basename(file1_path)
    file2_name = os.path.basename(file2_path)

    file1_base, ext = os.path.splitext(file1_path)
    file2_base, ext = os.path.splitext(file2_path)

    largest_lower_version= file1_base.split('-')[-1]
    largest_version= file2_base.split('-')[-1]
    
    qt_version1 = re.search(r'QT\d+\.\d+\.\d+', file1_base).group() if re.search(r'QT\d+\.\d+\.\d+', file1_base) else None
    qt_version2 = re.search(r'QT\d+\.\d+\.\d+', file2_base).group() if re.search(r'QT\d+\.\d+\.\d+', file2_base) else None

    file1_lines = readFileWithErrorHandling(file1_path)
    file2_lines = readFileWithErrorHandling(file2_path)

    processed_file1_lines = preprocess_lines(file1_lines)
    processed_file2_lines = preprocess_lines(file2_lines)

    if file1_lines is None or file2_lines is None:
        LOGGER_ERROR(f"Failed to process one or both files: {file1_path}, {file2_path}")
        return

    diff = list(difflib.unified_diff(
        processed_file1_lines,
        processed_file2_lines,
        fromfile=file1_name,
        tofile=file2_name,
        lineterm=''
    ))

    first_diff_line = None
    for line in diff:
        if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
            continue
        if line.startswith('+') or line.startswith('-'):
            first_diff_line = line
            break
    
    markdown_diff = formatDiffMarkdownLeftRight(diff)
    
    diff_directory = os.path.join(os.path.dirname(file1_path), 'diff')
    os.makedirs(diff_directory, exist_ok=True)

    output_file_name = f"{largest_lower_version}[{qt_version1}]VS{largest_version}[{qt_version2}].md"
    output_file_path = os.path.join(diff_directory, output_file_name)
    html_file_name = f"{largest_lower_version}[{qt_version1}]VS{largest_version}[{qt_version2}].html"
    html_file_path = os.path.join(diff_directory,html_file_name)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(f'# Diff Report: {largest_lower_version}[{qt_version1}] VS {largest_version}[{qt_version2}]\n')
            output_file.write(f'Total navigate controls in {largest_lower_version}: {len(file1_lines)-3}\n')
            output_file.write(f'Total navigate controls in {largest_version}: {len(file2_lines)-3}\n\n')
            output_file.write(markdown_diff)
    except Exception as e:
        LOGGER_ERROR(f"Error reading files: {e}")

    LOGGER_INFO(f"\nDiff file saved at: {output_file_path}")
    
    CConvertMarkdownToHTML.MarkdownToHTML(output_file_path, html_file_path)
    return {
        'output_file_name': output_file_name,
        'output_file_path': output_file_path,
        'largest_version': f'{largest_version}[{qt_version2}]',
        'largest_lower_version': f'{largest_lower_version}[{qt_version1}]',
        'file1_lines_count_minus_3': len(file1_lines) - 3,
        'file2_lines_count_minus_3': len(file2_lines) - 3,
        'first_diff_line': first_diff_line
    }
