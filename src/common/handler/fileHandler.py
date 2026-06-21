import os
import platform
from pathlib import Path

def getFilePath(report_file_path):    
    os.makedirs(os.path.dirname(report_file_path), exist_ok=True)
    
    return report_file_path

def is_image_file(file_path):
    """Check if a file is an image based on its extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico'}
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower() in image_extensions
    return False

def is_video_file(file_path):
    """Check if a file is a video based on its extension."""
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp'}
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower() in video_extensions
    return False

def is_audio_file(file_path):
    """Check if a file is an audio based on its extension."""
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower() in audio_extensions
    return False

def is_document_file(file_path):
    """Check if a file is a document based on its extension."""
    document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'}
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower() in document_extensions
    return False

def get_file_type(file_path):
    """Get the file type category (image, video, audio, document, other)."""
    if is_image_file(file_path):
        return 'image'
    elif is_video_file(file_path):
        return 'video'
    elif is_audio_file(file_path):
        return 'audio'
    elif is_document_file(file_path):
        return 'document'
    else:
        return 'other'

def get_file_extension(file_path):
    """Get the file extension."""
    return Path(file_path).suffix.lower()

def extract_json_from_txt(input_file, output_file):
        
    with open(input_file, 'r') as file:
        input_text = file.read()

    cleaned_text = input_text.replace('\\n', '').replace('\\', '')

    start_index = cleaned_text.find('{')
    end_index = cleaned_text.rfind('}')
    json_data = cleaned_text[start_index:end_index+1]
    
    with open(output_file, 'w') as output:
        output.write(json_data)
    
def write_to_file(content, filepath):
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(content + '\n')

def readFile(file_path):    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
 
def readLines(file_path):    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except FileNotFoundError:
        return None
    
def findContentAfterKeyword(file_path, keyword):
    lines = readLines(file_path)
    if lines is None:
        return None
    
    for line in lines:
        if keyword in line:
            keyword_position = line.find(keyword) + len(keyword)
            return line[keyword_position:].strip()

def getSortedFiles(folder_path):
    """Sort files by creation time (oldest first)"""
    files = [
        os.path.relpath(os.path.join(root, f), folder_path)
        for root, _, files in os.walk(folder_path)
        for f in files
    ]
    return sorted(files, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))

def createSymlink(link_path, target_path):
    """Create a symbolic link to the target path."""
    link_path = Path(link_path)
    target_path = Path(target_path)
    try:
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        if platform.system().lower() == "windows":
            os.symlink(str(target_path), str(link_path), target_is_directory=True)
        else:
            link_path.symlink_to(target_path, target_is_directory=True)

    except OSError:
        return None

if __name__ == "__main__":
    extract_json_from_txt('src/document/ChatGPT_Prompt_Response.txt', 'src/document/ChatGPT_Prompt_Response.json')
